"""Load actual firmware code for focused boot routine emulation."""
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_SP

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rknano_image import Image

STOP = 0x03008000
STOCK = ROOT / 'DP3_V137.img'


def word(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def machine(raw, module):
    image = Image(raw)
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    cpu.mem_map(0x03000000, 0x100000)
    for number in (0, module):
        for segment in ('code', 'data'):
            offset, size = image.module_region(number, segment)
            if size:
                address = image.modules[number][segment + '_exec']
                cpu.mem_write(address, raw[offset:offset + size])
    return cpu


def run(cpu, start, stop=STOP, count=500_000):
    cpu.reg_write(UC_ARM_REG_SP, 0x03010000)
    cpu.reg_write(UC_ARM_REG_LR, STOP | 1)
    cpu.emu_start(start | 1, stop, count=count)


def stub(cpu, handlers):
    for address in handlers:
        cpu.mem_write(address, b'\x70\x47')  # bx lr

    def intercept(cpu, address, size, data):
        if address in handlers:
            result = handlers[address](cpu)
            if result is not None:
                cpu.reg_write(UC_ARM_REG_R0, result & 0xFFFFFFFF)

    cpu.hook_add(UC_HOOK_CODE, intercept)
