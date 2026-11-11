"""Unicorn machine for the system core's natural track advance.

Loads modules 0 (kernel), 27 (now-playing UI) and 33 (media player) from
an image at their exec addresses, maps the peripheral windows as RAM and
runs real firmware code with a virtual clock. delay_ms (0x03064944) and
delay_us (0x03064920) are busy-waits in the firmware; the machine skips
the spin and charges their argument to the clock instead. Everything else
is charged per executed instruction at the system core's clock.
"""
import struct
import sys
from pathlib import Path

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE,
                     UC_HOOK_MEM_UNMAPPED, UC_HOOK_MEM_WRITE, UC_HOOK_BLOCK,
                     UC_HOOK_MEM_READ)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R10, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

DELAY_MS, DELAY_US = 0x03064944, 0x03064920
STACK_TOP, RET = 0x030F0000, 0x030FFF00
MODULES = (0, 27, 33)
LOADER = 0x03067870         # load_module(index, flags): storage -> exec
MU_KICK = 0x030611E0        # per-iteration kick in every core-1 wait
MU_SEND = 0x0306D0D8        # mailbox write (value, channel, slot)
PRINTF = 0x0306D8F0         # debug printf to the UART
CRU_GATE, CRU_RESET = 0x40180080, 0x401800CC
CORE1_BIT = 1 << 2
WFI = 0x03055B70            # wfi; bx lr
SET_ISR = 0x030664E8        # set_isr(irq, handler) into the RAM vectors
NVIC_LEAVES = (0x03056C44, 0x03056C88, 0x03056CE4, 0x03056D40, 0x03056D8E,
               0x03056DCE, 0x03056DD6)


class Machine:
    def __init__(self, raw, modules=MODULES, cpu_hz=None):
        self.im = Image(raw)
        self.raw = raw
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        # Runtime-installed function pointers (the file API table near
        # 0x03004450, driver hooks) are zero in a cold image. Page 0 is
        # mapped and the code hook returns from any call into it at once,
        # recording it in null_calls.
        u.mem_map(0x00000000, 0x1000)
        u.mem_map(0x01000000, 0x100000)      # core-1 window
        u.mem_map(0x03000000, 0x100000)      # system SRAM
        for base in (0x40000000, 0x50000000, 0x60000000):
            u.mem_map(base, 0x1000000)       # peripherals as RAM
        u.mem_map(0xE000E000, 0x1000)
        for idx in modules:
            m = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, size = self.im.module_region(idx, kind)
                if size:
                    u.mem_write(m[f'{kind}_exec'], raw[off:off + size])
        self.u = u
        self.cpu_hz = cpu_hz or self.r32(0x030064E0 + 0x18) or 120_000_000
        self.ns = 0                 # virtual clock, nanoseconds
        self.insns = 0
        self.delays = []            # (caller, kind, amount)
        self.stubs = {}             # addr -> fn(machine) returning r0 or None
        self.watch = {}             # addr -> label, logged when executed
        self.trace = []
        self.null_calls = []
        self.prints = []
        self.unmapped = []
        self.loads = []             # (module, flags, bytes, at_ms)
        self.flash_bps = 8_000_000  # module-load read rate (assumed)
        self.stubs[LOADER] = Machine._load_module
        # Decoder-core model. Every core-1 round trip in this firmware is
        # the same idiom: zero a reply word, write the mailbox, then spin
        # {kick 0x030611E0; yield 0x030531F6; delay_us(1)} until the
        # mailbox interrupt sets the word. The polled word is the last
        # SRAM word the loop read before the kick. The model answers each
        # wait after reply_ms(caller, word).
        self._last_read = None
        # Peripheral status bits that real hardware raises promptly (PLL
        # lock and the like): reads of these words see the mask set.
        self.ready_bits = {0x40180004: 0x400}   # CRU PLL lock
        # ... and self-clearing control bits (I2S controller soft reset)
        self.clear_bits = {0x40020020: 0xFFFFFFFF, 0x40030020: 0xFFFFFFFF}
        u.hook_add(UC_HOOK_MEM_READ, self._periph_read, begin=0x40000000,
                   end=0x60FFFFFF)
        u.hook_add(UC_HOOK_MEM_READ, self._read, begin=0x03000000,
                   end=0x030FFFFF)
        self.waits = []             # [caller, word, start_ms, end_ms]
        self._open_wait = None
        self.reply_ms = lambda caller, word: 0.05
        self.sent = []              # mailbox writes (value, channel, slot)
        self.stubs[MU_KICK] = Machine._mu_kick
        # Core-1 power state from the CRU. Writes use the Rockchip
        # write-mask form (high half = enable). Soft reset 0x32 is bit 2
        # of 0x401800CC; clock gate 2 is bit 2 of 0x40180080 (1 = gated).
        # A held or gated core answers nothing: a wait on it runs to its
        # cap, which the kick stub charges in one step.
        self.cru = {CRU_RESET: 0, CRU_GATE: 0}
        self.core1_log = []
        u.hook_add(UC_HOOK_MEM_WRITE, self._cru_write, begin=CRU_GATE,
                   end=CRU_RESET + 3)
        # Unicorn's Cortex-M model gives the NVIC/SCB page real exception
        # semantics, which derails plain firmware writes there. The leaf
        # helpers that touch it are stubbed; ISR registration is applied
        # to the RAM vector table directly and recorded.
        for a in NVIC_LEAVES:
            self.stubs[a] = lambda m: 0
        self.stubs[WFI] = lambda m: None    # wait-for-interrupt: no sleep
        self.isrs = []
        self.stubs[SET_ISR] = Machine._set_isr
        self.on_send = None
        u.hook_add(UC_HOOK_CODE, self._code)
        u.hook_add(UC_HOOK_MEM_UNMAPPED, self._unmapped)

    def reset_log(self):
        self.ns = self.insns = 0
        for lst in (self.delays, self.waits, self.sent, self.loads,
                    self.null_calls, self.prints, self.isrs, self.trace,
                    self.core1_log):
            lst.clear()
        self._open_wait = None

    # -- memory helpers
    def r32(self, a):
        return struct.unpack('<I', self.u.mem_read(a, 4))[0]

    def r16(self, a):
        return struct.unpack('<H', self.u.mem_read(a, 2))[0]

    def r8(self, a):
        return self.u.mem_read(a, 1)[0]

    def w32(self, a, v):
        self.u.mem_write(a, struct.pack('<I', v & 0xFFFFFFFF))

    def w16(self, a, v):
        self.u.mem_write(a, struct.pack('<H', v & 0xFFFF))

    def w8(self, a, v):
        self.u.mem_write(a, bytes([v & 0xFF]))

    @property
    def ms(self):
        return self.ns / 1e6

    def charge_ms(self, ms):
        self.ns += int(ms * 1e6)

    def _load_module(self):
        idx = self.u.reg_read(UC_ARM_REG_R0)
        flags = self.u.reg_read(UC_ARM_REG_R1)
        m = self.im.modules[idx]
        n = 0
        for kind in ('code', 'data'):
            off, size = self.im.module_region(idx, kind)
            if size and flags & (1 if kind == 'code' else 2):
                self.u.mem_write(m[f'{kind}_exec'], self.raw[off:off + size])
                n += size
        if flags & 4 and m.get('bss_len'):
            self.u.mem_write(m['bss_exec'], bytes(m['bss_len']))
        self.loads.append((idx, flags, n, round(self.ms, 3)))
        self.ns += int(n * 1e9 / self.flash_bps)
        return 0

    def _set_isr(self):
        irq = self.u.reg_read(UC_ARM_REG_R0)
        fn = self.u.reg_read(UC_ARM_REG_R1)
        self.w32(0x03004000 + 4 * irq, fn)
        self.isrs.append((irq, fn, round(self.ms, 3)))
        return 0

    def _cru_write(self, uc, access, addr, size, value, _):
        if addr not in self.cru:
            return
        mask = (value >> 16) & 0xFFFF
        old = self.cru[addr]
        self.cru[addr] = (old & ~mask) | (value & mask)
        if mask & CORE1_BIT:
            self.core1_log.append((
                'reset' if addr == CRU_RESET else 'gate',
                bool(self.cru[addr] & CORE1_BIT), round(self.ms, 3)))

    @property
    def core1_running(self):
        return not (self.cru[CRU_RESET] & CORE1_BIT or
                    self.cru[CRU_GATE] & CORE1_BIT)

    def _mu_kick(self):
        u = self.u
        caller = (u.reg_read(UC_ARM_REG_LR) & ~1) - 4
        word = self._last_read
        if word is None or self.r32(word) != 0:
            return 0
        w = self._open_wait
        if w is None or w[0] != caller or w[1] != word:
            w = [caller, word, self.ms, None]
            self.waits.append(w)
            self._open_wait = w
        if not self.core1_running:
            # nobody will answer: the loop runs out its counter (r4 in
            # every wait idiom here) at ~1.1 us per iteration
            left = u.reg_read(UC_ARM_REG_R4)
            self.ns += int(left * 1100)
            u.reg_write(UC_ARM_REG_R4, 1)
            w[3] = 'timeout'
            self._open_wait = None
            return 0
        if self.ms - w[2] >= self.reply_ms(caller, word):
            self.w32(word, 1)
            w[3] = self.ms
            self._open_wait = None
        return 0

    # -- hooks
    def _ret(self, r0=None):
        if r0 is not None:
            self.u.reg_write(UC_ARM_REG_R0, r0 & 0xFFFFFFFF)
        self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def _code(self, uc, addr, size, _):
        self.insns += 1
        self.ns += int(1e9 / self.cpu_hz)
        if addr < 0x1000:
            self.null_calls.append(((uc.reg_read(UC_ARM_REG_LR) & ~1) - 2,
                                    round(self.ms, 3)))
            self._ret()
            return
        if addr in self.watch:
            self.trace.append((round(self.ms, 3), self.watch[addr]))
        if addr == DELAY_MS or addr == DELAY_US:
            n = uc.reg_read(UC_ARM_REG_R0)
            kind = 'ms' if addr == DELAY_MS else 'us'
            self.delays.append((uc.reg_read(UC_ARM_REG_LR) - 4 | 0, kind, n,
                                round(self.ms, 3)))
            self.charge_ms(n if kind == 'ms' else n / 1000)
            self._ret()
        elif addr == PRINTF:
            fmt = bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R0), 80))
            self.prints.append((fmt.split(b'\0')[0].decode('latin1'),
                                round(self.ms, 3)))
        elif addr == MU_SEND:
            v = tuple(uc.reg_read(r) for r in (
                UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            self.sent.append(v + (round(self.ms, 3),))
            if self.on_send:
                self.on_send(*v)
        elif addr in self.stubs:
            r = self.stubs[addr](self)
            if r != 'jumped':
                self._ret(r)

    def _read(self, uc, access, addr, size, value, _):
        if size == 4:
            self._last_read = addr

    def _periph_read(self, uc, access, addr, size, value, _):
        a = addr & ~3
        if a in self.ready_bits:
            self.w32(a, self.r32(a) | self.ready_bits[a])
        if a in self.clear_bits:
            self.w32(a, self.r32(a) & ~self.clear_bits[a])

    def _unmapped(self, uc, access, addr, size, value, _):
        self.unmapped.append((hex(uc.reg_read(UC_ARM_REG_PC)), hex(addr)))
        return False

    def call(self, fn, *args, limit=50_000_000):
        u = self.u
        for reg, v in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                           UC_ARM_REG_R3), args):
            u.reg_write(reg, v)
        u.reg_write(UC_ARM_REG_SP, STACK_TOP)
        u.reg_write(UC_ARM_REG_LR, RET | 1)
        u.emu_start(fn | 1, RET, count=limit)
        return u.reg_read(UC_ARM_REG_R0)
