#!/usr/bin/env python3
"""Emulation gates for the browser marquee tag extension (v2).

The scroll string for a file with usable tags is ARTIST - TITLE
(plus - ALBUM), parsed by the firmware's own tag dispatcher
(module 0 FUN_0306C51C) from the file opened by (directory cluster,
enumeration index) through the stock open (FUN_030589B6). The open,
the dispatcher, its per-format parsers and the close run as REAL
code from the built variant. Modelled leaves: the dirent fetch
(FUN_03057F8E FAT / FUN_03057E46 FS type 3), the stream leaves the
parsers use (read FUN_03058FA8, seek FUN_030594A0, size
FUN_030545D4, tell FUN_0305943E / FUN_0305945E, yield
FUN_030611E0), the raw sector read FUN_030678CA (failed soft; the
parser proof showed the parse completes without it), and the same
text model the v1 suite uses. Fixture tag bytes live in
work/browser_marquee2/fixtures.py during development; the fixtures
are rebuilt here from the same constructors so this suite is
self-contained in the repo.
"""
import hashlib
import struct
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'patches' / 'framework'))
sys.path.insert(0, str(HERE))

from rknano_image import Image                               # noqa: E402
from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB,         # noqa: E402
                     UC_HOOK_CODE, UC_HOOK_MEM_INVALID)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,  # noqa: E402
                               UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)
import build_marquee as bm                                   # noqa: E402
import test_browser_marquee as t1                            # noqa: E402

PAINT = t1.PAINT
KEY = t1.KEY
FILL = t1.FILL
MEASURE = t1.MEASURE
CHARWIDTH = t1.CHARWIDTH
RENDER = t1.RENDER
ERASE = t1.ERASE
DRAWAT = t1.DRAWAT
KEYED = t1.KEYED
MCTX = bm.MCTX
BCTX = bm.BCTX
LCTX = bm.LCTX
CLOCK = bm.CLOCK
EVENTS = t1.EVENTS
SENTINEL = t1.SENTINEL
STACK_TOP = t1.STACK_TOP
NODE_POOL = t1.NODE_POOL
NODE_SIZE = t1.NODE_SIZE

FETCH = 0x03057F8E
FETCH3 = 0x03057E46
READ = 0x03058FA8
SEEK = 0x030594A0
SIZE = 0x030545D4
TELL_A = 0x0305943E
TELL_B = 0x0305945E
YIELD = 0x030611E0
PRINTF = 0x0306D8F0
MDREAD = 0x030678CA
LOADER = t1.LOADER
BITMAP = t1.BITMAP
FSTYPE_CELL = bm.FSTYPE
DESCRIPTORS = 0x0307AB68
# Extensions with a picture route: selecting one costs one
# extra dirent fetch (the thumbnail probe's open on the
# selecting paint) beyond the tag parse's own.
PIC_EXTS = [ext for ext, _route in bm.PIC_ROUTES]

# Payload layout, recomputed exactly as build_marquee.main does.
_probe, _pe = bm.assemble(bm.BASE + 0x1000, bm.BASE + 0x1020)
_code_len = (len(_probe) + 3) & ~3
STATE = bm.BASE + _code_len
BUF = STATE + bm.STATE_LEN
EXTTAB = BUF + bm.BUF_UNITS * 2
TSTRUCT = (EXTTAB + len(bm.TAG_EXTS) * 3 + 3) & ~3
KEYTAB = (TSTRUCT + bm.STRUCT_SPAN + 3) & ~3  # v5: the window
# key table sits between the struct span and the tag cache
CACHE = KEYTAB + bm.KEY_ENTRIES * bm.KEY_LEN
ENT = bm.assemble(STATE, BUF, _pe,
                  {'struct': TSTRUCT, 'cache': CACHE,
                   'exttab': EXTTAB, 'keytab': KEYTAB})[1]


def entry_buf(node):
    idx = (node >> 4) & (bm.CACHE_ENTRIES - 1)
    return CACHE + idx * bm.CACHE_ENTRY_LEN + 0x14


# ------------------------------------------------ fixtures

def id3v23(frames):
    body = b''
    for fid, payload in frames:
        body += fid + struct.pack('>I', len(payload)) + b'\x00\x00'
        body += payload
    size = len(body)
    sync = bytes(((size >> 21) & 0x7F, (size >> 14) & 0x7F,
                  (size >> 7) & 0x7F, size & 0x7F))
    return b'ID3\x03\x00\x00' + sync + body


def tf(text):
    return b'\x00' + text.encode('latin-1')


def fake_audio(n=2048):
    return (b'\xff\xfb\x90\x64' + bytes(124)) * (n // 128 + 1)


def mp3(frames=None, audio=2048):
    tag = id3v23(frames) if frames else b''
    return tag + fake_audio(audio)[:audio]


def vorbis_comment(pairs):
    body = struct.pack('<I', 0)
    body += struct.pack('<I', len(pairs))
    for k, v in pairs:
        e = (k + '=' + v).encode('utf-8')
        body += struct.pack('<I', len(e)) + e
    return body


def flac(pairs, malformed=False):
    comment = vorbis_comment(pairs)
    if malformed:
        hdr = bytes((0x84,)) + (0xFFFFF0).to_bytes(3, 'big')
        return b'fLaC' + hdr + comment[:16]
    hdr = bytes((0x84,)) + len(comment).to_bytes(3, 'big')
    return b'fLaC' + hdr + comment + fake_audio(512)


def ogg(pairs):
    payload = b'\x03vorbis' + vorbis_comment(pairs)
    hdr = (b'OggS\x00\x00' + (0).to_bytes(8, 'little') +
           (1).to_bytes(4, 'little') + (0).to_bytes(4, 'little') +
           (0).to_bytes(4, 'little') +
           bytes((1, len(payload))))
    return hdr + payload + fake_audio(256)


TAGGED_MP3 = mp3([(b'TIT2', tf('Fixture Title')),
                  (b'TPE1', tf('Fixture Artist')),
                  (b'TALB', tf('Fixture Album'))])
TAGGED_FLAC = flac([('TITLE', 'Flac Title'), ('ARTIST', 'Flac Artist'),
                    ('ALBUM', 'Flac Album')])
TAGGED_OGG = ogg([('TITLE', 'Ogg Title Track'),
                  ('ARTIST', 'Ogg Artist'),
                  ('ALBUM', 'Ogg Album')])
UNTAGGED_MP3 = mp3(None)
MALFORMED_FLAC = flac([], malformed=True)
TITLEONLY_MP3 = mp3([(b'TIT2', tf('Solo Title'))])
ARTISTONLY_MP3 = mp3([(b'TPE1', tf('Lone Artist'))])
WHITESPACE_MP3 = mp3([(b'TIT2', tf('Real Title')),
                      (b'TPE1', tf('   '))])
ALBUMARTIST_MP3 = mp3([(b'TIT2', tf('Group Song')),
                       (b'TPE2', tf('The Group'))])
LONGFIELDS_MP3 = mp3([(b'TIT2', tf('T' * 40)), (b'TPE1', tf('A' * 40)),
                      (b'TALB', tf('L' * 40))])


# ------------------------------------------------ emulator

class Machine:
    def __init__(self, raw):
        self.raw = raw
        self.im = Image(raw)
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x03000000, 0x500000)
        self.u.mem_map(0x01000000, 0x200000)
        self.u.mem_map(0xE000E000, 0x1000)
        self.u.mem_map(0x40000000, 0x400000)
        for idx in (0, 18, 19, 31):
            m = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, size = self.im.module_region(idx, kind)
                if size:
                    self.u.mem_write(m[kind + '_exec'],
                                     raw[off:off + size])
        # Modules 18/19 join the map for the v4 thumbnail path:
        # 18 is resident on hardware; 19 arrives through the
        # loader leaf modelled in the hook.
        self.fills = []
        self.renders = []
        self.erases = []
        self.draws = []
        self.bitmaps = []
        self.measures = []
        self.fetches = []        # (cluster, index) dirent fetches
        self.handles = {}        # handle -> [data, pos]
        self.files = {}          # (cluster, index) -> data
        self.dirents = {}        # (cluster, index) -> 32-byte dirent
        self.mdreads = 0
        self.u.hook_add(UC_HOOK_CODE, self._hook)
        self.u.hook_add(UC_HOOK_MEM_INVALID, self._bad)

    def _bad(self, uc, access, address, size, value, user):
        pc = uc.reg_read(UC_ARM_REG_PC)
        print(f'  MEMFAULT access={access} addr={address:#x} '
              f'size={size} pc={pc:#x} fetches={self.fetches}')
        return False

    def _bind(self, handle):
        """Bind a stream handle to its fixture bytes via the
        descriptor the real open filled (slot +0xC = directory
        cluster, +0x1C = index). Lazy, because the parse runs
        inside the same paint as the open. A closed slot drops
        the binding, so a reopened handle restarts at 0. The
        binding follows the descriptor's key: when a closed
        slot is reopened for a different file, the next access
        rebinds to the new file (the firmware reads by the
        descriptor's cluster chain, which the open refreshes;
        the v5 window decodes many files through one handle
        slot, which is what exposed the stale binding)."""
        slot = DESCRIPTORS + handle * 0x27E
        if self.r8(slot) == 0:
            self.handles.pop(handle, None)
            return
        key = (self.r32(slot + 0xC), self.r32(slot + 0x1C))
        cur = self.handles.get(handle)
        if cur is not None and len(cur) > 2 and cur[2] == key:
            return
        if cur is not None and len(cur) <= 2:
            return
        data = self.files.get(key)
        if data is not None:
            self.handles[handle] = [data, 0, key]

    # -- memory helpers (same as the v1 suite)
    def w32(self, a, v): self.u.mem_write(a, struct.pack('<I', v))
    def w16(self, a, v): self.u.mem_write(a, struct.pack('<H', v))
    def w8(self, a, v): self.u.mem_write(a, bytes([v]))
    def r32(self, a): return struct.unpack('<I', self.u.mem_read(a, 4))[0]
    def r16(self, a): return struct.unpack('<H', self.u.mem_read(a, 2))[0]
    def r8(self, a): return self.u.mem_read(a, 1)[0]

    def wstr(self, a, s):
        for i, ch in enumerate(s):
            self.w16(a + 2 * i, ord(ch))
        self.w16(a + 2 * len(s), 0)

    def read_str(self, a, maxn=90):
        out = []
        for i in range(maxn):
            ch = self.r16(a + 2 * i)
            if ch == 0:
                break
            out.append(chr(ch))
        return ''.join(out)

    def set_event(self, n):
        a = EVENTS + (n // 32) * 4
        self.w32(a, self.r32(a) | (1 << (n % 32)))

    def event(self, n):
        return bool(self.r32(EVENTS + (n // 32) * 4) >> (n % 32) & 1)

    def set_clock(self, t):
        self.w32(CLOCK, t)

    def mq_phase(self):
        return self.r8(STATE + 8)

    def mq_offset(self):
        return self.r16(MCTX + 0xA)

    def call(self, addr, r0=0, r1=0, until=SENTINEL):
        self.u.reg_write(UC_ARM_REG_SP, STACK_TOP)
        self.u.reg_write(UC_ARM_REG_R0, r0)
        self.u.reg_write(UC_ARM_REG_R1, r1)
        self.u.reg_write(UC_ARM_REG_LR, SENTINEL)
        # The budget catches runaway loops; the v5 windowed
        # paint decodes up to seven pictures in one paint at
        # roughly a million instructions each, so the budget
        # sits well above a legitimate paint.
        self.u.emu_start(addr | 1, until, count=16_000_000)

    def paint(self):
        self.call(PAINT, r0=0x030247C4)

    # -- fixture registration
    def add_file(self, cluster, index, data, name11, file_cluster):
        # Replacing a fixture invalidates every handle binding:
        # a handle's byte stream belongs to the file that was
        # registered when it was bound.
        self.handles.clear()
        self.files[(cluster, index)] = data
        d = bytearray(32)
        d[0:11] = name11
        d[11] = 0x20
        struct.pack_into('<H', d, 20, (file_cluster >> 16) & 0xFFFF)
        struct.pack_into('<H', d, 26, file_cluster & 0xFFFF)
        struct.pack_into('<I', d, 28, len(data))
        self.dirents[(cluster, index)] = bytes(d)

    # -- leaves
    def _ret(self, uc, val=None):
        if val is not None:
            uc.reg_write(UC_ARM_REG_R0, val & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def _fetch(self, uc, cluster, index):
        out = uc.reg_read(UC_ARM_REG_R0)
        self.fetches.append((cluster, index))
        d = self.dirents.get((cluster, index))
        if d is None:
            self._ret(uc, 9)
            return
        uc.mem_write(out, d)
        self._ret(uc, 0)

    def _hook(self, uc, addr, size, user):
        if addr == FETCH:
            self._fetch(uc, uc.reg_read(UC_ARM_REG_R1),
                        uc.reg_read(UC_ARM_REG_R2))
        elif addr == FETCH3:
            ptr = uc.reg_read(UC_ARM_REG_R1)
            cluster = struct.unpack('<I', uc.mem_read(ptr, 4))[0]
            self._fetch(uc, cluster, uc.reg_read(UC_ARM_REG_R2))
        elif addr == READ:
            buf = uc.reg_read(UC_ARM_REG_R0)
            count = uc.reg_read(UC_ARM_REG_R1)
            handle = uc.reg_read(UC_ARM_REG_R2) & 0xFF
            self._bind(handle)
            ent = self.handles.get(handle, (b'', 0))
            data, pos = ent[0], ent[1]
            chunk = data[pos:pos + count]
            if chunk:
                uc.mem_write(buf, chunk)
            self.handles[handle][1] = pos + len(chunk)
            self._ret(uc, len(chunk))
        elif addr == SEEK:
            off = uc.reg_read(UC_ARM_REG_R0)
            if off & 0x80000000:
                off -= 1 << 32
            whence = uc.reg_read(UC_ARM_REG_R1)
            handle = uc.reg_read(UC_ARM_REG_R2) & 0xFF
            self._bind(handle)
            ent = self.handles.get(handle, (b'', 0))
            data, pos = ent[0], ent[1]
            if whence == 0:
                pos = off
            elif whence == 1:
                pos = pos + off
            elif whence == 2:
                pos = len(data) - off
            if handle in self.handles:
                self.handles[handle][1] = max(0, pos)
            self._ret(uc, 0)
        elif addr == SIZE:
            handle = uc.reg_read(UC_ARM_REG_R0) & 0xFF
            self._bind(handle)
            ent = self.handles.get(handle, (b'', 0))
            self._ret(uc, len(ent[0]))
        elif addr in (TELL_A, TELL_B):
            handle = uc.reg_read(UC_ARM_REG_R0) & 0xFF
            self._bind(handle)
            ent = self.handles.get(handle, (b'', 0))
            self._ret(uc, ent[1])
        elif addr in (YIELD, PRINTF):
            self._ret(uc, 0)
        elif addr == MDREAD:
            self.mdreads += 1
            self._ret(uc, -1)
        elif addr == FILL:
            sp = uc.reg_read(UC_ARM_REG_SP)
            self.fills.append(tuple(
                uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                         UC_ARM_REG_R2, UC_ARM_REG_R3))
                + (struct.unpack('<I', uc.mem_read(sp, 4))[0]
                   & 0xFFFF,))
            self._ret(uc)
        elif addr == MEASURE:
            s = self.read_str(uc.reg_read(UC_ARM_REG_R0))
            self.measures.append(s)
            uc.reg_write(UC_ARM_REG_R0,
                         t1.model_width([ord(c) for c in s]))
            self._ret(uc)
        elif addr == CHARWIDTH:
            ch = uc.reg_read(UC_ARM_REG_R0) & 0xFFFF
            uc.reg_write(UC_ARM_REG_R0, t1.model_width([ch]))
            self._ret(uc)
        elif addr == RENDER:
            rect = struct.unpack('<4H', uc.mem_read(
                uc.reg_read(UC_ARM_REG_R0), 8))
            s = self.read_str(uc.reg_read(UC_ARM_REG_R2))
            self.renders.append((rect, s))
            self._ret(uc)
        elif addr == ERASE:
            sp = uc.reg_read(UC_ARM_REG_SP)
            y1 = struct.unpack('<i', uc.mem_read(sp, 4))[0]
            self.erases.append((uc.reg_read(UC_ARM_REG_R1),
                                uc.reg_read(UC_ARM_REG_R2),
                                uc.reg_read(UC_ARM_REG_R3), y1))
            self._ret(uc)
        elif addr in (DRAWAT, KEYED):
            self.draws.append((addr, uc.reg_read(UC_ARM_REG_R0)))
            self._ret(uc)
        elif addr == LOADER:
            idx = uc.reg_read(UC_ARM_REG_R0)
            mm = self.im.modules[idx]
            for kind in ('code', 'data'):
                off, sz = self.im.module_region(idx, kind)
                if sz:
                    uc.mem_write(mm[kind + '_exec'],
                                 self.raw[off:off + sz])
            if mm.get('bss_len'):
                uc.mem_write(mm['bss_exec'], bytes(mm['bss_len']))
            self._ret(uc, 0)
        elif addr == BITMAP:
            a = [uc.reg_read(r) for r in (UC_ARM_REG_R0,
                                          UC_ARM_REG_R1,
                                          UC_ARM_REG_R2,
                                          UC_ARM_REG_R3)]
            mode, ptr = struct.unpack('<II', uc.mem_read(
                uc.reg_read(UC_ARM_REG_SP), 8))
            px = struct.unpack('<%dH' % a[2],
                               uc.mem_read(ptr, a[2] * 2)) if a[2] \
                else ()
            self.bitmaps.append({'x': a[0], 'y': a[1], 'w': a[2],
                                 'h': a[3], 'mode': mode, 'px': px})
            self._ret(uc, 0)


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print('  ok:', msg)


def make_node2(m, idx, name, ext, size, ordinal, file_cluster=2,
               directory=False):
    a = t1.make_node(m, idx, name, ext, size, directory)
    m.w32(a + 0x0C, ordinal)
    m.u.mem_write(a + 0x63, struct.pack('<H',
                                        (file_cluster >> 16) & 0xFFFF))
    m.u.mem_write(a + 0x69, struct.pack('<H', file_cluster & 0xFFFF))
    return a


def name11(ext):
    return b'FILE    ' + ext


def scene(m, subjects):
    """Build the full seven node chain the painter walks.
    subjects maps a row index to a make_node2 argument tuple
    (name, ext, size, ordinal[, file_cluster[, directory]]);
    other rows are inert fillers."""
    nodes = {}
    for i in range(7):
        if i in subjects:
            nodes[i] = make_node2(m, i, *subjects[i])
        else:
            nodes[i] = make_node2(m, i, f'Filler {i}', b'MP3',
                                  1000, i)
    return nodes


def setup(m, dir_cluster=7, fs3=False):
    t1.base_fixture(m)
    m.w8(FSTYPE_CELL, 3 if fs3 else 1)
    if fs3:
        m.w32(BCTX + 0x18, dir_cluster)
        m.w32(BCTX + 0x14, 0xFFFF)
    else:
        m.w32(BCTX + 0x14, dir_cluster)


def run_dwell(m, t0=1000):
    """Paint the selecting paint at t0 and the dwell paints to
    expiry at t0 + 100; returns the registered string pointer."""
    m.set_event(0x144)
    m.set_clock(t0)
    m.paint()
    for t in range(t0 + 10, t0 + 101, 10):
        m.set_clock(t)
        m.paint()
    return m.r32(LCTX + 0xC)


# ------------------------------------------------ gates

def test_tagged(m, label, data, ext, node_name, want):
    print(f'tagged fixture scrolls tags: {label}')
    setup(m)
    a = scene(m, {0: (node_name, ext, len(data), 0)})[0]
    m.add_file(7, 0, data, name11(ext), 2)
    m.w16(BCTX + 0x1EE, 0)
    sp = run_dwell(m)
    # The parse opens the file once, on the selecting paint.
    # The background decode runs on the same paint and probes
    # the selected file once more when its extension has a
    # picture route (these fixtures carry no picture, so it
    # records a negative entry). No other row is probed: the
    # background belongs to the selection alone. Nothing is
    # fetched at dwell expiry.
    want_fetches = [(7, 0)] * (2 if ext in PIC_EXTS else 1)
    check(m.fetches == want_fetches,
          f'{label}: parse fetch plus the selecting paint window '
          f'probes ({m.fetches})')
    check(sp == entry_buf(a),
          f'{label}: the cache entry buffer is registered')
    got = m.read_str(entry_buf(a))
    check(got == want, f'{label}: scroll string {got!r} '
                       f'(want {want!r})')
    check(m.mq_phase() == 1, f'{label}: phase SCROLL')
    offs = []
    for t in range(1110, 1250, 10):
        m.set_clock(t)
        m.paint()
        offs.append(m.mq_offset())
    check(max(offs) >= 3, f'{label}: scrolling advances {offs}')


def test_fallback(m, label, data, ext, node_name, want):
    print(f'fallback keeps the v1 string: {label}')
    setup(m)
    a = scene(m, {0: (node_name, ext, len(data), 0)})[0]
    m.add_file(7, 0, data, name11(ext), 2)
    m.w16(BCTX + 0x1EE, 0)
    sp = run_dwell(m)
    want_fetches = [(7, 0)] * (2 if ext in PIC_EXTS else 1)
    check(m.fetches == want_fetches,
          f'{label}: the parse was attempted ({m.fetches})')
    check(sp != entry_buf(a),
          f'{label}: no tag string is registered')
    got = m.read_str(BUF)
    check(got == want, f'{label}: v1 string {got!r} '
                       f'(want {want!r})')


def test_folder_no_read(m):
    print('folder never triggers a file read')
    setup(m)
    scene(m, {0: ('A Rather Long Folder Name Here Indeed',
                  b'   ', 4096, 0, 2, True)})
    m.w16(BCTX + 0x1EE, 0)
    run_dwell(m)
    # The folder itself is never opened, and no other row is
    # probed: the background decode serves the selection alone,
    # and a folder resolves negative without a fetch.
    check(m.fetches == [],
          f'no dirent fetch for the folder itself ({m.fetches})')
    check(m.read_str(BUF) == 'A Rather Long Folder Name Here Indeed',
          'folder composes the bare name as in v1')


def test_cache_and_invalidation(m):
    print('cache: reselect hits, directory change invalidates')
    setup(m)
    nodes = scene(m, {0: ('First Song', b'MP3', len(TAGGED_MP3), 0),
                      1: ('Second Song', b'FLA', len(TAGGED_FLAC), 1),
                      2: ('Folder', b'   ', 0, 2, 2, True)})
    a = nodes[0]
    m.add_file(7, 0, TAGGED_MP3, name11(b'MP3'), 2)
    m.add_file(7, 1, TAGGED_FLAC, name11(b'FLA'), 3)
    m.add_file(9, 0, TAGGED_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    run_dwell(m)
    # A's selecting paint: the parse fetch, then the
    # background decode's probe of the selected file (A is
    # registered and picture-less, so it records a negative).
    # No other row is ever probed.
    win = [(7, 0), (7, 0)]
    check(m.fetches == win,
          f'A parsed once, probed once ({m.fetches})')
    m.w16(BCTX + 0x1EE, 1)
    m.set_event(0x144)
    run_dwell(m, 2000)
    check(m.fetches == win + [(7, 1), (7, 1)],
          f'B parsed once and probed once ({m.fetches})')
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    run_dwell(m, 3000)
    # The string cache hits (no parse fetch). The background
    # store holds one entry, keyed to the current selection:
    # it now holds B, so reselecting A re-probes A once. (The
    # windowed build held every visible row's entry and
    # re-probed nothing here; the single background entry is
    # the new model's stated discipline.)
    check(m.fetches == win + [(7, 1), (7, 1), (7, 0)],
          f'reselecting A hits the string cache and re-probes '
          f'the background once ({m.fetches})')
    check(m.read_str(entry_buf(a)) ==
          'Fixture Title - Fixture Artist - Fixture Album',
          'A still scrolls its tags after reselection')
    # Key press on A: dwell restarts, still no re-read.
    m.set_clock(3200)
    m.call(KEY, until=KEY + 4)
    for t in range(3210, 3301, 10):
        m.set_clock(t)
        m.paint()
    check(m.fetches == win + [(7, 1), (7, 1), (7, 0)],
          f'key reset does not re-read ({m.fetches})')
    # Directory change: same nodes, new directory cluster.
    m.w32(BCTX + 0x14, 9)
    m.w16(BCTX + 0x1EE, 2)
    m.set_event(0x144)
    run_dwell(m, 4000)
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    run_dwell(m, 5000)
    check(m.fetches[-1] == (9, 0) and m.fetches.count((7, 0)) == 3,
          f'directory change re-parses under the new key '
          f'({m.fetches})')


def test_field_rules(m):
    print('field rules: partial tags, trimming, full fields, '
          'album artist')
    cases = [
        ('title only', TITLEONLY_MP3, 'Solo Title'),
        # v5 lead rule: with no title, the file name leads and
        # the artist is appended (the artist never leads). The
        # v2 to v4 expectation here was 'Lone Artist'.
        ('artist only', ARTISTONLY_MP3,
         'Some Long Enough Name - Lone Artist'),
        ('whitespace artist', WHITESPACE_MP3, 'Real Title'),
        # v5 order: title first, then the (fallback) artist.
        ('album artist fallback', ALBUMARTIST_MP3,
         'Group Song - The Group'),
        # v3: the fields are carried in full (v2 capped them at
        # 24/24/13, which expected 'A' * 24 + ' - ' + 'T' * 24 +
        # ' - ' + 'L' * 13 here). The fixture fields are 40 units
        # each, beyond every v2 cap. v5 order: title, artist,
        # album.
        ('full fields', LONGFIELDS_MP3,
         'T' * 40 + ' - ' + 'A' * 40 + ' - ' + 'L' * 40),
    ]
    for label, data, want in cases:
        setup(m)
        a = scene(m, {0: ('Some Long Enough Name', b'MP3',
                          len(data), 0)})[0]
        m.add_file(7, 0, data, name11(b'MP3'), 2)
        m.w16(BCTX + 0x1EE, 0)
        run_dwell(m)
        got = m.read_str(entry_buf(a), 200)
        check(got == want, f'{label}: {got!r} (want {want!r})')
        # reset payload state via the exit hook for the next case
        m.call(t1.EXIT)


def test_wma_excluded(m):
    print('WMA keeps the v1 string (overlay parser not resident)')
    setup(m)
    scene(m, {0: ('Windows Tune', b'WMA', len(TAGGED_MP3), 0)})
    m.add_file(7, 0, TAGGED_MP3, name11(b'WMA'), 2)
    m.w16(BCTX + 0x1EE, 0)
    run_dwell(m)
    # No fetch at all: WMA has no parse and no picture route,
    # and no other row is probed under the background model.
    check(m.fetches == [],
          f'no fetch for WMA itself ({m.fetches})')
    got = m.read_str(BUF)
    check(got.startswith('Windows Tune - WMA - '),
          f'v1 string for WMA ({got!r})')


def test_fs3(m):
    print('FS type 3: the open is attempted with the +0x18 cluster')
    # The payload's own contract is what is gated here: on FS type
    # 3 the directory cluster must come from the level record's
    # +0x18 twin, not +0x14. The modelled fetch refuses, the stock
    # open fails soft, and the v1 string results; the exFAT entry
    # handling inside the stock open is the scan's own machinery
    # and stays a Phase E item (design.md).
    setup(m, dir_cluster=7, fs3=True)
    scene(m, {0: ('Fixture Song', b'MP3', len(TAGGED_MP3), 0)})
    m.add_file(7, 0, TAGGED_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    run_dwell(m)
    # Every fetch must use cluster 7 (from +0x18), never the
    # 0xFFFF at +0x14, and the first two are the parse and the
    # selected row's probe of (7, 0). The FS3 model's stock open
    # records extra dirent fetches per open at higher indices
    # (visible in the trace); the payload issues exactly one
    # open per visible row, which the v5 suite proves from the
    # key table state.
    check(all(c == 7 for c, _i in m.fetches)
          and m.fetches[:2] == [(7, 0), (7, 0)],
          f'FS3 fetches all used cluster 7 from +0x18, not the '
          f'0xFFFF at +0x14 ({m.fetches})')
    got = m.read_str(BUF)
    check(got.startswith('Fixture Song - MP3 - '),
          f'v1 string after the refused FS3 open ({got!r})')


def test_parse_inside_dwell(m):
    print('the parse lands on the selecting paint, inside the dwell')
    setup(m)
    scene(m, {0: ('Fixture Song', b'MP3', len(TAGGED_MP3), 0)})
    m.add_file(7, 0, TAGGED_MP3, name11(b'MP3'), 2)
    m.w16(BCTX + 0x1EE, 0)
    m.set_event(0x144)
    m.set_clock(1000)
    m.paint()
    check(m.fetches == [(7, 0), (7, 0)],
          'parse and background probe already done on the '
          'selecting paint')
    check(m.mq_offset() == 0, 'no step on the selecting paint')
    for t in range(1010, 1100, 10):
        m.set_clock(t)
        m.paint()
    check(m.mq_offset() == 0, 'no step before the dwell expires')


def main():
    stock = (REPO / 'DP3_V137.img').read_bytes()
    if hashlib.sha256(stock).hexdigest() != bm.STOCK_SHA:
        raise SystemExit('stock image hash mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        raw = t1.build_variant(tmp)
    print(f'variant sha256: {hashlib.sha256(raw).hexdigest()}')
    print(f'variant length: {len(raw)} (stock {len(stock)}, '
          f'delta {len(raw) - len(stock)})')
    test_tagged(Machine(raw), 'MP3/ID3v2', TAGGED_MP3, b'MP3',
                'Fixture Song',
                'Fixture Title - Fixture Artist - Fixture Album')
    test_tagged(Machine(raw), 'FLAC/Vorbis', TAGGED_FLAC, b'FLA',
                'Flac Song', 'Flac Title - Flac Artist - Flac Album')
    test_tagged(Machine(raw), 'OGG/Vorbis', TAGGED_OGG, b'OGG',
                'Ogg Song',
                'Ogg Title Track - Ogg Artist - Ogg Album')
    test_fallback(Machine(raw), 'untagged MP3', UNTAGGED_MP3, b'MP3',
                  'Plain Tune', 'Plain Tune - MP3 - 2 KB')
    test_fallback(Machine(raw), 'malformed FLAC', MALFORMED_FLAC,
                  b'FLA', 'Broken Tune',
                  f'Broken Tune - FLA - {len(MALFORMED_FLAC)} B')
    test_folder_no_read(Machine(raw))
    test_cache_and_invalidation(Machine(raw))
    test_field_rules(Machine(raw))
    test_wma_excluded(Machine(raw))
    test_fs3(Machine(raw))
    test_parse_inside_dwell(Machine(raw))
    print('ALL MARQUEE TAG GATES PASS')


if __name__ == '__main__':
    main()
