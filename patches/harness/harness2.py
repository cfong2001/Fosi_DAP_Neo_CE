#!/usr/bin/env python3
"""Core-1 emulation harness, milestone 2 (Phase D). Extends harness.py's
Harness with instrumentation only -- harness.py is not modified.

Adds:
- block hooks on the decode chain (entry + selected return sites) with
  argument capture,
- state probes of the codec/stream/flag cells after every phase,
- snapshot-diffing of the whole data window (0x01020000..0x01060000) so
  any PCM-sized write burst anywhere is visible,
- direct codec-function calls (emu75-style) for trigger experiments.

All hook addresses are module 76, 0-based core-1 code view (execution view).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import Harness, DATA_VA, HANDLE_TABLE  # noqa: E402
from unicorn import UC_HOOK_BLOCK  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,  # noqa: E402
                               UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)

# ---- module 76 code offsets (0-based view) ----
FN = {
    'sel12_decode': 0x2B9A, 'getbuffer': 0x2BD4, 'frame_decode': 0x2E2C,
    'flac_decode_frame': 0x48FA, 'decode_frame': 0x47C4, 'hdr_parse': 0x44EA,
    'pcm_out': 0x2E9A, 'pump232e': 0x232E, 'bufsetup490': 0x490,
    'vtable_install': 0x456, 'open_tail2782': 0x2782, 'flagclear_b16': 0xB16,
    'ch3_handler': 0x884, 'wrap_open': 0x4D08, 'wrap_pos': 0x4D26,
    'codec_fn': 0x2ADC, 'seek34cc': 0x34CC,
}
# return sites (block right after the BL in the caller) -> (name, fn)
RET = {
    0x4940: 'decode_frame',        # in flac_decode_frame after bl 0x47c4
    0x2E3A: 'flac_decode_frame',   # in frame_decode after bl 0x48fa
    0x2BB2: 'frame_decode',        # in sel12 after bl 0x2e2c
    0x47EC: 'hdr_parse',           # in decode_frame after bl 0x44ea
    0x49DC: 'pcm_out',             # in flac_decode_frame after bl 0x2e9a
}
# key data cells (VA view)
CODEC_STATE = 0x010459A0           # +0x18 total samples, +0x28 decoded samples (u64)
STREAM_STATE = 0x010222C8          # {cursor, remaining} of FLAC input buffer
FLAC_STATE = 0x0103C958            # FLAC decoder state (bitreader at +0x20)
INBUF = 0x01038950                 # FLAC input bitstream buffer
CH_BUF = (0x0103C9A0, 0x010411A0)  # FLAC state +0x48 / +0x4848 channel buffers (s32 planes)
FREQ_FLAG = 0x01022130             # byte cleared by ch3 cmd 6 via fn 0xb16
CTRLC = 0x0102229C                 # ctrl+0xc (FreqChange-timeout notification)
OUTCELL = 0x010222AC               # flac size/alloc cell passed by frame_decode
WIN_LO, WIN_HI = 0x01020000, 0x01060000


class H2(Harness):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.counts = {}
        self.calls = []            # (name, r0, r1, r2) at entry
        self.rets = []             # (name, r0) at return site
        for name, at in FN.items():
            self.u.hook_add(UC_HOOK_BLOCK, self._mk_entry(name), begin=at, end=at)
        for at, name in RET.items():
            self.u.hook_add(UC_HOOK_BLOCK, self._mk_ret(name), begin=at, end=at)
        self._snap = None

    def _mk_entry(self, name):
        def cb(u, addr, size, data):
            self.counts[name] = self.counts.get(name, 0) + 1
            if name in ('sel12_decode', 'frame_decode', 'flac_decode_frame',
                        'decode_frame', 'pcm_out', 'bufsetup490', 'getbuffer',
                        'open_tail2782', 'hdr_parse', 'seek34cc'):
                self.calls.append((name, u.reg_read(UC_ARM_REG_R0),
                                   u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2)))
        return cb

    def _mk_ret(self, name):
        def cb(u, addr, size, data):
            self.rets.append((name, u.reg_read(UC_ARM_REG_R0)))
        return cb

    # ---- probes ----
    def q64(self, addr):
        return struct.unpack('<Q', self.rd(addr, 8))[0]

    def probe(self, tag):
        cs = CODEC_STATE
        p = {
            'total_samples': self.q64(cs + 0x18), 'decoded_samples': self.q64(cs + 0x28),
            'out_idx': self.rd32(0x010222A4), 'outbase_cell': self.rd32(0x01022114),
            'outptr0': self.rd32(0x010222B4), 'outptr1': self.rd32(0x010222B8),
            'outcnt_cell': self.rd32(cs + 8),
            'stream_cur': self.rd32(STREAM_STATE), 'stream_rem': self.rd32(STREAM_STATE + 4),
            'outcell_222ac': self.rd32(OUTCELL),
            'freq_flag': self.rd(FREQ_FLAG, 1)[0], 'ctrl_c': self.rd32(CTRLC),
            'vtable': self.rd32(0x010220F4), 'handle_tab3': self.rd32(0x01022234 + 12),
            'flac_blk': self.rd32(FLAC_STATE + 4), 'flac_30': self.rd32(FLAC_STATE + 0x30),
            'flac_40': self.rd32(FLAC_STATE + 0x40),
        }
        self.tr.log('PROBE', tag + ' ' + ' '.join(f'{k}={v:#x}' if isinstance(v, int) and v > 9 else f'{k}={v}' for k, v in p.items()))
        return p

    def bufhash(self, tag):
        import hashlib
        out = []
        for base in (self.rd32(0x010222B4), self.rd32(0x010222B8)):
            if WIN_LO <= base < WIN_HI - 0x100:
                out.append((hex(base), hashlib.sha256(self.rd(base, 0x9000)).hexdigest()[:10],
                            sum(1 for b in self.rd(base, 0x9000) if b)))
        ch = [(hex(a), hashlib.sha256(self.rd(a, 0x4800)).hexdigest()[:10]) for a in CH_BUF]
        self.tr.log('BUFHASH', f'{tag} pcm={out} chan={ch}')
        return out, ch

    def snapdiff(self, tag):
        cur = self.rd(WIN_LO, WIN_HI - WIN_LO)
        if self._snap is not None:
            prev = self._snap
            ranges = []
            start = None
            for i in range(len(cur)):
                if cur[i] != prev[i]:
                    if start is None:
                        start = i
                elif start is not None:
                    ranges.append((start, i))
                    start = None
            if start is not None:
                ranges.append((start, len(cur)))
            desc = ', '.join(f'{WIN_LO + a:#x}+{b - a}' for a, b in ranges[:24])
            self.tr.log('SNAPDIFF', f'{tag}: {len(ranges)} ranges, {sum(b - a for a, b in ranges)} bytes: {desc}')
        self._snap = cur

    # ---- corrected HifiFile server semantics (milestone 2 fidelity fix) ----
    def _serve_rpc(self, cmd, param):
        """Overrides harness.py's server with the reply values the real
        module-33 server (fn 0x030895DA, disassembled) actually sends:
        - Read (0x6B): reply param = bytes read (the FS call's return value,
          sent via the param mailbox writer 0x0306D0AC). The decoder's Read
          stub returns this word from 0x01022298, and both slot producers
          (pump 0x232E, slot-advance 0x22C6) store it as the slot's
          valid-byte count -- param 0 (milestone 1) made every refilled
          slot look empty, so the buffered reader (fn 0x237C) returned 0
          and decode_frame reported EOF on a full file.
        - Read block result word [blk+4] and Seek block word [blk+0]:
          the server writes the folder entry's +0x20 word AFTER the FS
          call, i.e. the FS-side position for the handle; the stubs copy
          it into handle_table[handle], which the runtime's position
          helpers (0x2460..) treat as the delivered-data end. We write
          the host position after the operation.
        All other cases replicate harness.py exactly."""
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
            self.wr32(blk, new)                            # folder+0x20 analog: post-seek position
            self.tr.log('HIFIFILE', f'Seek(h={h}, off={off_s}, whence={whence & 0xff}) -> pos={new}; blk+0 := pos {new}')
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
            self.wr32(blk + 4, self.pos[h])                # folder+0x20 analog: post-read position
            self.reads_served += 1
            self.bytes_served += len(chunk)
            self.tr.log('HIFIFILE', f'Read(h={h}, buf={buf:#010x}, n={n}) -> {len(chunk)} bytes from pos {cur}')
            self._deliver_ch2_reply(0x6C, len(chunk))      # param = bytes read (server-proven)
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

    # ---- direct codec call (emu75-style) ----
    TRAP = 0x0001FF00              # in code window tail; filled with bx lr loop

    def call_codec(self, sel, a1=0, a2=0, a3=0):
        """Call the FLAC codec function (table[6] target 0x2adc) directly."""
        u = self.u
        u.mem_write(self.TRAP, b'\xfe\xe7')          # b .
        sp = u.reg_read(UC_ARM_REG_SP)
        for r, v in ((UC_ARM_REG_R0, sel), (UC_ARM_REG_R1, a1), (UC_ARM_REG_R2, a2),
                     (UC_ARM_REG_R3, a3), (UC_ARM_REG_LR, self.TRAP | 1)):
            u.reg_write(r, v)
        from unicorn import UcError
        try:
            u.emu_start(FN['codec_fn'] | 1, self.TRAP, count=50_000_000)
        except UcError as e:
            self.tr.log('FAULT', f'call_codec sel={sel}: {e} pc={u.reg_read(UC_ARM_REG_PC):#x}')
        u.reg_write(UC_ARM_REG_SP, sp)
        return u.reg_read(UC_ARM_REG_R0)


OUT_STATE = 0x010220E4             # audio output state: +0 / +4 DMA-complete flags


class H3(H2):
    """H2 + decoder-local DMA completion model.

    The FLAC decode path outputs each frame through fn 0x524A (and its
    sibling fn 0x51F4), which programs the decoder-local DMA (fn 0xD5E)
    and then blocks in a WFI loop until the DMA-complete handler
    (fn 0x518A / fn 0x5174, dispatched by the interrupt walker 0x5198)
    sets a flag in the output state at 0x010220E4 (+4 for 0x524A, +0 for
    0x51F4). The harness has no interrupt source, so without this model
    the decoder parks in WFI forever (observed: PC stuck at the wfi
    helper 0x28DC). The hooks sit on the two `bl wfi` sites and set the
    same flag the handler would -- a zero-latency DMA model. Every
    0x524A/0x51F4/0xD5E entry is logged so the PCM source buffers can be
    identified from the descriptor arguments."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.dma_log = []
        self.pcm = bytearray()
        self.pcm_frames = []
        self.frames_out = []       # (samples, ch0 s32 bytes, ch1 s32 bytes) per 0x524A call
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_dma_done(4), begin=0x52DC, end=0x52DC)
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_dma_done(0), begin=0x5234, end=0x5234)
        for name, at in (('out524a', 0x524A), ('out51f4', 0x51F4), ('dma_d5e', 0xD5E)):
            self.u.hook_add(UC_HOOK_BLOCK, self._mk_dma_log(name), begin=at, end=at)
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_pcm_cap(), begin=0x2E9A, end=0x2E9A)
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_pcm_ret(), begin=0x49DC, end=0x49DC)
        # --- hardware LPC-offload model -------------------------------------
        # decode_subframe_lpc (0x423E) for predictor order >= 3 does NOT
        # reconstruct the signal on the CPU: it uploads the coefficient
        # array to the audio block at 0x0106B000 (memcpy fn 0x5090, called
        # at 0x4312), programs order/shift via fn 0x2AC4 (called at 0x4308),
        # and hands the residual plane to fn 0x524A (DMA out). The audio
        # hardware performs FLAC__lpc_restore_signal. The model below
        # captures (order, shift, coefs) and reconstructs in Python at the
        # fn 0x2E9A interleave point, where both channel planes are final.
        self.lpc_pending = {}      # plane addr -> (order, shift, coefs memory order)
        self.lpc_frames = []       # (blocksize, ch0 list, ch1 list) reconstructed
        # hook the callees (the call sites 0x4308/0x4312 are mid-block and a
        # block hook there never fires): fn 0x2AC4 entry carries
        # (r1 = order, r2 = shift); fn 0x5090 entry carries (r0 = coef src,
        # r1 = dst, r2 = word count) — record only uploads to 0x0106B000.
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_lpc_cfg(), begin=0x2AC4, end=0x2AC4)
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_lpc_coef(), begin=0x5090, end=0x5090)
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_frame_asm(), begin=0x2E9A, end=0x2E9A)

    def _mk_lpc_cfg(self):
        def cb(u, addr, size, data):
            self._lpc_cfg = (u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2))
        return cb

    def _mk_lpc_coef(self):
        def cb(u, addr, size, data):
            if u.reg_read(UC_ARM_REG_R1) != 0x0106B000:
                return
            src = u.reg_read(UC_ARM_REG_R0)
            n = u.reg_read(UC_ARM_REG_R2)
            coefs = list(struct.unpack(f'<{n}i', self.rd(src, 4 * n))) if 0 < n <= 32 else []
            self._lpc_coef = coefs
        return cb

    @staticmethod
    def _lpc_restore(plane, order, shift, coefs_mem):
        # FLAC LPC: s[i] = residual[i] + ((sum_j c[j] * s[i-1-j]) >> shift).
        # The decoder stores coefficients reversed on the stack (stream
        # order c[order-1] first); the uploaded array keeps that order.
        c = list(reversed(coefs_mem))
        s = list(plane)
        for i in range(order, len(s)):
            acc = 0
            for j in range(order):
                acc += c[j] * s[i - 1 - j]
            s[i] = (plane[i] + (acc >> shift)) & 0xFFFFFFFF
            if s[i] >= 0x80000000:
                s[i] -= 0x100000000
        return s

    def _mk_frame_asm(self):
        def cb(u, addr, size, data):
            sp = u.reg_read(UC_ARM_REG_SP)
            cnt = struct.unpack('<I', self.rd(sp, 4))[0]
            if not (0 < cnt <= 0x1200):
                return
            chans = []
            for plane_addr in CH_BUF:
                plane = list(struct.unpack(f'<{cnt}i', self.rd(plane_addr, 4 * cnt)))
                rec = self.lpc_pending.pop(plane_addr, None)
                if rec is not None:
                    order, shift, coefs = rec
                    plane = self._lpc_restore(plane, order, shift, coefs)
                chans.append(plane)
            self.lpc_frames.append((cnt, chans[0], chans[1]))
        return cb
        # DMA channel status registers (fn 0x50A8 reads [0x01060008 - 0x3C*ch]
        # and the output caller spins until bit 0x8000 reads back; the FIFO
        # feed loop at 0x50BA polls bit 0 of the same register). With a
        # zero-latency DMA the transfer is complete when programmed, so the
        # status bits are set at every dma_d5e / out entry and every 0x50A8
        # read.
        self.u.hook_add(UC_HOOK_BLOCK, self._mk_status(), begin=0x50A8, end=0x50A8)

    # -- milestone-2 job-2 helpers -------------------------------------------
    eos_sent = False

    def _on_send_cmd(self, u, addr, size, data):
        super()._on_send_cmd(u, addr, size, data)
        val, unit, ch = self._regs()
        if ch == 1 and val == 6:
            self.eos_sent = True     # decoder -> system end-of-stream notify

    def rd64(self, addr):
        return struct.unpack('<Q', self.rd(addr, 8))[0]

    def switch_media(self, path):
        """Point the host file layer at a different file WITHOUT touching
        decoder state (the load-skipped transition: a new 0x65 push for a
        new file on the resident decoder)."""
        from pathlib import Path as _P
        self.media = _P(path).read_bytes()
        self.media_name = str(path)
        self.pos = {}
        self.tr.log('SYS', f'host media switched to {path} ({len(self.media)} bytes) '
                           f'-- decoder NOT reset')

    def snapshot(self, label):
        """Curated decoder-state snapshot for the reload-vs-skip diff."""
        snap = {
            'label': label,
            'param_page': self.rd(0x01020000, 144),
            'fmt_word': self.rd32(0x01022224),
            'file_size': self.rd32(0x01022230),
            'handle_tab3': self.rd32(HANDLE_TABLE + 12),
            'ctrl_block': self.rd(0x01022114, 0x30),
            'freq_flag': self.rd(0x01022130, 1)[0],
            'dma_flags': self.rd(0x010220E4, 8),
            'total_samples': self.rd64(CODEC_STATE + 0x18),
            'decoded_samples': self.rd64(CODEC_STATE + 0x28),
            'event_bitmap': self.rd32(0x010459F0),
            'flac_30': self.rd32(FLAC_STATE + 0x30),
            'flac_34': self.rd32(FLAC_STATE + 0x34),
            'flac_40': self.rd32(FLAC_STATE + 0x40),
            'fs_struct': self.rd(0x01022924, 0x40),
            'fill_table': self.rd(0x01022944, 8),
            'stream_state': self.rd(0x010222C8, 0x10),
            'out_idx': self.rd32(0x010222A4),
            'out_cell': self.rd32(0x010222AC),
            'data_window': self.rd(0x01020000, 0x40000),
        }
        self.tr.log('SNAP', f'{label}: total={snap["total_samples"]} '
                            f'decoded={snap["decoded_samples"]} fmt={snap["fmt_word"]} '
                            f'size={snap["file_size"]} flac30={snap["flac_30"]:#x} '
                            f'out_idx={snap["out_idx"]} out_cell={snap["out_cell"]:#x}')
        return snap

    def _mk_pcm_cap(self):
        # At fn 0x2E9A entry: r0 = destination double buffer, stack arg 0 =
        # sample count. At its return site in flac_decode_frame's tail
        # (0x49DC) the buffer holds the finished interleaved s16 frame.
        def entry(u, addr, size, data):
            sp = u.reg_read(UC_ARM_REG_SP)
            cnt = struct.unpack('<I', self.rd(sp, 4))[0]
            self._pcm_pending = (u.reg_read(UC_ARM_REG_R0), cnt)
        return entry

    def _mk_pcm_ret(self):
        def cb(u, addr, size, data):
            pend = getattr(self, '_pcm_pending', None)
            if pend:
                base, cnt = pend
                self._pcm_pending = None
                if 0 < cnt <= 0x1200:
                    self.pcm += self.rd(base, cnt * 4)   # s16 stereo interleaved
                    self.pcm_frames.append((cnt, base))
                    self.tr.log('PCM', f'captured {cnt} samples from double buffer '
                                       f'{base:#x} (total {len(self.pcm) // 4})')
        return cb

    def _set_dma_status(self, ch):
        addr = 0x01060008 - 0x3C * ch
        try:
            self.wr32(addr, self.rd32(addr) | 0x8001)
        except Exception:
            pass

    def _mk_status(self):
        def cb(u, addr, size, data):
            self._set_dma_status(u.reg_read(UC_ARM_REG_R0))
        return cb

    def _mk_dma_done(self, off):
        def cb(u, addr, size, data):
            self.wr32(OUT_STATE + off, 1)
            self.tr.log('DMA', f'completion modelled: [{OUT_STATE + off:#x}] := 1')
        return cb

    def _mk_dma_log(self, name):
        def cb(u, addr, size, data):
            sp = u.reg_read(UC_ARM_REG_SP)
            args = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                            UC_ARM_REG_R2, UC_ARM_REG_R3)]
            stk = struct.unpack('<2I', self.rd(sp, 8))
            self.dma_log.append((name, *args, *stk))
            self.tr.log('DMA', f'{name} r0={args[0]:#x} r1={args[1]:#x} r2={args[2]:#x} '
                               f'r3={args[3]:#x} stk=({stk[0]:#x},{stk[1]:#x})')
            if name == 'dma_d5e':
                self._set_dma_status(args[0])
            if name == 'out524a':
                # PCM capture: r0 = channel-0 plane, r2 = samples this frame;
                # channel-1 plane sits at FLAC state +0x4848 (CH_BUF[1]).
                n = args[2]
                if 0 < n <= 0x1200:
                    self.frames_out.append((n, self.rd(CH_BUF[0], 4 * n),
                                            self.rd(CH_BUF[1], 4 * n)))
                    self.tr.log('DMA', f'captured frame planes: {n} samples x2ch (s32)')
                # register the pending LPC offload for this plane so the
                # frame assembler at fn 0x2E9A reconstructs it in Python
                cfg = getattr(self, '_lpc_cfg', None)
                if cfg is not None and getattr(self, '_lpc_coef', None):
                    self.lpc_pending[args[0]] = (cfg[0], cfg[1], list(self._lpc_coef))
                    self.tr.log('DMA', f'LPC offload: plane={args[0]:#x} order={cfg[0]} '
                                       f'shift={cfg[1]} coefs={self._lpc_coef}')
        return cb


def phase_a(media):
    h = H2(76, media, trace_path='run_log_m2a.txt')
    assert h.boot(), 'boot failed'
    h.probe('after-boot')
    h.send_info65()
    assert h.run_slices(400, until=lambda: h.open_notified), 'no 0x66'
    h.probe('after-0x65')
    h.send_ch1(1)
    got = h.run_slices(600, until=lambda: h.info_reported not in (None, 'pending-param'))
    h.tr.log('PHASE', f'open info reported: {got}')
    h.probe('after-open')
    h.bufhash('after-open')
    h.snapdiff('after-open')
    for i in range(6):
        h.send_ch1(4)
        h.run_slices(300)
        h.tr.log('PHASE', f'poll {i} done')
        h.probe(f'poll-{i}')
        h.bufhash(f'poll-{i}')
        h.snapdiff(f'poll-{i}')
        if h.counts.get('pcm_out'):
            h.tr.log('MILESTONE', 'pcm_out (fn 0x2e9a) was called!')
            break
    h.tr.log('COUNTS', str(h.counts))
    h.tr.log('RETS', str(h.rets[:40]))
    h.tr.log('DONE', f'reads={h.reads_served} bytes={h.bytes_served}')
    return h


if __name__ == '__main__':
    media = sys.argv[1] if len(sys.argv) > 1 else 'test44.flac'
    mode = sys.argv[2] if len(sys.argv) > 2 else 'phasea'
    if mode == 'phasea':
        phase_a(media)
