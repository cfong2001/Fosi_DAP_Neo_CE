"""Make a separate CE diagnostic image with a live format-error readout.

Explicit opt-in; the input and normal release image are never modified.
The readout is: CE: resident-extension browser-extension browser-kind codec
open-marker extension-first-byte. The last four fields are hex bytes. Browser fields describe
the last activated browser node, not necessarily the current library item.
Only three extension bytes and one class byte are captured. No filename,
path, media contents, serial number or host identifier is collected.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'patches/full/build'),
               str(ROOT / 'patches/framework/tools')]
from rknano_image import Image, rk_crc32
from validate_grown import validate_grown
from build_tail import branch
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

ENTRY, HELPERS, CAPTURE = 0x0306D304, 0x030643C8, 0x03061638
TRACE = 0x03023490  # SAVEINFO +0x1F0, after theater and 12-byte focus state
RESOURCE, PROFILE, NODE_SITE = 0x030630C2, 0x0305168C, 0x0307DF06
STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'


def assemble():
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    def asm(source, address):
        return bytes(ks.asm(source, address)[0])
    copy = asm('push {lr};movs r6,#3;again:ldrb r0,[r5],#1;'
               'strh r0,[r4],#2;subs r6,#1;bne again;movs r0,#32;'
               'strh r0,[r4],#2;pop {pc}', HELPERS)
    hexbase = HELPERS + len(copy)
    hexcode = asm('push {lr};ldrb r6,[r5];lsrs r0,r6,#4;bl nibble;'
                  'and r0,r6,#15;bl nibble;movs r0,#32;strh r0,[r4],#2;'
                  'pop {pc};nibble:cmp r0,#10;ite lo;addlo r0,#48;'
                  'addhs r0,#55;strh r0,[r4],#2;bx lr', hexbase)
    prefix = ';'.join(f'movs r0,#{c};strh r0,[r4],#2' for c in b'CE:')
    entry = asm(f'''cmp r0,#60;bne pass;cmp r2,#32;blo pass;
        push {{r4,r5,r6,lr}};mov r4,r1;{prefix};
        ldr r5,=0x030056f2;bl {HELPERS};
        ldr r5,={TRACE};bl {HELPERS};
        ldr r5,={TRACE+3};bl {hexbase};
        ldr r5,=0x0304b4d4;bl {hexbase};
        ldr r5,=0x03023151;bl {hexbase};
        ldr r5,={TRACE};bl {hexbase};
        movs r0,#0;strh r0,[r4];pop {{r4,r5,r6,pc}};
        pass:b.w {PROFILE};.ltorg''', ENTRY)
    capture = asm(f'''push {{r0,r1,r2,lr}};
        ldrb r5,[r4,#0x4e];ldr r0,={TRACE};
        cmp r5,#0;bne file;
        movw r1,#0x2d2d;strh r1,[r0];movs r1,#45;strb r1,[r0,#2];b done;
    file:
        ldrb r1,[r4,#0x57];strb r1,[r0];
        ldrb r1,[r4,#0x58];strb r1,[r0,#1];
        ldrb r1,[r4,#0x59];strb r1,[r0,#2];
    done:
        strb r5,[r0,#3];
        pop.w {{r0,r1,r2,lr}};b.w {NODE_SITE+4};.ltorg''', CAPTURE)
    helpers = copy + hexcode
    assert len(entry) <= 106 and len(helpers) <= 78 and len(capture) <= 72
    return entry, helpers, capture


def build(raw, stock):
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('stock reference hash mismatch')
    validate_grown(raw)
    image, original = Image(raw), Image(stock)
    result = bytearray(raw)
    def location(im, module, address, size):
        offset, length = im.module_region(module, 'code')
        relative = address - im.modules[module]['code_exec']
        if relative < 0 or relative + size > length:
            raise ValueError('diagnostic patch outside code segment')
        return offset + relative
    entry, helpers, capture = assemble()
    edits = [(0, ENTRY, entry), (0, HELPERS, helpers), (0, CAPTURE, capture),
             (0, RESOURCE, branch(RESOURCE, ENTRY)),
             (31, NODE_SITE, branch(NODE_SITE, CAPTURE))]
    for module, address, code in edits:
        at = location(image, module, address, len(code))
        before = location(original, module, address, len(code))
        expected = branch(RESOURCE, PROFILE) if address == RESOURCE else stock[before:before + len(code)]
        if raw[at:at + len(code)] != expected:
            raise ValueError(f'occupied or unexpected diagnostic site: module {module} {address:#x}')
        result[at:at + len(code)] = code
    struct.pack_into('<I', result, len(result) - 4, rk_crc32(result[:-4]))
    validate_grown(result)
    report = {'input_sha256': hashlib.sha256(raw).hexdigest(),
              'output_sha256': hashlib.sha256(result).hexdigest(),
              'browser_capture_bytes': 4,
              'fields': ['resident browser extension', 'last browser node extension',
                         'last browser node kind (hex)', 'codec id (hex)',
                         'per-open marker (hex; semantics not established)',
                         'browser extension first byte (hex; distinguishes case)'],
              'normal_resource_lookup': 'preserved; short buffers use original error text',
              'limitations': 'Live state evidence only; no playback or repair claim.'}
    return bytes(result), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'release/DP3_V137_CE.img')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report_path = Path(str(args.output) + '.diagnostics.json')
    for target in (args.output, report_path):
        if target.resolve() == args.input.resolve() or target.exists() or target.is_symlink():
            parser.error('output/report already exists or aliases the input')
    data, report = build(args.input.read_bytes(), (ROOT / 'DP3_V137.img').read_bytes())
    with args.output.open('xb') as output:
        output.write(data)
    with report_path.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2)
        output.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
