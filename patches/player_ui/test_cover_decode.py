"""Cover decode work on track select, against the images before each change.

Runs the real player art request (module 27 0x0307E8A4: open, picture
extraction, module 18 setup, module 19 decode and scaler, CE row compositor
and theater sampling), the theater repaint it posts, and the second request.
File, overlay-loader and LCD-bitmap leaves are modeled; the bitmap model
keeps every row. Reported numbers are emulated instructions, not time.
"""
import base64
import hashlib
import io
import json
import random
import runpy
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'tools'), str(ROOT / 'patches/full/build')]
from rknano_image import Image
from build_tail import branch
from build_artwork_scaler import payloads
from repair_metrics import ogg
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_BLOCK
from unicorn.arm_const import *

THEATER = 0x0307C350
EVENTS = 0x03023CFC
REPAINT, ART = 1 << 25, 1 << 27
CELL = 0x03004400
LOAD_ART, PAINTER = 0x0307E8A4, 0x03083B36
LEAVES = (0x3058FA8, 0x30594A0, 0x30545D4, 0x3058E8E, 0x305C86A, 0x305C822, 0x305CA1C, 0x306D8F0,
          0x30611E0, 0x3058CC6, 0x3067870, 0x306333E, 0x30589B6, 0x30670E0, 0x306712C, 0x3067510)
REPAINT_STUBS = (0x030632FA, 0x03052D5C, 0x03063700, 0x0306354A, 0x03063642)
CS = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)


def at(im, module, address):
    offset, _ = im.module_region(module, 'code')
    return offset + address - im.modules[module]['code_exec']


def previous(raw):
    """The image before the integer column coordinates: the patches' expect bytes back."""
    image, out = Image(raw), bytearray(raw)
    for path in sorted(HERE.glob('037?-scaler-*.patch')):
        fields = dict(l.split(': ', 1) for l in path.read_text().splitlines() if ': ' in l)
        pos = at(image, int(fields['module']), int(fields['address'], 16))
        new, old = bytes.fromhex(fields['replace']), bytes.fromhex(fields['expect'])
        assert raw[pos:pos + len(new)] == new, 'candidate lacks ' + path.name
        out[pos:pos + len(old)] = old
    return bytes(out)


def legacy(raw):
    """The image before the cover decode changes: stock scaler bytes and the old theater payload."""
    stock, image, out = (ROOT / 'DP3_V137.img').read_bytes(), Image(raw), bytearray(raw)
    original = Image(stock)
    for module, address, code in payloads():
        pos = at(image, module, address)
        assert raw[pos:pos + len(code)] == code, 'candidate lacks scaler patch'
        before = at(original, module, address)
        out[pos:pos + len(code)] = stock[before:before + len(code)]
    src = runpy.run_path(str(ROOT / 'patches/full/build/theater/build_theater.py'))
    tail = list(src['TRAMP_TAIL_ASM'])
    cut = tail.index('abort_decode:')
    del tail[cut:cut + len(src['ABORT_ASM'])]
    reset, _ = src['assemble'](src['RESET_ASM'], THEATER)
    body = reset + branch(THEATER + len(reset), 0x030838A2)
    entry = THEATER + len(body)
    head, _ = src['assemble'](src['TRAMP_HEAD_ASM'], entry)
    rest, _ = src['assemble'](tail, entry + len(head) + 4)
    old = (body + head + branch(entry + len(head), src['BITMAP'], True) + rest).ljust(680, b'\0')
    assert hashlib.sha256(old).hexdigest() == 'cc8ac25ec178cc5e9ed41ed1c067e3649a9a55e15d6181f717f84d20925763af'
    pos = at(image, 0, THEATER)
    out[pos:pos + 680] = old
    return bytes(out)


class Machine:
    def __init__(self, raw, media, focus=False, ground=0x10A2):
        im = Image(raw)
        u = self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x03000000, 0x100000)
        u.mem_map(0xE0000000, 0x100000)
        for module in (0, 18, 19, 27):
            for kind in ('code', 'data'):
                offset, size = im.module_region(module, kind)
                u.mem_write(im.modules[module][kind + '_exec'], raw[offset:offset + size])
        u.mem_write(0x0300443C, struct.pack('<II', 0x3058FA9, 0x30594A1))
        u.mem_write(0x03023980 + 0x38, struct.pack('<I', 1))
        u.mem_write(0x03023484 + 8, bytes([focus]))
        u.mem_write(CELL, struct.pack('<H', ground))
        self.files, self.pos, self.rows, self.n, self.sizes = {7: media, 2: b''}, {7: 0, 2: 0}, [], 0, {}
        def block(uc, address, size, _):
            key = (address, size)
            if key not in self.sizes:     # a modeled leaf returns after its first instruction
                self.sizes[key] = 1 if address in LEAVES else len(list(CS.disasm(bytes(uc.mem_read(address, size)), address)))
            self.n += self.sizes[key]
        u.hook_add(UC_HOOK_BLOCK, block)
        def leaf(uc, a, size, _):
            r0, r1, r2, r3 = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            value = 0
            if a == 0x3058CC6:
                self.pos[2], value = 0, 2
            elif a == 0x30589B6:
                self.pos[7], value = 0, 7
            elif a == 0x306333E:
                mode, ptr = struct.unpack('<II', uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 8))
                self.rows.append((r0, r1, bytes(uc.mem_read(ptr, r2 * 2))))
            elif a == 0x3058FA8:
                block = self.files[r2][self.pos[r2]:self.pos[r2] + r1]
                self.pos[r2] += len(block)
                uc.mem_write(r0, block)
                value = len(block)
            elif a == 0x30594A0:
                offset = r0 - (1 << 32) if r0 >> 31 else r0
                self.pos[r2] = offset + (self.pos[r2] if r1 else 0)
                value = self.pos[r2]
            elif a == 0x30545D4:
                value = len(self.files[r0])
            elif a == 0x305C822:
                self.files[2], self.pos[2], value = b'', 0, 2
            elif a == 0x305CA1C:
                self.files[r3] = self.files[r3][:r1] + bytes(uc.mem_read(r0, r2)) + self.files[r3][r1 + r2:]
                value = r2
            elif a == 0x3067870:                  # overlay loader: copy segments, clear BSS
                m = im.modules[r0]
                for kind in ('code', 'data'):
                    offset, size = im.module_region(r0, kind)
                    uc.mem_write(m[kind + '_exec'], raw[offset:offset + size])
                uc.mem_write(m['bss_exec'], bytes(m['bss_len']))
            uc.reg_write(UC_ARM_REG_R0, value)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        for a in LEAVES:
            u.hook_add(UC_HOOK_CODE, leaf, begin=a, end=a)

    def word(self, address):
        return struct.unpack('<I', self.u.mem_read(address, 4))[0]

    def call(self, address):
        u = self.u
        for reg, value in ((UC_ARM_REG_R0, 0), (UC_ARM_REG_SP, 0x030F0000), (UC_ARM_REG_LR, 0x030EF001)):
            u.reg_write(reg, value)
        u.emu_start(address | 1, 0x030EF000, count=400000000)
        assert u.reg_read(UC_ARM_REG_PC) == 0x030EF000
        return u.reg_read(UC_ARM_REG_R0)

    def art(self):
        """The view-0 art request, then any progressive painter rows the player loop would run."""
        self.call(LOAD_ART)
        while self.word(0x0304ADA8) == 0 and self.word(0x0304ADA4) == 1:
            if self.word(EVENTS) & REPAINT or not self.call(PAINTER):
                break

    def repaint(self):
        u, fills = self.u, []
        def stub(uc, a, size, _):
            if a == 0x03052D5C:
                fills.append(struct.unpack('<I', uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 4))[0])
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        hooks = [u.hook_add(UC_HOOK_CODE, stub, begin=a, end=a) for a in REPAINT_STUBS]
        u.reg_write(UC_ARM_REG_SP, 0x030F0000)
        u.emu_start(0x0307EF7B, 0x0307F084, count=2000000)
        for h in hooks:
            u.hook_del(h)
        assert self.word(EVENTS) & ART and fills == [struct.unpack('<H', u.mem_read(CELL, 2))[0]]
        return fills[0]


def select(raw, media, **kw):
    """Select a track: art, then each posted repaint (full fill + art) until it settles."""
    m = Machine(raw, media, **kw)
    m.art()
    work, first, ground = [m.n], len(m.rows), struct.unpack('<H', m.u.mem_read(CELL, 2))[0]
    screen = None
    while m.word(EVENTS) & REPAINT:
        assert len(work) < 4, 'repaint did not settle'
        screen = [m.repaint()] * (240 * 320)
        m.u.mem_write(EVENTS, struct.pack('<I', m.word(EVENTS) & ~ART))   # the art handler's test-and-clear
        m.rows.clear()
        m.n = 0
        m.art()
        work.append(m.n)
    if screen is None:
        screen = [ground] * (240 * 320)
    for x, y, row in m.rows:
        pixels = struct.unpack('<%dH' % (len(row) // 2), row)
        screen[y * 240 + x:y * 240 + x + len(pixels)] = pixels
    return dict(work=work, first_rows=first, rows=len(m.rows),
                ground=struct.unpack('<H', m.u.mem_read(CELL, 2))[0],
                screen=hashlib.sha256(struct.pack('<76800H', *screen)).hexdigest())


def jpeg(width, height, seed):
    from PIL import Image as Picture
    rnd = random.Random(seed)
    img = Picture.new('RGB', (width, height))
    px = img.load()
    a, b = [rnd.randrange(256) for _ in range(3)], [rnd.randrange(256) for _ in range(3)]
    for y in range(height):
        for x in range(width):
            c = a if y < height // 3 else b
            px[x, y] = tuple((v + 3 * x + 5 * y + rnd.randrange(24)) % 256 for v in c)
    out = io.BytesIO()
    img.save(out, 'JPEG', quality=90)
    return out.getvalue()


def opus(width, height, seed):
    data, mime = jpeg(width, height, seed), b'image/jpeg'
    block = struct.pack('>II', 3, len(mime)) + mime + struct.pack('>6I', 0, width, height, 24, 0, len(data)) + data
    comment = b'METADATA_BLOCK_PICTURE=' + base64.b64encode(block)
    tags = b'OpusTags' + struct.pack('<II', 0, 1) + struct.pack('<I', len(comment)) + comment
    return ogg([b'OpusHead' + bytes([1, 2]) + bytes(9), tags])


def conversion_exhaustive(stock):
    """The stock per-channel chain equals v >> 16 for every v in 0..2^24."""
    im = Image(stock)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    offset, size = im.module_region(0, 'code')
    u.mem_write(im.modules[0]['code_exec'], stock[offset:offset + size])
    at = 0x030E0000
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm('''
        loop: mov r0, r4; bl 0x30552ea; mvn r2, #0xf; bl 0x3055288; bl 0x30553c2; bl 0x3055336
        uxtb r0, r0; lsrs r1, r4, #16; uxtb r1, r1; cmp r0, r1; it ne; addne r5, r5, #1
        adds r4, r4, #1; cmp r4, r6; bne loop; done: b done''', at)[0])
    u.mem_write(at, code)
    for reg, value in ((UC_ARM_REG_R4, 0), (UC_ARM_REG_R5, 0), (UC_ARM_REG_R6, (1 << 24) + 1),
                       (UC_ARM_REG_SP, 0x030F0000)):
        u.reg_write(reg, value)
    u.emu_start(at | 1, at + len(code) - 2)
    assert u.reg_read(UC_ARM_REG_R4) == (1 << 24) + 1
    assert u.reg_read(UC_ARM_REG_R5) == 0, 'stock conversion differs from a shift'
    return (1 << 24) + 1


def multiply_equal(stock, raw, samples=20000):
    """The UMULL helper returns the stock helper's r0 for edge and random operands."""
    results = []
    for image in (stock, raw):
        im = Image(image)
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x03000000, 0x100000)
        offset, size = im.module_region(0, 'code')
        u.mem_write(im.modules[0]['code_exec'], image[offset:offset + size])
        rnd, out = random.Random(1), []
        edges = [0, 1, 0xFFFF, 0x10000, 0x10001, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
        pairs = [(a, b) for a in edges for b in edges] + [(rnd.getrandbits(32), rnd.getrandbits(32)) for _ in range(samples)]
        for a, b in pairs:
            for reg, value in ((UC_ARM_REG_R0, a), (UC_ARM_REG_R1, b), (UC_ARM_REG_R4, 0x1234),
                               (UC_ARM_REG_SP, 0x030F0000), (UC_ARM_REG_LR, 0x030EF001)):
                u.reg_write(reg, value)
            u.emu_start(0x0306D8CF, 0x030EF000, count=100)
            assert u.reg_read(UC_ARM_REG_R4) == 0x1234 and u.reg_read(UC_ARM_REG_SP) == 0x030F0000
            out.append(u.reg_read(UC_ARM_REG_R0))
        results.append(out)
    assert results[0] == results[1] == [((a * b) >> 16) & 0xFFFFFFFF for a, b in pairs]
    return len(pairs)


def resident(image, modules=(0, 19)):
    im = Image(image)
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x03000000, 0x100000)
    for module in modules:
        offset, size = im.module_region(module, 'code')
        u.mem_write(im.modules[module]['code_exec'], image[offset:offset + size])
    return u


def run(u, begin, end, **regs):
    for name, value in regs.items():
        u.reg_write(getattr(sys.modules[__name__], 'UC_ARM_REG_' + name.upper()), value)
    u.emu_start(begin | 1, end, count=10000)
    assert u.reg_read(UC_ARM_REG_PC) == end
    return u.reg_read(UC_ARM_REG_R0)


PAINTER_BOXES = (144, 190)       # stock and focus art boxes, square


def coordinates_exhaustive(stock, raw):
    """Every column x < 256 of every scale the painter reaches gets the stock source coordinate.

    The scale is min(fl(box / W), fl(box / H)) = fl(box / max(W, H)), so
    box / n for n up to the 1000 px source limit covers every cover. The stock
    side runs the original per-pixel instructions (0x03087552 and
    0x0308770E: i2f, fdiv, f2iz, ldexp, f2uiz); the new side runs the row
    hook at 0x03087530 once per scale, then the per-pixel bytes at the same
    addresses. Both must give xi in r0 and the 16.16 coordinate A.
    """
    old, new, sp = resident(stock), resident(raw), 0x030F0000 - 0x80
    yq = 0x3FC00000                       # 1.5: the row's y quotient
    checked = 0
    for box in PAINTER_BOXES:
        for n in range(1, 1001):
            a = run(old, 0x030552B6, 0x030EF000, r0=box, sp=sp, lr=0x030EF001)
            b = run(old, 0x030552B6, 0x030EF000, r0=n, sp=sp, lr=0x030EF001)
            scale = run(old, 0x03054FBE, 0x030EF000, r0=a, r1=b, sp=sp, lr=0x030EF001)
            for u in (old, new):
                u.mem_write(sp, struct.pack('<I', 999) * 0x18)
                u.mem_write(sp + 0x40, struct.pack('<II', scale, yq))
            assert run(new, 0x03087530, 0x03087534, r0=yq, sp=sp) == 1
            assert struct.unpack('<I', new.mem_read(sp + 0x44, 4))[0] == yq
            for x in range(256):
                xi = run(old, 0x03087552, 0x03087562, r0=x, fp=x, sp=sp)
                want = (xi, run(old, 0x0308770E, 0x0308771A, sp=sp))
                xi = run(new, 0x03087552, 0x03087562, r0=x, fp=x, sp=sp)
                got = (xi, run(new, 0x0308770E, 0x0308771A, sp=sp))
                assert got == want, (box, n, x, want, got)
                checked += 1
    return checked


CASES = (('square cover, new ground', dict(size=(300, 300), seed=1)),
         ('portrait cover, new ground', dict(size=(240, 360), seed=2)),
         ('small cover upscaled', dict(size=(60, 60), seed=3)),
         ('focus geometry', dict(size=(300, 300), seed=4, focus=True)),
         ('same cover, ground already derived', dict(size=(300, 300), seed=1, settled=True)),
         ('cover over 1000 px, placeholder exit', dict(size=(1100, 64), seed=5)),
         ('square cover, coordinates past 256', dict(size=(280, 280), seed=6)),
         ('wide cover', dict(size=(400, 225), seed=7)))


def check(raw):
    stock = (ROOT / 'DP3_V137.img').read_bytes()
    prior = previous(raw)
    before = legacy(prior)
    report = dict(conversion_values_checked=conversion_exhaustive(stock),
                  multiply_pairs_checked=multiply_equal(stock, raw),
                  columns_checked=coordinates_exhaustive(stock, raw), cases=[])
    for name, case in CASES:
        media = opus(*case['size'], case['seed'])
        kw = dict(focus=case.get('focus', False))
        if case.get('settled'):
            kw['ground'] = select(raw, media)['ground']
        runs = [select(image, media, **kw) for image in (before, prior, raw)]
        for other in runs[:2]:
            assert (other['screen'], other['ground'], other['rows']) == \
                (runs[2]['screen'], runs[2]['ground'], runs[2]['rows']), name
        old, mid, new = runs
        assert len(new['work']) == len(mid['work']) == len(old['work']), name
        assert sum(new['work']) < sum(mid['work']) < sum(old['work']), name
        report['cases'].append(dict(case=name, repaints=len(new['work']) - 1,
                                    first_request_rows=(old['first_rows'], new['first_rows']),
                                    original_instructions=old['work'], previous_instructions=mid['work'],
                                    after_instructions=new['work'],
                                    ratio_to_previous=round(sum(new['work']) / sum(mid['work']), 4),
                                    ratio_to_original=round(sum(new['work']) / sum(old['work']), 4)))
    report['screen_parity'] = ('identical settled framebuffer, final rows and ground in every case, '
                               'against the image before the cover decode changes and the one before '
                               'the integer column coordinates')
    return report


if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release/DP3_V137_CE.img'
    print(json.dumps(check(path.read_bytes()), indent=2))
