"""Natural-advance scenario: state seeding and the decoder-core model.

Seeds the runtime state a playing track leaves behind (current-track
record, decoder output descriptor, resident codec glue) and stubs the
file service, then runs the playback task's end-of-track handler, the
stop-and-advance helper 0x03089AD6(0), exactly as the task does when it
takes event 0xEC.
"""
from machine import (Machine, ROOT, UC_HOOK_CODE, UC_ARM_REG_R0,
                     UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                     UC_ARM_REG_R4, UC_ARM_REG_R10, UC_ARM_REG_PC,
                     UC_ARM_REG_SP)

TRACK = 0x030F8000          # current-track record ([0x0304AD78] points here)
DEC_OUT = 0x0304B47C        # decoder output descriptor (shared with core 1)
CODEC = 0x0304B4D4          # current codec index
FILEINFO = 0x03023980
ADVANCE = 0x03089AD6        # stop + advance, called with r0 = 0 on 0xEC
LOAD_START = 0x03088D9C
DISPATCH = 0x03089C86        # codec dispatcher (message, arg)
DMA_START = 0x0305FF74      # dma_start(ch, src, dst, len, ...)
I2S_TX = 0x40030024
FOPEN = 0x030589B6
FCLOSE = 0x03058E8E
DIR_STEP = 0x0305D876       # walk n entries in the browse list
I2C_POLLS = (0x03060676, 0x030606D6, 0x0306071C, 0x030607CE, 0x03060836,
             0x0306088A)


class Scenario:
    def __init__(self, raw, ext=b'FLA', rate=44100, bits=16, channels=2,
                 decoder=None):
        self.m = m = Machine(raw)
        self.dec = decoder or Decoder()
        self.ext = ext
        m.w32(0x0304AD78, TRACK)
        # playlist position: track 3 of 12 in the current folder
        m.w16(FILEINFO + 0, 12)
        m.w16(FILEINFO + 2, 3)
        m.w32(TRACK + 0x08, rate)
        m.w32(TRACK + 0x0C, 1411)
        m.w32(TRACK + 0x10, channels)
        m.w32(TRACK + 0x1C, 0)          # play mode: sequential
        m.w32(TRACK + 0x9C, bits)
        self.rate, self.bits, self.channels = rate, bits, channels
        self.fs = []                    # (op, at_ms)
        self.i2c = 0                    # completed I2C transfers
        self.dma = []                   # (ch, src, dst, len, at_ms)
        m.stubs[DIR_STEP] = self._fs('step', 1)
        m.stubs[FOPEN] = self._fs('open', 0)
        m.stubs[FCLOSE] = self._fs('close', 0)
        m.stubs[DMA_START] = self._dma
        m.reply_ms = self.dec.reply_ms
        m.on_send = self._on_send
        # I2C transfer-done byte the controller's ISR sets (DAC register
        # writes during track A's cold start); polled at 0x03060676.
        for poll in I2C_POLLS:
            m.u.hook_add(UC_HOOK_CODE, self._i2c_done, begin=poll, end=poll)

    def _i2c_done(self, uc, addr, size, _):
        base = uc.reg_read(UC_ARM_REG_R10)
        flag = base + uc.reg_read(UC_ARM_REG_R4)
        if not self.m.r8(flag):
            # a DAC register write on the wire: start, address, 2-3 bytes,
            # stop at 400 kHz is about 0.11 ms
            self.m.charge_ms(self.dec.i2c_ms)
            self.i2c += 1
        self.m.w8(flag, 1)

    def _fs(self, op, ret):
        def stub(m):
            self.fs.append((op, round(m.ms, 3)))
            m.charge_ms(self.dec.fs_ms.get(op, 0))
            return ret
        return stub

    def _dma(self, m):
        u = m.u
        sp = u.reg_read(UC_ARM_REG_SP)
        args = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                        UC_ARM_REG_R2, UC_ARM_REG_R3)]
        self.dma.append(tuple(args) + (round(m.ms, 3),))
        cb = m.r32(sp + 4)
        if args[2] != I2S_TX and cb:
            # memory-to-memory copy (decoder output into a PCM buffer):
            # complete it at once and enter the completion callback, which
            # returns straight to the caller
            u.reg_write(UC_ARM_REG_R0, args[0])
            u.reg_write(UC_ARM_REG_PC, cb)
            return 'jumped'
        return 0

    def _on_send(self, value, channel, slot):
        """Mailbox writes to core 1: answer with decoder-side state."""
        m = self.m
        if value == 0x65:               # open next file: report its info
            # read back through glue ops 6, 3, 0x11, 4, 5 respectively
            m.w32(DEC_OUT + 0x04, 180_000)          # duration, ms
            m.w32(DEC_OUT + 0x08, 1411)             # bitrate, kbit/s
            m.w32(DEC_OUT + 0x0C, self.bits)
            m.w32(DEC_OUT + 0x10, self.rate)
            m.w32(DEC_OUT + 0x14, self.channels)
        elif value == 4:                # decode one output frame
            m.charge_ms(0)              # core 1 works in parallel
            m.w32(DEC_OUT + 0x20, 1152)
            m.w32(DEC_OUT + 0x24, 1)
            m.w32(DEC_OUT + 0x28, 0)

    def set_next_file(self, ext=None):
        self.m.u.mem_write(FILEINFO + 0x1C, ext or self.ext)

    def start_first(self):
        """Track A: the stock start path (load-start) brings up the codec,
        its glue module and the decoder, as on a cold play."""
        self.set_next_file()
        self.m.call(LOAD_START)
        self.clear()

    def run(self, limit=40_000_000):
        """Natural end of track: the playback task's 0xEC handler."""
        self.set_next_file()
        self.m.call(ADVANCE, 0, limit=limit)
        return self

    def skip(self, limit=40_000_000):
        """User NEXT: the codec dispatcher's 0x106 message, step +1."""
        self.set_next_file()
        self.m.call(DISPATCH, 0x106, 1, limit=limit)
        return self

    def first_audio_ms(self):
        """When the I2S DMA restarts, or None if it never does."""
        for ch, src, dst, n, t in self.dma:
            if dst == I2S_TX:
                return t
        return None

    def clear(self):
        self.i2c = 0
        self.m.reset_log()
        self.fs.clear()
        self.dma.clear()


class Decoder:
    """Latencies of the decoder core and storage, in milliseconds. These
    are inputs, not measurements: the rig reports how many times the
    system side waits on each, so their cost can be read off for any
    value."""
    def __init__(self, reply=0.05, fs=None, i2c=0.11):
        self.reply = reply
        self.fs_ms = fs or {}
        self.i2c_ms = i2c

    def reply_ms(self, caller, word):
        return self.reply
