"""Now Playing under Unicorn, one 10 ms tick at a time.

Real code from the image under test: module 0 (with the CE tail), module 18
and module 27. Each tick advances the OS clock and the elapsed time, then runs
the player's Service handler, its Display handler and the framebuffer flush
(0x0306448A), in the order the window loop calls them.

Modelled leaves, and only these:
- MDRead (0x030678CA) serves sectors of the image file, which is the system
  disk (the boot code reads font and resource offsets from its header at
  sector 0). The block reader 0x03067510 above it runs for real, so its
  calls and the sector reads it issues are both counted.
- The interrupt mask pair (0x0306660A, 0x03066662) returns.
- The LCD driver's row transfer (driver record 0x0306F1E8, slot 0x14) records
  the rows the flush pushes.
- The artwork request 0x0307E8A4 returns at once (it needs a mounted card).
"""
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

END = 0x030EF000
STACK = 0x030F0000
READER, MDREAD, ISR_OFF, ISR_ON = 0x03067510, 0x030678CA, 0x0306660A, 0x03066662
LCD_DRIVER, LCD_ROWS = 0x0306F1E8, 0x030E8100
SERVICE, DISPLAY, FLUSH = 0x0307DFDA, 0x0307EF4E, 0x0306448A
ART_REQUEST = 0x0307E8A4
EVENTS, CLOCK = 0x03023CF8, 0x03023298
SAVEINFO, TEXT, DCTX = 0x030232A0, 0x0302385C, 0x030238B8
TOP, LOWER = 0x030065A8, 0x0306F224
PLAY_STATE, STATE_A, STATE_B = 0x03023924, 0x0302314A, 0x0302314B
TIME_PTR, TIME = 0x0304AD78, 0x0304C100
TITLE, ARTIST = 0x0304AF24 + 0x60, 0x0304AF24 + 0x15E
GROUND = 0x03004400
FOCUS = 0x03023484


class Machine:
    def __init__(self, raw):
        self.raw = raw
        self.im = Image(raw)
        u = self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x03000000, 0x500000)
        u.mem_map(0x01000000, 0x200000)
        u.mem_map(0xE000E000, 0x1000)
        for idx in (0, 18, 27):
            self.load(idx)
        self.reads = self.sectors = self.instructions = 0
        self.rows = []
        self.counting = True
        u.hook_add(UC_HOOK_CODE, self._hook)
        u.hook_add(UC_HOOK_CODE, self._count)
        self.boot()

    # ------------------------------------------------------------ memory
    def load(self, idx):
        m = self.im.modules[idx]
        for kind in ('code', 'data'):
            off, size = self.im.module_region(idx, kind)
            if size:
                self.u.mem_write(m[kind + '_exec'], self.raw[off:off + size])

    def w8(self, a, v): self.u.mem_write(a, bytes([v]))
    def w16(self, a, v): self.u.mem_write(a, struct.pack('<H', v))
    def w32(self, a, v): self.u.mem_write(a, struct.pack('<I', v))
    def r8(self, a): return self.u.mem_read(a, 1)[0]
    def r16(self, a): return struct.unpack('<H', self.u.mem_read(a, 2))[0]
    def r32(self, a): return struct.unpack('<I', self.u.mem_read(a, 4))[0]

    def post(self, n):
        a = EVENTS + n // 32 * 4
        self.w32(a, self.r32(a) | 1 << n % 32)

    def pending(self, n):
        return bool(self.r32(EVENTS + n // 32 * 4) >> n % 32 & 1)

    def screen(self):
        """Both framebuffer surfaces of the displayed bank and the display context."""
        bank = self.r16(DCTX)
        return (bytes(self.u.mem_read(TOP + bank * 115200, 115200))
                + bytes(self.u.mem_read(LOWER + bank * 38400, 38400)),
                bytes(self.u.mem_read(DCTX, 40)))

    # ------------------------------------------------------------- leaves
    def _ret(self, value=None):
        if value is not None:
            self.u.reg_write(UC_ARM_REG_R0, value & 0xFFFFFFFF)
        self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def _count(self, uc, addr, size, _):
        self.instructions += 1

    def _hook(self, uc, addr, size, _):
        if addr == READER:
            self.reads += 1
        elif addr in (ISR_OFF, ISR_ON):
            self._ret(0)
        elif addr == MDREAD:
            dev, sector, count, dst = (uc.reg_read(r) for r in
                                       (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            assert dev == 0x30000, f'unexpected device {dev:#x}'
            self.sectors += count
            uc.mem_write(dst, self.raw[sector * 512:(sector + count) * 512].ljust(count * 512, b'\0'))
            self._ret(0)
        elif addr == LCD_ROWS:
            self.rows.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R3)))
            self._ret(0)
        elif addr == ART_REQUEST:
            self._ret(0)

    def call(self, addr, *args):
        u = self.u
        for reg, v in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            u.reg_write(reg, v)
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, END | 1)
        u.emu_start(addr | 1, END, count=100_000_000)
        assert u.reg_read(UC_ARM_REG_PC) == END, f'{addr:#x} stopped at {u.reg_read(UC_ARM_REG_PC):#x}'
        assert u.reg_read(UC_ARM_REG_SP) == STACK
        return u.reg_read(UC_ARM_REG_R0)

    # --------------------------------------------------------------- state
    def boot(self):
        """The cells boot fills from the image header, and the text context."""
        hdr = lambda o: struct.unpack_from('<I', self.raw, o)[0]
        self.w32(0x03023270, hdr(0x78))          # font A
        self.w32(0x03023274, hdr(0x80))          # font B
        self.w32(0x03023280, hdr(0x78))          # selected font
        self.w32(0x0302328C, hdr(0x14C))         # image resources (dark set)
        self.w32(LCD_DRIVER + 0x14, LCD_ROWS | 1)
        self.w16(LCD_ROWS, 0x4770)
        for off, v in ((0, 0), (2, 0xFFFF), (4, 0), (0xC, 0), (0xE, 0), (0x10, 239),
                       (0x12, 319), (0x14, 0), (0x16, 0), (0x18, 0), (0x1A, 0), (0x1C, 0),
                       (0x1E, 239), (0x22, 0)):
            self.w16(TEXT + off, v)
        self.call(0x03063186, 0)                 # portrait display window
        self.w16(DCTX + 4, 0x140)
        self.w16(DCTX + 6, 0)
        bank = self.r16(DCTX)
        self.u.mem_write(TOP + bank * 115200, b'\x5a\xa5' * 57600)
        self.u.mem_write(LOWER + bank * 38400, b'\x5a\xa5' * 19200)

    def player(self, title='Short Title', artist='Artist Name', total_ms=245_000,
               elapsed_ms=61_000, play_state=0, light=False):
        self.w8(SAVEINFO + 0x1A, 0)              # artwork view
        self.w8(SAVEINFO + 0x61, 0)              # play mode
        self.w8(SAVEINFO + 0x2D8, 1 if light else 0)
        self.w8(STATE_A, 0)
        self.w8(STATE_B, 0)
        self.w16(PLAY_STATE, play_state)
        self.w32(0x03023980 + 0x44, 0)
        self.w32(TIME_PTR, TIME)
        self.u.mem_write(TIME, struct.pack('<II', total_ms, elapsed_ms) + bytes(0x38))
        self.u.mem_write(TITLE, title.encode('utf-16-le') + b'\0\0')
        self.u.mem_write(ARTIST, artist.encode('utf-16-le') + b'\0\0')
        self.w32(CLOCK, 10_000)
        self.wake()

    def wake(self):
        """What the focus reset stub does at Init: stamp activity, controls shown."""
        self.w32(FOCUS, self.r32(CLOCK))
        self.w32(FOCUS + 4, self.r32(0x0302317C))
        self.w8(FOCUS + 8, 0)
        self.post(0x39)

    def elapsed(self):
        return self.r32(TIME + 4)

    def tick(self, playing=True):
        """One 10 ms tick: clock and elapsed advance, Service, Display, flush."""
        self.w32(CLOCK, self.r32(CLOCK) + 1)
        if playing:
            self.w32(TIME + 4, self.r32(TIME + 4) + 10)
        self.call(SERVICE)
        self.call(DISPLAY)
        self.call(FLUSH)

    def measure(self, ticks, **kw):
        """Run `ticks` ticks; return the work they did."""
        i, r, s, n = self.instructions, self.reads, self.sectors, len(self.rows)
        for _ in range(ticks):
            self.tick(**kw)
        rows = sum(b - a + 1 for a, b in self.rows[n:])
        return dict(instructions=self.instructions - i, reads=self.reads - r,
                    sectors=self.sectors - s, lcd_rows=rows)
