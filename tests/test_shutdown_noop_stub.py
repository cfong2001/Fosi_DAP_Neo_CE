"""Shutdown and software reset keep their no-op call at 0x03060D8E.

Stock module 0 calls the `bx lr` stub at 0x03060D8E from the shutdown
routine (0x03067CD8, before the power-hold GPIO is released) and from the
software reset (0x030536C4). A patch that turns that stub into code makes
shutdown return through a stale stack word instead of powering off. These
tests pin the stub in every release image and run the shutdown tail under
emulation until it reaches the power-hold call.
"""
import struct
import sys
import unittest
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_SP

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image  # noqa: E402

STUB = 0x03060D8E
CALLERS = (0x030536C4, 0x03067CD8)   # software reset, shutdown
POWER_HOLD = 0x030613BE              # power-hold GPIO2.6 write, called with 0
STALE = 0x0BADC0DE                   # caller-frame filler a bad return would load
IMAGES = ('DP3_V137.img', 'release/DP3_V137_CE.img', 'release/DP3_V137_CE_minimal.img',
          'release/DP3_V137_CE_recovery.img')


def module0(raw):
    image = Image(raw)
    offset, size = image.module_region(0, 'code')
    return raw[offset:offset + size], image.modules[0]['code_exec']


def run_shutdown_tail(raw):
    code, base = module0(raw)
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    cpu.mem_map(0x03000000, 0x100000)
    cpu.mem_write(base, code)
    # Peripheral and display helpers that shutdown calls after the stub.
    for address in (0x0306043A, 0x03061280, 0x0306123A, 0x03067894, 0x03064944):
        cpu.mem_write(address, b'\x70\x47')
    sp = 0x03040000
    # Shutdown keeps an 8-byte frame; above it sits the power-off handler's
    # 0x20-byte local area. Fill it so a wrong epilogue returns to STALE.
    cpu.mem_write(sp + 8, struct.pack('<8I', *([STALE] * 8)) + bytes(8))
    cpu.reg_write(UC_ARM_REG_SP, sp)
    cpu.reg_write(UC_ARM_REG_R0, 0)
    cpu.reg_write(UC_ARM_REG_R4, 0x18)
    cpu.reg_write(UC_ARM_REG_R5, 0x03020000)
    reached = []

    def hook(machine, address, size, data):
        if address == POWER_HOLD:
            reached.append(machine.reg_read(UC_ARM_REG_R0))
            machine.emu_stop()

    cpu.hook_add(UC_HOOK_CODE, hook)
    try:
        cpu.emu_start(0x03067CD8 | 1, 0x03067D1A, count=5000)
    except UcError:
        return None, cpu.reg_read(UC_ARM_REG_PC)
    return (reached[0] if reached else None), cpu.reg_read(UC_ARM_REG_PC)


class ShutdownNoopStub(unittest.TestCase):
    def test_stock_calls_the_stub_from_shutdown_and_reset(self):
        code, base = module0((ROOT / 'DP3_V137.img').read_bytes())
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for caller in CALLERS:
            insn = next(md.disasm(code[caller - base:caller - base + 4], caller))
            self.assertEqual((insn.mnemonic, insn.op_str), ('bl', f'#{STUB:#x}'))

    def test_every_image_keeps_the_stub_and_its_callers(self):
        for name in IMAGES:
            with self.subTest(image=name):
                code, base = module0((ROOT / name).read_bytes())
                self.assertEqual(code[STUB - base:STUB + 2 - base], b'\x70\x47')
                for caller in CALLERS:
                    stock, _ = module0((ROOT / 'DP3_V137.img').read_bytes())
                    self.assertEqual(code[caller - base:caller + 4 - base],
                                     stock[caller - base:caller + 4 - base])

    def test_shutdown_reaches_power_hold_release(self):
        for name in IMAGES:
            with self.subTest(image=name):
                value, pc = run_shutdown_tail((ROOT / name).read_bytes())
                self.assertEqual(value, 0, f'shutdown left the path at pc={pc:#x}')

    def test_old_trampoline_placement_is_caught(self):
        raw = bytearray((ROOT / 'DP3_V137.img').read_bytes())
        image = Image(bytes(raw))
        offset, _ = image.module_region(0, 'code')
        base = image.modules[0]['code_exec']
        raw[offset + STUB - base:offset + STUB - base + 4] = bytes.fromhex('6870c4e7')
        value, pc = run_shutdown_tail(bytes(raw))
        self.assertIsNone(value)
        self.assertEqual(pc, STALE)


if __name__ == '__main__':
    unittest.main()
