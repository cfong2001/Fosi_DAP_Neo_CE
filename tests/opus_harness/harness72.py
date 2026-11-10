#!/usr/bin/env python3
"""Core-1 emulation harness parameterised for module 72 (WMA stock /
Opus transplant). Subclasses the Phase D harness (work/harness/harness.py)
with module 72's receiver-derived constants; the Phase D files are not
modified.

Constants, all derived from module 72's own binary (see results.md):
- MU send fns: cmd 0x103E0 (writes [unit + 0x30 + 8*ch]), param 0x1040C
  (+0x34 + 8*ch); printf 0x902. Boot sends READY as send(1, 0, 0) from
  0x1628, which pins the argument order (value, unit, channel).
- ch1 receiver 0x139C: command word 0x0102220C, argument word 0x01022210,
  translation identical to module 76 (1->1, 4->2, 7->4, 9->5, 0x0B->3+arg,
  0x0D->6+arg, 0xCB->14+arg, 0xCD->13+arg).
- ch2 receiver 0x142C: control struct 0x01022284 (+0 state, +4 last cmd,
  +8 last param), completion flag byte 0x01022220, first-read flag
  0x01022221, per-handle position table 0x01022228.
  0x65 case: [0x01022208] = struct ptr, byte[struct+0] -> [0x01022108]
  (file handle), word[struct+4] -> [0x01022224] (file size),
  word[struct+8] -> position table[handle], word[struct+0x14] ->
  [0x01022214] (codec type word), ctrl[0] = 1.
  Reply states: 0x6A->2, 0x6C->3, 0x6E->4, 0x70->5, 0x72->6,
  0x74->7 if param != 0, 0xD1->9 if param != 0. The 0x6C case also runs
  first-reply bookkeeping while [0x01022221] == 0: position
  table[byte[read block + 8]] = word[read block + 4],
  [0x01026B10 + 4*[0x01026B0C]] = reply param, [0x01026B00] = 0,
  [0x01022221] = 1. The read block is the fixed block at 0x01022254.
- HifiFile stubs: Seek 0x206 (block 0x01022248), Read 0x26C (block
  0x01022254; refuses until [0x01022221] == 1), Write 0x2DC (block
  0x01022260). The stubs copy the block result word into the position
  table themselves on completion and return the status byte at
  [0x0102228C] (ctrl + 8 low byte).
- Server semantics (module 33 fn 0x030895DA, milestone-2 form): Read
  replies carry param = bytes read and the block's +4 word becomes the
  post-read position; Seek replies write the post-seek position into
  the block's +0 word.
- Info block 0x010269C0 (codec_abi layout): +0x00 time ms, +0x04 length
  ms, +0x08 bitrate, +0x0C bps, +0x10 sample rate, +0x14 channels,
  +0x1C PCM pointer, +0x20 PCM frames (interleaved).
- Main loop (0x164A): command-word TBB at 0x167A: 1 -> open (wrapper
  0x10138; success fills info and sends ch1 cmd 3 + info block, failure
  sends ch1 cmd 2), 2 -> decode/position (wrapper 0x10156; failure sends
  ch1 cmd 6 = end of stream; success updates time, runs GETBUFFER into
  info +0x1C/+0x20 and sends ch1 cmd 5 + info block), 3 -> seek (wrapper
  0x10174, replies ch1 cmd 0xC), 6 -> close (wrapper 0x1023C, replies
  ch1 cmd 0xE), 7 -> file-buffer setup (fn 0x2940), 14 -> clear only,
  others -> no-op. ctrl[0] TBB at 0x18C6: state 1 = the 0x65-armed open
  state (fn 0x3C6 rate reserve, fn 0x2940 buffer setup, sends ch2 0x66).
- Delay fns read the parameter page exactly like module 76: fn 0xB6C
  divides [page + 0x20] by 1e6, fn 0xB90 divides [page + 0x24] by 3000,
  so the base harness's page values (96 MHz / 24 MHz) apply unchanged.
- Console port at 0x400B0000: fn 0x198 waits for bit 1 of the status
  word at +0x7C (transmitter ready) and then writes the message word
  to +0x00; fn 0x9A/0x168 send formatted command strings through it
  during codec open (the transplant's codec glue uses it, the stock
  WMA path does not). Only fn 0x198 references the base (literal pool
  at 0x1AC). The harness models the port as always ready by seeding
  +0x7C with bit 1 set, the same category of hardware modelling as the
  MU server. On hardware the peripheral raises the bit itself.
"""
import struct
import sys
from pathlib import Path

WS = Path.home() / 'workspace/fosi-dap-neo'
sys.path.insert(0, str(WS / 'work/harness'))
import harness as H  # noqa: E402

# ---- module 72 constants (0-based core-1 code view / absolute data VAs) ----
SEND_CMD, SEND_PARAM, PRINTF = 0x103E0, 0x1040C, 0x902
CMDWORD, ARGWORD, FMTWORD = 0x0102220C, 0x01022210, 0x01022214
CTRL, FLAG, INITFLAG = 0x01022284, 0x01022220, 0x01022221
HANDLE_TABLE = 0x01022228                    # per-handle position words
INFO = 0x010269C0                            # codec info block
FILE_HANDLE_CELL, FILE_SIZE_CELL = 0x01022108, 0x01022224
INFO_PTR_CELL = 0x01022208                   # ch2 receiver stores struct ptr
READ_BLOCK = 0x01022254
SCRATCH72 = 0x0105F800                       # above the plug-in .noinit end
STACK_FLOOR, STACK_TOP = 0x01020090, 0x01022000
EVENT_FLAGS = (0x0103CB18, 0x0103CB58)       # runtime event-flag words

CODEC_TYPE_WMA = 1

# Rebind the base harness's module-76 globals before any instance is built.
H.SEND_CMD, H.SEND_PARAM, H.PRINTF = SEND_CMD, SEND_PARAM, PRINTF
H.CMDWORD, H.ARGWORD, H.FMTWORD = CMDWORD, ARGWORD, FMTWORD
H.CTRL, H.FLAG, H.INITFLAG, H.HANDLE_TABLE = CTRL, FLAG, INITFLAG, HANDLE_TABLE
H.INFO_STRUCT = INFO

TRANSPLANT_BIN = WS / 'work/opus_transplant/module72_opus.bin'
CODE_LEN, DATA_LEN = 0x162C0, 0x67C0


class H72(H.Harness):
    def __init__(self, media=None, transplant=False, trace_path='run_log.txt',
                 count_insns=False):
        super().__init__(72, media, fmt_word=CODEC_TYPE_WMA, handle=3,
                         trace_path=trace_path)
        # console port 0x400B0000: model the transmitter as always ready
        self.wr32(0x400B007C, 2)
        self.transplant = transplant
        if transplant:
            blob = TRANSPLANT_BIN.read_bytes()
            assert len(blob) == CODE_LEN + DATA_LEN, len(blob)
            self.code = blob[:CODE_LEN]
            self.data = blob[CODE_LEN:]
            self.u.mem_write(0x00000000, self.code)
            self.u.mem_write(H.CODE_VA, self.code)
            # keep the harness parameter page (first 0x90 bytes) as built
            self.u.mem_write(H.DATA_VA + 0x90, self.data[0x90:])
        # session tracking (set by _on_send_cmd)
        self.eos_sent = False
        self.open_failed = False
        self.close_replied = False
        self.seek_replied = None
        self.pos_replies = 0
        self.pcm = bytearray()
        self.pcm_blocks = []          # (frames, channels, ptr) per cmd-5 reply
        self._pcm_seen = 0
        # instruction counting (vorbis decode_cost method)
        self.counting = False
        self.insn_count = 0
        self.block_count = 0
        if count_insns:
            self._install_counter()

    # ---- instruction counting: block hooks + cached capstone counts ----
    def _install_counter(self):
        import capstone
        from unicorn import UC_HOOK_BLOCK
        md = capstone.Cs(capstone.CS_ARCH_ARM,
                         capstone.CS_MODE_THUMB | capstone.CS_MODE_MCLASS)
        cache = {}

        def hook(u, addr, size, data):
            if not self.counting:
                return
            key = (addr, size)
            c = cache.get(key)
            if c is None:
                code = bytes(u.mem_read(addr, size))
                c = sum(1 for _ in md.disasm(code, addr))
                cache[key] = c
            self.insn_count += c
            self.block_count += 1

        self.u.hook_add(UC_HOOK_BLOCK, hook)

    # ---- MU send tracking ----
    def _on_send_cmd(self, u, addr, size, data):
        super()._on_send_cmd(u, addr, size, data)
        val, unit, ch = self._regs()
        if ch == 1:
            if val == 6:
                self.eos_sent = True
            elif val == 2:
                self.open_failed = True
            elif val == 5:
                self.pos_replies += 1
            elif val == 0x0C:
                self.seek_replied = 'pending-param'
            elif val == 0x0E:
                self.close_replied = True

    def _on_send_param(self, u, addr, size, data):
        super()._on_send_param(u, addr, size, data)
        val, unit, ch = self._regs()
        if ch == 1 and self.seek_replied == 'pending-param':
            self.seek_replied = val

    # ---- HifiFile server (milestone-2 semantics) + receiver replication ----
    def _deliver_ch2_reply(self, cmd, param):
        """Replicates module 72's ch2 receiver (0x142C) for an RPC reply."""
        self.wr32(CTRL + 4, cmd)
        self.wr32(CTRL + 8, param)
        state = H.CH2_REPLY_STATE.get(cmd)
        if cmd == 0x74:
            state = 7 if param != 0 else None
        elif cmd == 0xD1:
            state = 9 if param != 0 else None
        if state is not None:
            self.wr8(CTRL, state)
        if cmd == 0x6C and self.rd(INITFLAG, 1)[0] == 0:
            # first-read-reply bookkeeping, verbatim from the receiver
            blk = READ_BLOCK
            h = self.rd(blk + 8, 1)[0]
            self.wr32(HANDLE_TABLE + 4 * h, self.rd32(blk + 4))
            idx = self.rd32(0x01026B0C)
            self.wr32(0x01026B10 + 4 * idx, param)
            self.wr32(0x01026B00, 0)
            self.wr8(INITFLAG, 1)
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
            self.wr32(blk, new)                            # post-seek position
            self.tr.log('HIFIFILE', f'Seek(h={h}, off={off_s}, whence={whence & 0xff}) -> pos={new}')
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
            self.wr32(blk + 4, self.pos[h])                # post-read position
            self.reads_served += 1
            self.bytes_served += len(chunk)
            self.tr.log('HIFIFILE', f'Read(h={h}, buf={buf:#010x}, n={n}) -> {len(chunk)} bytes from pos {cur}')
            self._deliver_ch2_reply(0x6C, len(chunk))      # param = bytes read
        elif cmd == 0x6D:                                  # Write
            self.tr.log('HIFIFILE', f'Write(blk={param:#010x}) -- acked, discarded')
            self._deliver_ch2_reply(0x6E, 0)
        elif cmd == 0x73:                                  # Close
            self.tr.log('HIFIFILE', f'Close(h={param})')
            self._deliver_ch2_reply(0x74, 0)
        elif cmd == 0x6F:
            self._deliver_ch2_reply(0x70, size)
        elif cmd == 0x71:
            self._deliver_ch2_reply(0x72, 0)

    # ---- system -> decoder messages ----
    def send_info65(self):
        """Replicates module 72's ch2 receiver 0x65 case."""
        size = len(self.media)
        self.u.mem_write(SCRATCH72, bytes(0x18))
        self.wr8(SCRATCH72 + 0, self.handle)
        self.wr32(SCRATCH72 + 4, size)
        self.wr32(SCRATCH72 + 8, 0)
        self.wr32(SCRATCH72 + 0x14, self.fmt_word)
        self.tr.log('SYS', f'ch2 0x65 info push: handle={self.handle} size={size} fmt={self.fmt_word} (struct @{SCRATCH72:#x})')
        self.wr32(INFO_PTR_CELL, SCRATCH72)
        self.wr8(FILE_HANDLE_CELL, self.handle)
        self.wr32(FILE_SIZE_CELL, size)
        self.wr32(HANDLE_TABLE + 4 * self.handle, 0)
        self.wr32(FMTWORD, self.fmt_word)
        self.wr8(CTRL, 1)

    def switch_media(self, path):
        """New file on the resident decoder (gapless R1 pattern, no reset)."""
        self.media = Path(path).read_bytes()
        self.media_name = str(path)
        self.pos = {}
        self.eos_sent = False
        self.open_failed = False
        self.info_reported = None
        self.tr.log('SYS', f'host media switched to {path} ({len(self.media)} bytes) -- decoder NOT reset')

    # ---- info block helpers ----
    def info(self):
        w = struct.unpack('<12I', self.rd(INFO, 0x30))
        return {'time_ms': w[0], 'length_ms': w[1], 'bitrate': w[2],
                'bps': w[3], 'rate': w[4], 'channels': w[5],
                'pcm_ptr': w[7], 'pcm_frames': w[8]}

    def capture_pcm(self):
        """Copy out any PCM block reported since the last capture."""
        while self._pcm_seen < self.pos_replies:
            self._pcm_seen += 1
            inf = self.info()
            frames, ch, ptr = inf['pcm_frames'], inf['channels'], inf['pcm_ptr']
            if frames and ch and 0x01020000 <= ptr < 0x01060000:
                self.pcm += self.rd(ptr, frames * ch * 2)
                self.pcm_blocks.append((frames, ch, ptr))
                self.tr.log('PCM', f'captured block {frames} frames x{ch}ch from {ptr:#x} '
                                   f'(total {len(self.pcm)} bytes)')
            else:
                self.pcm_blocks.append((frames, ch, ptr))
                self.tr.log('PCM', f'reply with no PCM: frames={frames} ch={ch} ptr={ptr:#x}')

    # ---- driver helpers ----
    def open_current(self, max_slices=4000):
        """0x65 push, then ch1 cmd 1 (AUDIO_DECODE_OPEN). Returns the info
        dict on success, None on failure."""
        self.open_notified = False
        self.info_reported = None
        self.send_info65()
        if not self.run_slices(max_slices, until=lambda: self.open_notified):
            self.tr.log('PHASE', 'open FAILED: no ch2 0x66 notification')
            return None
        self.send_ch1(1)
        ok = self.run_slices(max_slices,
                             until=lambda: self.info_reported not in (None, 'pending-param')
                             or self.open_failed)
        if self.open_failed or not ok:
            self.tr.log('PHASE', f'open FAILED: info_reported={self.info_reported} open_failed={self.open_failed}')
            return None
        inf = self.info()
        self.tr.log('PHASE', f'open OK: rate={inf["rate"]} ch={inf["channels"]} '
                             f'bitrate={inf["bitrate"]} bps={inf["bps"]} length_ms={inf["length_ms"]}')
        # The runtime primes the first PCM buffer during open (the codec's
        # OPEN fills buffer 0 and the open path publishes it in the info
        # block); it precedes every poll-reported buffer in stream order.
        if inf['pcm_frames'] and inf['channels'] and 0x01020000 <= inf['pcm_ptr'] < 0x01060000:
            self.pcm += self.rd(inf['pcm_ptr'], inf['pcm_frames'] * inf['channels'] * 2)
            self.pcm_blocks.append((inf['pcm_frames'], inf['channels'], inf['pcm_ptr']))
            self._pcm_seen = self.pos_replies
            self.tr.log('PCM', f'captured open-primed buffer {inf["pcm_frames"]} frames '
                               f'x{inf["channels"]}ch from {inf["pcm_ptr"]:#x}')
        return inf

    def poll_decode(self, max_slices=6000, slice_insns=2_000_000):
        """One position poll (ch1 cmd 4 -> command word 2). Returns True if
        a cmd-5 reply arrived."""
        before = self.pos_replies
        self.send_ch1(4)
        self.run_slices(max_slices,
                        until=lambda: self.pos_replies > before or self.eos_sent,
                        slice_insns=slice_insns)
        self.capture_pcm()
        return self.pos_replies > before

    def decode_to_eos(self, max_polls=4000):
        """Poll until the decoder sends ch1 cmd 6 (end of stream)."""
        stalls = 0
        polls = 0
        while polls < max_polls and not self.eos_sent:
            got = self.poll_decode()
            polls += 1
            if not got and not self.eos_sent:
                stalls += 1
                if stalls >= 3:
                    break
            else:
                stalls = 0
        inf = self.info()
        self.tr.log('PHASE', f'decode done: polls={polls} eos={self.eos_sent} '
                             f'time_ms={inf["time_ms"]} pcm_bytes={len(self.pcm)} '
                             f'reads={self.reads_served} bytes_served={self.bytes_served}')
        return polls

    def close_current(self):
        self.close_replied = False
        self.send_ch1(0x0D, 0)                 # -> command word 6 (close)
        self.run_slices(2000, until=lambda: self.close_replied)
        self.tr.log('PHASE', f'close replied: {self.close_replied}')
        return self.close_replied
