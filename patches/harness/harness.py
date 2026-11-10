#!/usr/bin/env python3
"""Core-1 emulation harness for DAP Neo decoder modules (Phase D, milestone 1).

Boots a stock decoder program (default: module 76, FLAC) from its reset
vector under Unicorn, plays the system core's part of the boot handshake,
and serves the decoder's HifiFile RPC (MU channel 2) from a host file.

Design (all addresses FLAC-derived; see command_semantics.md):
- MU at 0x40110000 is plain RAM. The decoder's MU sends are intercepted
  with block hooks on its send functions (0x01004fb0 cmd / 0x01004fdc
  param) -- block hooks only, because code/mem hooks mis-execute Thumb
  IT blocks on Unicorn 2.1 (lesson from refs/echo-mini-opus emu74.py).
- HifiFile requests are served synchronously inside the param-send hook:
  the operation is performed and the reply's *effects* (normally applied
  by the decoder's channel-2 receive ISR, fn 0x01001390) are written
  directly -- completion flag [0x0102222c]=1, reply cmd/param recorded
  at ctrl+4/+8, ctrl[0] state per the receiver's table. The stub polling
  the flag then completes on its first iteration. The receiver functions
  are interrupt handlers (vector slots 0x1a/0x1b in the RAM vector table
  at 0x01022000); they are replicated, not executed -- see
  command_semantics.md for the instruction-level derivation of every
  replicated write.
- System->decoder messages (ch1 command table, ch2 0x65 info push) are
  delivered the same way: the receive fns' shared-memory effects are
  applied by the driver between emu_start slices.
"""
import os
import struct
import sys
from pathlib import Path

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS,
                     UC_HOOK_BLOCK, UC_HOOK_MEM_INVALID, UC_MEM_WRITE,
                     UC_MEM_READ)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_PC, UC_ARM_REG_SP)

def _workspace():
    """Extraction workspace (the extracted/ tree): FOSI_WORKSPACE >
    walk up from this script for extracted/manifest.json > cwd.
    Portable per tools/fosi_paths.py — no hard-coded dev path."""
    env = os.environ.get('FOSI_WORKSPACE')
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for anc in (here.parent, *here.parents):
        if (anc / 'extracted' / 'manifest.json').exists():
            return anc
    return Path.cwd()


WS = _workspace()
CODE_VA, DATA_VA = 0x01000000, 0x01020000

# ---- decoder-side addresses (module 76 FLAC; re-derive per module) ----
SEND_CMD, SEND_PARAM, PRINTF = 0x00004FB0, 0x00004FDC, 0x0000095E  # core-1 local (0-based) code view
CMDWORD, ARGWORD, FMTWORD = 0x0102221C, 0x01022220, 0x01022224
CTRL = 0x01022290                # +0 state byte, +4 last rx cmd, +8 last rx param
FLAG, INITFLAG = 0x0102222C, 0x0102222D
HANDLE_TABLE = 0x01022234
INFO_STRUCT = 0x010227F4         # decoder stream-info struct (ch1 cmd 3 param)
SCRATCH = 0x0103F000             # harness-owned: the 0x65 info struct lives here

CH1_TRANSLATE = {1: (1, False), 4: (2, False), 7: (4, False), 9: (5, False),
                 0x0B: (3, True), 0x0D: (6, True),
                 0xCB: (14, True), 0xCD: (13, True)}
# ch2 reply cmd -> ctrl[0] state written by the receiver (fn 0x01001390)
CH2_REPLY_STATE = {0x6A: 2, 0x6C: 3, 0x6E: 4, 0x70: 5, 0x72: 6}


class Trace:
    def __init__(self, path):
        self.f = open(path, 'w')
        self.slice_no = 0

    def log(self, tag, msg=''):
        line = f'[s{self.slice_no:05d}] {tag} {msg}'
        print(line, flush=True)
        self.f.write(line + '\n')
        self.f.flush()


class Harness:
    def __init__(self, module_idx=76, media=None, fmt_word=6, handle=3,
                 trace_path='run_log.txt'):
        man = __import__('json').load(open(WS / 'extracted/manifest.json'))
        mods = {m['index']: m for m in man['modules']}
        m = mods[module_idx]
        self.code = open(WS / f"extracted/module_{module_idx:02d}_code_01000000.bin", 'rb').read()
        self.data = open(WS / f"extracted/module_{module_idx:02d}_data_01020000.bin", 'rb').read()
        assert len(self.code) == m['code_len'] and len(self.data) == m['data_len']
        self.media = Path(media).read_bytes() if media else b''
        self.media_name = str(media)
        self.fmt_word, self.handle = fmt_word, handle
        self.pos = {}                      # handle -> host file position
        self.tr = Trace(trace_path)
        self.ready = False                 # ch0 cmd 1 seen
        self.open_notified = False         # ch2 0x66 seen
        self.info_reported = None          # ch1 cmd 3 param
        self.pending_rpc = None            # ch2 cmd awaiting its param send
        self.reads_served = 0
        self.bytes_served = 0
        self.stop = False

        u = self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        u.mem_map(0x00000000, 0x20000)                 # code in core-1's local 0-based view
        u.mem_map(CODE_VA, 0x20000)                    # shadow in the shared/system view
        u.mem_map(DATA_VA, 0x40000)                    # window to 0x01060000
        u.mem_map(0x01060000, 0xA0000)                 # decoder-local MMIO: DMAC/audio
        # blocks at 0x0106xxxx-0x0108xxxx (writes seen at 0x0106000c, literal
        # 0x01080108) -- pre-mapped because UC_HOOK_MEM_INVALID does not fire
        # reliably on this Unicorn build (faults surface as emu_start errors)
        u.mem_map(0x40000000, 0x200000)                # MU 0x40110000, CRU, misc SoC
        u.mem_map(0x60080000, 0x10000)                 # audio MMIO view 0x60082xxx
        u.mem_map(0xE0000000, 0x100000)                # PPB: VTOR/NVIC/SCB as RAM
        u.mem_write(0x00000000, self.code)
        u.mem_write(CODE_VA, self.code)
        # 144-byte parameter page overwrites the data image head on hardware
        # (reset-and-start 0x0306cb2c). The image's first 0x90 bytes are zero
        # and the page contents are runtime-built/undecoded: start from zeros.
        u.mem_write(DATA_VA, bytes(0x90))
        u.mem_write(DATA_VA + 0x90, self.data[0x90:])
        # Two page fields are dividers in the decoder's delay loops and must
        # be nonzero: [page+0x20] is read as Hz by delay fn 0xb54 (count =
        # arg * (Hz/1e6) / 10) and [page+0x24] as Hz by delay fn 0xb78
        # (count = arg * (Hz/3000)); with zeros the latter underflows into a
        # ~4e9-iteration spin. Values are plausible clock rates, not measured
        # page contents (the real page is runtime-built; contents undecoded).
        for off, hz in ((0x20, 96_000_000), (0x24, 24_000_000)):
            u.mem_write(DATA_VA + off, struct.pack('<I', hz))

        u.hook_add(UC_HOOK_BLOCK, self._on_send_cmd, begin=SEND_CMD, end=SEND_CMD)
        u.hook_add(UC_HOOK_BLOCK, self._on_send_param, begin=SEND_PARAM, end=SEND_PARAM)
        u.hook_add(UC_HOOK_BLOCK, self._on_printf, begin=PRINTF, end=PRINTF)
        u.hook_add(UC_HOOK_MEM_INVALID, self._on_invalid)

    # ---------- memory helpers ----------
    def rd(self, addr, size):
        return bytes(self.u.mem_read(addr, size))

    def rd32(self, addr):
        return struct.unpack('<I', self.rd(addr, 4))[0]

    def wr32(self, addr, val):
        self.u.mem_write(addr, struct.pack('<I', val & 0xFFFFFFFF))

    def wr8(self, addr, val):
        self.u.mem_write(addr, bytes([val & 0xFF]))

    # ---------- hooks ----------
    def _regs(self):
        return (self.u.reg_read(UC_ARM_REG_R0), self.u.reg_read(UC_ARM_REG_R1),
                self.u.reg_read(UC_ARM_REG_R2))

    def _on_printf(self, u, addr, size, data):
        r0 = u.reg_read(UC_ARM_REG_R0)
        try:
            s = bytes(u.mem_read(r0, 120)).split(b'\0')[0].decode('latin1')
        except Exception:
            s = f'<unreadable fmt @{r0:#x}>'
        self.tr.log('PRINTF', repr(s))

    def _on_send_cmd(self, u, addr, size, data):
        val, unit, ch = self._regs()
        self.tr.log('MU-SEND', f'cmd unit={unit} ch={ch} cmd={val:#06x}')
        if ch == 0 and val == 1:
            self.ready = True
            self.tr.log('MILESTONE', 'decoder READY (ch0 cmd 1)')
        if ch == 2:
            if val in (0x69, 0x6B, 0x6D, 0x73, 0x6F, 0x71):
                self.pending_rpc = val
            elif val == 0x66:
                self.open_notified = True
                self.tr.log('MILESTONE', 'open accepted by decoder (ch2 0x66 notify)')
            else:
                self.tr.log('MU-NOTIFY', f'ch2 notification {val:#06x} (no reply)')
        if ch == 1 and val == 3:
            self.info_reported = 'pending-param'

    def _on_send_param(self, u, addr, size, data):
        val, unit, ch = self._regs()
        self.tr.log('MU-SEND', f'param unit={unit} ch={ch} param={val:#010x}')
        if ch == 1 and self.info_reported == 'pending-param':
            self.info_reported = val
            self.tr.log('MILESTONE', f'stream info reported (ch1 cmd 3, param={val:#010x})')
        if ch == 2 and self.pending_rpc is not None:
            cmd, self.pending_rpc = self.pending_rpc, None
            self._serve_rpc(cmd, val)

    def _on_invalid(self, u, access, addr, size, value):
        pc = u.reg_read(UC_ARM_REG_PC)
        kind = 'write' if access == UC_MEM_WRITE else 'read'
        self.tr.log('FAULT', f'unmapped {kind} @{addr:#010x} size={size} pc={pc:#010x} -- mapping zero page')
        base = addr & ~0xFFF
        try:
            u.mem_map(base, 0x1000)
        except Exception:
            pass
        return True

    # ---------- HifiFile server (system side, per module 33 fn 0x030895da) ----------
    def _deliver_ch2_reply(self, cmd, param):
        """Replicates fn 0x01001390's effects for an RPC reply."""
        self.wr32(CTRL + 4, cmd)
        self.wr32(CTRL + 8, param)
        if cmd in CH2_REPLY_STATE:
            self.wr8(CTRL, CH2_REPLY_STATE[cmd])
        elif cmd == 0x74 and param != 0:
            self.wr8(CTRL, 7)
        self.wr8(FLAG, 1)
        self.tr.log('MU-RECV', f'ch2 reply cmd={cmd:#06x} param={param:#010x} delivered (flag set)')

    def _serve_rpc(self, cmd, param):
        size = len(self.media)
        if cmd == 0x69:                                    # Seek
            blk = param
            off, whence = self.rd32(blk), self.rd32(blk + 4)
            h = self.rd(blk + 8, 1)[0]
            cur = self.pos.get(h, 0)
            off_s = off - 0x100000000 if off & 0x80000000 else off
            new = {0: off_s, 1: cur + off_s, 2: size + off_s}.get(whence & 0xFF, off_s)
            new = max(0, min(new, size))
            self.pos[h] = new
            self.wr32(blk, size)                           # server writes folder +0x20 word
            self.tr.log('HIFIFILE', f'Seek(h={h}, off={off_s}, whence={whence & 0xff}) -> pos={new}; blk+0 := size {size}')
            self._deliver_ch2_reply(0x6A, 0)
        elif cmd == 0x6B:                                  # Read
            blk = param
            buf, n = self.rd32(blk), self.rd32(blk + 4)
            h = self.rd(blk + 8, 1)[0]
            cur = self.pos.get(h, 0)
            chunk = self.media[cur:cur + n]
            if chunk:
                self.u.mem_write(buf, chunk)
            self.pos[h] = cur + len(chunk)
            self.wr32(blk + 4, len(chunk))                 # result word: bytes read
            self.reads_served += 1
            self.bytes_served += len(chunk)
            self.tr.log('HIFIFILE', f'Read(h={h}, buf={buf:#010x}, n={n}) -> {len(chunk)} bytes from pos {cur}')
            self._deliver_ch2_reply(0x6C, 0)
        elif cmd == 0x6D:                                  # Write (not expected in playback)
            self.tr.log('HIFIFILE', f'Write(blk={param:#010x}) -- acked, discarded')
            self._deliver_ch2_reply(0x6E, 0)
        elif cmd == 0x73:                                  # Close: param = handle value
            self.tr.log('HIFIFILE', f'Close(h={param})')
            self._deliver_ch2_reply(0x74, 0)
        elif cmd == 0x6F:                                  # info query: folder +0x20 field
            self._deliver_ch2_reply(0x70, size)
        elif cmd == 0x71:                                  # info query: folder +0x10 field
            self._deliver_ch2_reply(0x72, 0)

    # ---------- system -> decoder messages (receiver effects replicated) ----------
    def send_ch1(self, cmd, param=0):
        """Replicates fn 0x010012fc (ch1 command receiver)."""
        cw, has_arg = CH1_TRANSLATE[cmd]
        self.tr.log('SYS', f'ch1 cmd {cmd:#06x} -> command word {cw}' + (f' arg={param:#x}' if has_arg else ''))
        if has_arg:
            self.wr32(ARGWORD, param)
        self.wr32(CMDWORD, cw)

    def send_info65(self):
        """Replicates fn 0x01001390's 0x65 case (generic layout, fmt not in {2,7}):
        the system pushes the open-info struct; the decoder copies fields and
        sets ctrl[0]=1, which arms the open state (buffer setup + ch2 0x66)."""
        size = len(self.media)
        self.u.mem_write(SCRATCH, bytes(0x18))
        self.wr8(SCRATCH + 0, self.handle)
        self.wr32(SCRATCH + 4, size)                       # -> [0x01022230]
        self.wr32(SCRATCH + 8, 0)                          # -> handle_table[handle]
        self.wr32(SCRATCH + 0x14, self.fmt_word)           # -> [0x01022224]
        self.tr.log('SYS', f'ch2 0x65 info push: handle={self.handle} size={size} fmt={self.fmt_word} (struct @{SCRATCH:#x})')
        self.wr32(0x01022118, self.handle)
        self.wr32(0x01022230, size)
        self.wr32(HANDLE_TABLE + 4 * self.handle, 0)
        self.wr32(FMTWORD, self.fmt_word)
        self.wr8(CTRL, 1)

    # ---------- execution driver ----------
    def run_slices(self, max_slices, until=None, slice_insns=200_000):
        from unicorn import UcError
        for _ in range(max_slices):
            self.tr.slice_no += 1
            pc = self.u.reg_read(UC_ARM_REG_PC)
            try:
                # all decoder code is Thumb; the raw PC reads back even, and
                # Unicorn picks ARM vs Thumb from the start address's low bit
                self.u.emu_start(pc | 1, 0xFFFFFFF0, count=slice_insns)
            except UcError as e:
                self.tr.log('FAULT', f'emu_start error at slice {self.tr.slice_no}: {e} pc={self.u.reg_read(UC_ARM_REG_PC):#010x}')
                return False
            if until and until():
                return True
        return False

    def boot(self):
        sp = struct.unpack('<I', self.code[0:4])[0]
        reset = struct.unpack('<I', self.code[4:8])[0]
        self.tr.log('BOOT', f'SP={sp:#010x} reset={reset:#010x} (VA {CODE_VA + reset & ~1:#010x})')
        self.u.reg_write(UC_ARM_REG_SP, sp)
        # emu_start directly at the table-1 reset trampoline (thumb)
        self.tr_pc = reset & ~1  # 0-based local view
        from unicorn import UcError
        self.tr.slice_no += 1
        try:
            self.u.emu_start(self.tr_pc | 1, 0xFFFFFFF0, count=200_000)
        except UcError as e:
            self.tr.log('FAULT', f'boot slice error: {e}')
        return self.run_slices(400, until=lambda: self.ready)

    def dump_state(self):
        self.tr.log('STATE', f'cmdword={self.rd32(CMDWORD)} fmt={self.rd32(FMTWORD)} '
                             f'ctrl0={self.rd(CTRL,1)[0]} flag={self.rd(FLAG,1)[0]} '
                             f'initflag={self.rd(INITFLAG,1)[0]} pos={self.pos} '
                             f'reads={self.reads_served} bytes={self.bytes_served}')
        info = self.rd(INFO_STRUCT, 0x30)
        words = struct.unpack('<12I', info)
        self.tr.log('STATE', 'info struct 0x010227f4: ' + ' '.join(f'{w:#010x}' for w in words))


def main():
    module = int(sys.argv[1]) if len(sys.argv) > 1 else 76
    media = sys.argv[2] if len(sys.argv) > 2 else 'test44.flac'
    h = Harness(module, media, trace_path='run_log.txt')
    ok = h.boot()
    h.tr.log('PHASE', f'boot+ready: {ok}')
    if not ok:
        h.dump_state()
        h.tr.log('BLOCKER', 'decoder did not signal ready -- see faults above')
        return 1
    h.send_info65()
    got = h.run_slices(400, until=lambda: h.open_notified)
    h.tr.log('PHASE', f'open notify (0x66): {got}')
    h.dump_state()
    # AUDIO_DECODE_OPEN: system ch1 cmd 1 -> command word 1
    h.send_ch1(1)
    got = h.run_slices(600, until=lambda: h.info_reported not in (None, 'pending-param'))
    h.tr.log('PHASE', f'info reported: {got} param={h.info_reported}')
    h.dump_state()
    # position poll: system ch1 cmd 4 -> command word 2
    for i in range(2):
        h.send_ch1(4)
        h.run_slices(300)
        h.tr.log('PHASE', f'position poll {i} done')
        h.dump_state()
    h.tr.log('DONE', f'reads served={h.reads_served} bytes={h.bytes_served} media={h.media_name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
