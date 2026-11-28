#!/usr/bin/env python3
"""Port the minimal-image patch set from V137 to a newer official image.

Every patch in patches/framework/patches/ pins a V137 exec address and the
stock bytes found there. Fosi's later images move code and globals, so this
tool re-derives each patch for a target image from evidence inside that
image, and refuses what it cannot prove.

  Locate(site)  The V137 bytes around the site, with the immediates of 32-bit
                BL/B.W/BLX and every word whose value is an IRAM address
                masked out, searched in the same module of the target. The
                window grows (both sides, left only, right only) until exactly
                one place matches. A module boundary inside the window is
                context too. Result: an address, Missing or Ambiguous.
  Relocation    Every branch, PC-relative load or ADR, MOVW/MOVT pair and data
                word in a replacement that points outside its own patch is
                mapped: into another patch by that patch's new address, into
                code by Locate (cross-checked against the BL found at the
                matching stock instruction), into RAM only by evidence, the
                same constant at a located stock reference. No evidence means
                UNPORTED. A global address is never guessed.
  Caves         The target range holds the same fill bytes, lies inside the
                module's declared length, nothing in the target references it,
                and no other module is mapped over it.
  Routines      Each feature names the stock routines its behaviour relies on.
                If one's masked body differs in the target, every patch of the
                feature is a CONFLICT.
  Features      Patches that only work together port together or not at all.

Writes patches/ported/<VERSION>/: the ported patch files (with base_sha256
and ported_from), manifest.txt, transplants.txt, port_report.json and
README.md. Offline and read-only on its inputs.

    python3 tools/port_patches.py --target DP3_V162.img [--source DP3_V137.img]
"""
import argparse
import bisect
import hashlib
import importlib.util
import json
import struct
import sys
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
from official_images import OFFICIAL  # noqa: E402
from rknano_image import Image  # noqa: E402

FRAMEWORK = REPO / 'patches' / 'framework'
MANIFEST = FRAMEWORK / 'patches' / 'manifest.txt'
TRANSPLANTS = FRAMEWORK / 'patches' / 'transplants.txt'
PORTED = REPO / 'patches' / 'ported'
SOURCE_VERSION = 'V137'

# IRAM: code and globals both live here, and both move between versions.
# Peripheral addresses and core-1 addresses (fixed module records) do not.
RELOC = (0x03000000, 0x03100000)

# What each feature's behaviour relies on in V137: its patches (manifest
# names) and the stock code and data that must be unchanged in the target:
# (module, entry, label) is a routine, compared under the mask;
# (module, start, label, length) is a data block, compared byte for byte.
# Entries come from each patch's rationale.
FEATURES = {
    'selftest': (('noop-selftest',), ()),
    'dac-fix': (('dac-fix-1-branch', 'dac-fix-2-cave'),
                ((0, 0x03060C4C, 'dac_write'),)),
    'clock-v1': (tuple(f'clock-v1-row-{n:02}' for n in (*range(5, 12), *range(14, 23))),
                 ((0, 0x03066EFC, 'clock solver FREQSetFreq'),
                  (0, 0x03079824, 'clock request table (36 rows; row 1 is the floor)', 36 * 28))),
    'i2c-reset-pulse': (('i2c-reset-pulse',),
                        ((0, 0x0306021C, 'i2c controller init'),
                         (0, 0x03064920, 'delay_us'))),
    'gapless': (('gapless-0-state-pair', 'gapless-1-gate-hook', 'gapless-2-gate-cave',
                 'gapless-3-flag-literal', 'gapless-4-keep-decoder', 'gapless-5-gate-tail',
                 'gapless-6-arm', 'gapless-warm-start'),
                ((0, 0x0306CB2C, 'core-1 decoder reset-and-start'),
                 (0, 0x0306CB0C, 'core-1 halt'),
                 (0, 0x03064F7E, 'playback monitor'),
                 (33, 0x03088824, 'per-codec dispatcher'),
                 (33, 0x0308936E, 'decoder file close'),
                 (33, 0x030893C4, 'decoder shutdown'),
                 (33, 0x03089AD6, 'stop-and-advance helper'),
                 (34, 0x0308BFBC, 'decoder start'))),
    'sortkeys': (('sortkeys-comparator-hook', 'sortkeys-builder-a-hook',
                  'sortkeys-builder-bmain-hook', 'sortkeys-builder-balt-hook', 'sortkeys-cave'),
                 ((39, 0x0307D620, 'library comparator'),
                  (39, 0x0307D6EA, 'sorted insert'),
                  (39, 0x0307D80A, 'key builder A'),
                  (39, 0x0307D8C4, 'key builder B'),
                  (0, 0x03067510, 'string read'))),
    'wheel-period': (('power-wheel-period-1000us',),
                     ((1, 0x0307D1CC, 'key init'),
                      (0, 0x030510A2, 'TimerPeriodSet'))),
}
# Routine bodies that differ from V137 and were read and judged harmless to
# the feature: (feature, V137 entry) -> {masked target body sha256: why}.
# The hash covers the whole target routine with its own relocatable fields
# masked, so any further change by Fosi makes the routine a CONFLICT again.
REVIEWED = {
    ('dac-fix', 0x03060C4C): {
        'c5be9d8dbe43423d63e0140637feb21a8e16280c64aa4e564fbe849374ebf3d8':
            'one change: ldrb.w ip, [ip, #0x2e8] became #0x306 at +0x0a, a config byte '
            'read before the transfer from the SAVEINFO block (which grew); the counter-'
            'block literal (0x0300411d in every version), the success branch at +0xc8 '
            'that the hook retargets and the shared tail the cave rejoins are unchanged',
    },
    ('sortkeys', 0x0307D8C4): {
        '568e65b2ac5d99eb56d0638c39de8ba0bb96b0dbbbac159111b584e9ca5be24d':
            'Fosi added a record-count cap after the main fold loop: +0xcc `cmp r0, #0; '
            'it ne; cmpne.w r5, #0x2000; blo`, with r0 reloaded from the stack after the '
            'loop exit, so the hooks clobbering r0-r3 do not feed it; both fold loops the '
            'hooks replace, their record pointer (r4) and their exits are unchanged',
    },
}

# Patches whose bytes are table data inside a code segment, not instructions.
DATA_PATCHES = frozenset(FEATURES['clock-v1'][0])


def in_reloc(v):
    return RELOC[0] <= v < RELOC[1]


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


# ------------------------------------------------------------ Thumb decode

@dataclass(frozen=True)
class Insn:
    addr: int
    size: int
    op: str          # bl blx b.w bcc.w b bcc cbz ldr adr movw movt tbb tbh it cmp ret other
    ref: int = None  # branch target, PC-relative address, imm16, IT length or cmp imm
    rd: int = None


BRANCHES = frozenset({'bl', 'blx', 'b.w', 'bcc.w', 'b', 'bcc', 'cbz'})
PCREL = BRANCHES | {'ldr', 'adr'}
LONG_CALLS = frozenset({'bl', 'blx', 'b.w'})


def _sext(v, bits):
    return v - (1 << bits) if v >> (bits - 1) & 1 else v


def decode(buf, i, addr):
    hw1 = buf[i] | buf[i + 1] << 8
    if hw1 >> 11 in (0x1D, 0x1E, 0x1F) and i + 4 <= len(buf):
        return _decode32(hw1, buf[i + 2] | buf[i + 3] << 8, addr)
    return _decode16(hw1, addr)


def _decode16(hw, a):
    base = (a + 4) & ~3
    if hw & 0xFF87 in (0x4700, 0x4687) or hw & 0xFF00 == 0xBD00:
        return Insn(a, 2, 'ret')                       # bx rm, mov pc, rm, pop {.., pc}
    if hw & 0xF800 == 0xE000:
        return Insn(a, 2, 'b', a + 4 + _sext((hw & 0x7FF) << 1, 12))
    if hw & 0xF000 == 0xD000 and (hw >> 8) & 0xF < 0xE:
        return Insn(a, 2, 'bcc', a + 4 + _sext((hw & 0xFF) << 1, 9))
    if hw & 0xF500 == 0xB100:
        return Insn(a, 2, 'cbz', a + 4 + ((hw >> 9 & 1) << 6 | (hw >> 3 & 0x1F) << 1))
    if hw & 0xF800 == 0x4800:
        return Insn(a, 2, 'ldr', base + (hw & 0xFF) * 4, hw >> 8 & 7)
    if hw & 0xF800 == 0xA000:
        return Insn(a, 2, 'adr', base + (hw & 0xFF) * 4, hw >> 8 & 7)
    if hw & 0xFF00 == 0xBF00 and hw & 0xF:
        return Insn(a, 2, 'it', 4 - ((hw & 0xF) & -(hw & 0xF)).bit_length() + 1)
    if hw & 0xF800 == 0x2800:
        return Insn(a, 2, 'cmp', hw & 0xFF, hw >> 8 & 7)
    return Insn(a, 2, 'other')


def _decode32(h1, h2, a):
    base = (a + 4) & ~3
    if h1 & 0xF800 == 0xF000 and h2 & 0x8000:
        s, j1, j2 = h1 >> 10 & 1, h2 >> 13 & 1, h2 >> 11 & 1
        kind = h2 & 0x5000
        if kind == 0x0000:
            if (h1 >> 6) & 0xF >= 0xE:
                return Insn(a, 4, 'other')
            off = _sext(s << 20 | j2 << 19 | j1 << 18 | (h1 & 0x3F) << 12 | (h2 & 0x7FF) << 1, 21)
            return Insn(a, 4, 'bcc.w', a + 4 + off)
        i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
        off = _sext(s << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1, 25)
        if kind == 0x5000:
            return Insn(a, 4, 'bl', a + 4 + off)
        if kind == 0x1000:
            return Insn(a, 4, 'b.w', a + 4 + off)
        return Insn(a, 4, 'blx', base + off)
    if h1 & 0xFE1F == 0xF81F:                          # ldr{b,h,sb,sh}.w rt, [pc, #+-imm12]
        imm = h2 & 0xFFF
        return Insn(a, 4, 'ldr', base + (imm if h1 & 0x80 else -imm), h2 >> 12)
    if h1 & 0xFBFF in (0xF20F, 0xF2AF) and not h2 & 0x8000:   # adr.w (add/sub rd, pc)
        imm = (h1 >> 10 & 1) << 11 | (h2 >> 12 & 7) << 8 | h2 & 0xFF
        return Insn(a, 4, 'adr', base + (imm if h1 & 0xFBFF == 0xF20F else -imm), h2 >> 8 & 0xF)
    if h1 & 0xFB70 == 0xF240 and not h2 & 0x8000:      # movw / movt
        imm = (h1 & 0xF) << 12 | (h1 >> 10 & 1) << 11 | (h2 >> 12 & 7) << 8 | h2 & 0xFF
        return Insn(a, 4, 'movt' if h1 & 0x80 else 'movw', imm, h2 >> 8 & 0xF)
    if h1 & 0xFFF0 == 0xE8D0 and h2 & 0xFFE0 == 0xF000:
        return Insn(a, 4, 'tbh' if h2 & 0x10 else 'tbb', h2 & 0xF)
    if (h1 == 0xE8BD and h2 & 0x8000) or (h1 == 0xF85D and h2 == 0xFB04):
        return Insn(a, 4, 'ret')                       # pop.w {.., pc}, ldr pc, [sp], #4
    return Insn(a, 4, 'other')


def encode(insn, raw, addr, ref):
    """`raw` (the instruction's bytes) re-encoded at `addr` so that its
    PC-relative operand or MOVW/MOVT immediate is `ref`; None if the new
    value does not fit the encoding."""
    op = insn.op
    if op in ('movw', 'movt'):
        h1, h2 = struct.unpack('<HH', raw)
        h1 = h1 & 0xFBF0 | (ref >> 12) & 0xF | (ref >> 11 & 1) << 10
        h2 = h2 & 0x8F00 | (ref >> 8 & 7) << 12 | ref & 0xFF
        return struct.pack('<HH', h1, h2)
    base = (addr + 4) & ~3
    off = ref - (addr + 4)
    if op in ('bl', 'b.w'):
        if off & 1 or not -(1 << 24) <= off < 1 << 24:
            return None
        h1, h2 = struct.unpack('<HH', raw)
        s = off < 0
        i1, i2 = off >> 23 & 1, off >> 22 & 1
        h1 = h1 & 0xF800 | s << 10 | off >> 12 & 0x3FF
        h2 = h2 & 0xD000 | ((1 - i1) ^ s) << 13 | ((1 - i2) ^ s) << 11 | off >> 1 & 0x7FF
        return struct.pack('<HH', h1, h2)
    if op == 'bcc.w':
        if off & 1 or not -(1 << 20) <= off < 1 << 20:
            return None
        h1, h2 = struct.unpack('<HH', raw)
        s = off < 0
        h1 = h1 & 0xFBC0 | s << 10 | off >> 12 & 0x3F
        h2 = h2 & 0xD000 | (off >> 18 & 1) << 13 | (off >> 19 & 1) << 11 | off >> 1 & 0x7FF
        return struct.pack('<HH', h1, h2)
    hw = struct.unpack('<H', raw[:2])[0]
    if op == 'b':
        return struct.pack('<H', 0xE000 | off >> 1 & 0x7FF) if -2048 <= off <= 2046 and not off & 1 else None
    if op == 'bcc':
        return struct.pack('<H', hw & 0xFF00 | off >> 1 & 0xFF) if -256 <= off <= 254 and not off & 1 else None
    if op == 'cbz':
        return (struct.pack('<H', hw & 0xFD07 | (off >> 6 & 1) << 9 | (off >> 1 & 0x1F) << 3)
                if 0 <= off <= 126 and not off & 1 else None)
    off = ref - base
    if op in ('ldr', 'adr') and insn.size == 2:
        return struct.pack('<H', hw & 0xFF00 | off >> 2) if 0 <= off <= 1020 and not off & 3 else None
    h1, h2 = struct.unpack('<HH', raw)
    if op == 'ldr' and h1 & 0xFE1F == 0xF81F and abs(off) <= 0xFFF:
        return struct.pack('<HH', h1 & ~0x80 | (0x80 if off >= 0 else 0), h2 & 0xF000 | abs(off))
    if op == 'adr' and abs(off) <= 0xFFF:
        imm = abs(off)
        h1 = (0xF20F if off >= 0 else 0xF2AF) | (imm >> 11 & 1) << 10
        return struct.pack('<HH', h1, (imm >> 8 & 7) << 12 | h2 & 0x0F00 | imm & 0xFF)
    return None


# ---------------------------------------------------------------- images

@dataclass
class Segment:
    module: int
    region: str
    exec: int
    data: bytes

    @property
    def end(self):
        return self.exec + len(self.data)

    def holds(self, addr, n=1):
        return self.exec <= addr and addr + n <= self.end

    @cached_property
    def insns(self):
        """Linear sweep. Data inside code decodes as junk, which only ever
        over-masks a signature or over-reports a reference."""
        out, i, d = [], 0, self.data
        while i + 2 <= len(d):
            ins = decode(d, i, self.exec + i)
            out.append(ins)
            i += ins.size
        return out

    @cached_property
    def starts(self):
        return [ins.addr for ins in self.insns]

    def insns_in(self, lo, hi):
        i = bisect.bisect_left(self.starts, lo)
        j = bisect.bisect_left(self.starts, hi)
        return self.insns[i:j]

    @cached_property
    def mask(self):
        m = bytearray(b'\xff' * len(self.data))
        if self.region == 'code':
            # Long calls and literal-pool offsets change whenever code between
            # the instruction and its target or pool changes size. The pool
            # word itself is checked through the target's own instruction.
            for ins in self.insns:
                o = ins.addr - self.exec
                if ins.op in LONG_CALLS:
                    m[o:o + 4] = b'\x00\xf8\x00\xd0'
                elif ins.op == 'ldr' and ins.size == 2:
                    m[o] = 0
                elif ins.op == 'ldr':
                    m[o + 2] = 0
                    m[o + 3] = 0xF0
        for o in range((-self.exec) % 4, len(self.data) - 3, 4):
            if in_reloc(u32(self.data, o)):
                m[o:o + 4] = bytes(4)
        return bytes(m)

    def insn_at(self, addr):
        return decode(self.data, addr - self.exec, addr)


class Firmware:
    def __init__(self, raw):
        self.raw = bytes(raw)
        self.image = Image(self.raw)
        self.sha256 = hashlib.sha256(self.raw).hexdigest()
        self.version = OFFICIAL.get(self.sha256, (None,))[0]
        self._segs = {}

    def seg(self, module, region):
        key = (module, region)
        if key not in self._segs:
            off, ln = self.image.module_region(module, region)
            self._segs[key] = Segment(module, region, self.image.modules[module][region + '_exec'],
                                      self.raw[off:off + ln])
        return self._segs[key]

    def code_module(self, module, addr):
        """The module whose code holds `addr` as seen from `module`'s code:
        the module itself (an overlay shares its slot with others) or the
        resident module 0."""
        for m in dict.fromkeys((module, 0)):
            if self.seg(m, 'code').holds(addr):
                return m
        return None

    def spans(self, module):
        m = self.image.modules[module]
        return [(m[k + '_exec'], m[k + '_exec'] + m[k + '_len'])
                for k in ('code', 'data', 'bss') if m[k + '_len']]

    def coresident(self, a, b):
        """Two overlays mapped over the same code slot are never loaded together."""
        if a == b:
            return True
        x, y = self.seg(a, 'code'), self.seg(b, 'code')
        return not (x.data and y.data and x.exec < y.end and y.exec < x.end)

    @cached_property
    def references(self):
        """Every address the image could reference: branch targets,
        PC-relative loads and ADRs, MOVW/MOVT pairs, and address-valued
        words in every segment. Sorted (address, source module, kind, at)."""
        out = []
        for m in range(len(self.image.modules)):
            for region in ('code', 'data'):
                s = self.seg(m, region)
                if not s.data:
                    continue
                if region == 'code':
                    low = {}
                    for ins in s.insns:
                        if ins.op in PCREL:
                            out.append((ins.ref & ~1, m, ins.op, ins.addr))
                        elif ins.op == 'movw':
                            low[ins.rd] = (ins.ref, ins.addr)
                        elif ins.op == 'movt' and ins.rd in low and ins.addr - low[ins.rd][1] <= 16:
                            out.append(((ins.ref << 16 | low.pop(ins.rd)[0]) & ~1, m, 'movw/movt', ins.addr))
                for o in range((-s.exec) % 4, len(s.data) - 3, 4):
                    v = u32(s.data, o)
                    if in_reloc(v):
                        out.append((v & ~1, m, 'word', s.exec + o))
        out.sort()
        return out

    def refs_into(self, module, lo, hi):
        refs = self.references
        i = bisect.bisect_left(refs, (lo,))
        found = []
        while i < len(refs) and refs[i][0] < hi:
            if self.coresident(refs[i][1], module):
                found.append(refs[i])
            i += 1
        return found

    def nearest_ref_below(self, module, addr, floor):
        """Nearest address below `addr` referenced by a co-resident module
        that itself runs from IRAM. Core-1 decoders (exec 0x01000000) carry
        constants that only look like IRAM addresses and never move."""
        refs = self.references
        i = bisect.bisect_left(refs, (addr,)) - 1
        while i >= 0 and refs[i][0] >= floor:
            if self.coresident(refs[i][1], module) and in_reloc(self.seg(refs[i][1], 'code').exec):
                return refs[i][0]
            i -= 1
        return None


# ----------------------------------------------------------------- locate

@dataclass(frozen=True)
class Site:
    module: int
    region: str
    address: int


@dataclass(frozen=True)
class Hit:
    address: int
    lo: int          # matched V137 window [lo, hi), exec addresses
    hi: int


@dataclass(frozen=True)
class Missing:
    reason: str


@dataclass(frozen=True)
class Ambiguous:
    hits: int
    reason: str


GROWTH = (0, 4, 8, 16, 32, 64, 128, 256, 512)
MIN_COMPARED = 16    # a unique match on fewer compared bytes is not evidence


def _matches(hay, pat, mask, phase, start_anchor, end_anchor):
    """Offsets s (s % 4 == phase) where hay[s:] equals pat under mask; None
    when the mask leaves nothing to compare."""
    runs, partial, i = [], [], 0
    while i < len(pat):
        if mask[i] == 0xFF:
            j = i
            while j < len(pat) and mask[j] == 0xFF:
                j += 1
            runs.append((i, pat[i:j]))
            i = j
        else:
            if mask[i]:
                partial.append((i, pat[i] & mask[i], mask[i]))
            i += 1
    if not runs:
        return None
    last = len(hay) - len(pat)
    if start_anchor or end_anchor:
        cands = [0] if start_anchor else [last]
        if start_anchor and end_anchor and last != 0:
            cands = []
    else:
        ao, anchor = max(runs, key=lambda r: len(r[1]))
        cands, j = [], hay.find(anchor)
        while j >= 0:
            s = j - ao
            cands.append(s)
            j = hay.find(anchor, j + 1)
    return [s for s in cands if 0 <= s <= last and s % 4 == phase
            and all(hay[s + o:s + o + len(r)] == r for o, r in runs)
            and all(hay[s + o] & m == v for o, v, m in partial)]


def locate(src, dst, site, n=2):
    """The unique target address that corresponds to `site` (n bytes) in
    the source image: Hit | Missing | Ambiguous."""
    S, D = src.seg(site.module, site.region), dst.seg(site.module, site.region)
    rel = site.address - S.exec
    if not S.holds(site.address, n):
        return Missing(f'{site.address:#x} is outside V137 module {site.module} {site.region}')
    if not D.data:
        return Missing(f'target module {site.module} has no {site.region} segment')
    fewest = None
    for g in GROWTH:
        found = []
        for left, right in (((g, g), (g, 0), (0, g)) if g else ((0, 0),)):
            lo, hi = max(0, rel - left), min(len(S.data), rel + n + right)
            phase = (S.exec + lo - D.exec) % 4
            hits = _matches(D.data, S.data[lo:hi], S.mask[lo:hi], phase,
                            lo == 0 and rel - left < 0, hi == len(S.data) and rel + n + right > len(S.data))
            if hits is not None:
                found.append((lo, hi, {D.exec + h + rel - lo for h in hits}))
        if not found:
            continue
        unique = {next(iter(h)): (lo, hi) for lo, hi, h in found
                  if len(h) == 1 and compared(S.mask[lo:hi]) >= MIN_COMPARED}
        if len(unique) == 1:
            (addr, (lo, hi)), = unique.items()
            return Hit(addr, S.exec + lo, S.exec + hi)
        if len(unique) > 1:
            return Ambiguous(len(unique), 'windows grown left and right match different places')
        if all(not h for _, _, h in found):
            return Missing('no masked match' if g == 0 else
                           f'site matches but its context differs within {g} bytes on every side')
        fewest = min(len(h) for _, _, h in found if h)
        if any(len(h) == 1 for _, _, h in found):
            fewest = 1
    return Ambiguous(fewest or 0, f'still {fewest} matches with {GROWTH[-1]} bytes of context')


def compared(mask):
    return sum(1 for m in mask if m)


def hit_evidence(src, dst, site, hit):
    """Correspondences proven by a match: for every masked item in the
    window, (V137 value, target value, where)."""
    S, D = src.seg(site.module, site.region), dst.seg(site.module, site.region)
    delta = hit.address - site.address
    out = []
    for ins in S.insns_in(hit.lo, hit.hi - 3) if site.region == 'code' else ():
        if ins.op in LONG_CALLS:
            t = D.insn_at(ins.addr + delta)
            if t.op == ins.op:
                out.append((ins.ref, t.ref, f'{ins.op} at {ins.addr:#x}'))
    for a in range(hit.lo + (-hit.lo) % 4, hit.hi - 3, 4):
        v = u32(S.data, a - S.exec)
        if in_reloc(v):
            w = u32(D.data, a + delta - D.exec)
            if in_reloc(w):
                out.append((v, w, f'word at {a:#x}'))
    return out


def masked_body_sha(fw, module, entry):
    """sha256 of a routine's bytes with its own relocatable fields masked,
    followed by every non-address literal it loads."""
    seg = fw.seg(module, 'code')
    end = routine_extent(seg, entry)
    o, n = entry - seg.exec, end - entry
    h = hashlib.sha256(bytes(b & m for b, m in zip(seg.data[o:o + n], seg.mask[o:o + n])))
    for ins in seg.insns_in(entry, end):
        if ins.op == 'ldr' and seg.holds(ins.ref & ~3, 4):
            v = u32(seg.data, (ins.ref & ~3) - seg.exec)
            h.update(struct.pack('<I', 0 if in_reloc(v) else v))
    return h.hexdigest()


def routine_extent(seg, start):
    """End of the routine entered at `start`: decode until an unconditional
    exit past every forward branch target taken inside it. None if none
    is found within 8 KB or a table branch cannot be sized."""
    frontier, it, a, prev = start, 0, start, []
    while seg.holds(a, 2) and a - start < 0x2000:
        ins = seg.insn_at(a)
        cond = it > 0
        it = ins.ref if ins.op == 'it' else max(0, it - 1)
        nxt = a + ins.size
        internal = ins.op in ('bcc', 'cbz', 'bcc.w', 'b') or ins.op == 'b.w' and start <= ins.ref < a
        if internal and start <= ins.ref < start + 0x2000:
            frontier = max(frontier, ins.ref)
        if ins.op in ('tbb', 'tbh'):
            cmp = next((p for p in reversed(prev[-4:]) if p.op == 'cmp' and p.rd == ins.ref), None)
            if cmp is None:
                return None
            hi_bound = any(p.op == 'bcc' and seg.data[p.addr + 1 - seg.exec] == 0xD8 for p in prev[-3:])
            count = cmp.ref + 1 if hi_bound else cmp.ref
            width = 1 if ins.op == 'tbb' else 2
            table = seg.data[nxt - seg.exec:nxt - seg.exec + count * width]
            for k in range(count):
                e = table[k] if width == 1 else table[2 * k] | table[2 * k + 1] << 8
                frontier = max(frontier, nxt + 2 * e)
            nxt += (count * width + 1) & ~1
        if ins.op in ('ret', 'b', 'b.w') and not cond and nxt > frontier:
            return nxt
        prev.append(ins)
        a = nxt
    return None


# ------------------------------------------------------------- the port

@dataclass
class Port:
    patch: dict
    feature: str
    role: str                  # noop | code | data | cave | stacked
    status: str = 'PORTED'     # PORTED | UNPORTED | CONFLICT
    address: int = None
    expect: bytes = None
    replace: bytes = None
    reason: str = None
    evidence: list = field(default_factory=list)
    relocations: list = field(default_factory=list)
    code_offsets: list = field(default_factory=list)

    def fail(self, status, reason):
        """Record the first reason; a CONFLICT outranks an earlier UNPORTED."""
        if self.status == 'PORTED':
            self.status, self.reason = status, reason
        elif status == 'CONFLICT' and self.status == 'UNPORTED':
            self.status, self.reason = status, f'{reason} (and: {self.reason})'

    @property
    def end137(self):
        return self.patch['address'] + len(self.patch['expect'])


class Refused(Exception):
    pass


def _load_build():
    spec = importlib.util.spec_from_file_location('fw_build', FRAMEWORK / 'build.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def is_fill(b):
    return b == bytes(len(b)) or (len(b) % 2 == 0 and b == b'\x70\x47' * (len(b) // 2))


class Porter:
    def __init__(self, source_raw, target_raw, manifest=MANIFEST):
        self.src = Firmware(source_raw)
        self.dst = Firmware(target_raw)
        if self.src.version != SOURCE_VERSION:
            raise ValueError(f'source must be the official {SOURCE_VERSION} image')
        build = _load_build()
        patches = build.load_manifest(manifest)
        if any(p['kind'] != 'module' for p in patches):
            raise ValueError('only module patches can be ported')
        owner = {name: f for f, (names, _) in FEATURES.items() for name in names}
        missing = [p['name'] for p in patches if p['name'] not in owner]
        if missing:
            raise ValueError(f'FEATURES does not cover {missing}')
        patched, _ = build.apply_patches(self.src.raw, patches)
        self.patched = Firmware(patched)
        self.ports = []
        for p in patches:
            self.ports.append(Port(p, owner[p['name']], self._role(p)))
        self.evidence = {}
        self._located = {}
        self._code = self._traverse()

    # -- classification ---------------------------------------------------

    def _role(self, p):
        if p['replace'] == p['expect']:
            return 'noop'
        if self._container(p['module'], p['address'], len(p['expect'])):
            return 'stacked'
        if is_fill(p['expect']):
            return 'cave'
        return 'data' if p['name'] in DATA_PATCHES else 'code'

    def _container(self, module, addr, n=1, skip=None):
        """The earliest non-stacked port whose V137 range holds [addr, addr+n)
        in a module that `module`'s code can see."""
        for q in self.ports:
            p = q.patch
            if q is not skip and q.role != 'stacked' and p['module'] in (module, 0) \
                    and p['address'] <= addr and addr + n <= q.end137:
                return q
        return None

    def _traverse(self):
        """Instruction starts inside the patch set, by following control
        flow through the fully patched V137 image from each in-place hook.
        Bytes no instruction reaches are data (literals, tables, padding)."""
        seen, work = {}, [(q.patch['module'], q.patch['address'], 0)
                          for q in self.ports if q.role == 'code']
        while work:
            m, a, it = work.pop()
            q = self._container(m, a)
            if q is None or (q.patch['module'], a) in seen:
                continue
            m = q.patch['module']
            ins = self.patched.seg(m, 'code').insn_at(a)
            seen[(m, a)] = ins
            cond = it > 0
            nit = ins.ref if ins.op == 'it' else max(0, it - 1)
            if ins.op in ('tbb', 'tbh'):
                raise ValueError(f'{q.patch["name"]}: table branch in a replacement')
            succ = []
            if ins.op in BRANCHES:
                tm = self.src.code_module(m, ins.ref)
                if tm is not None:
                    succ.append((tm, ins.ref, 0))
            if cond or ins.op not in ('ret', 'b', 'b.w'):
                succ.append((m, a + ins.size, nit))
            work.extend(succ)
        return seen

    # -- locating ---------------------------------------------------------

    def locate(self, site, n=2):
        key = (site, n)
        if key not in self._located:
            self._located[key] = locate(self.src, self.dst, site, n)
        return self._located[key]

    def _note(self, feature, value, target, where):
        self.evidence.setdefault(feature, {}).setdefault(value, {}).setdefault(target, []).append(where)

    def _note_hit(self, feature, site, hit, why):
        """Correspondences inside a window matched for the feature itself
        (its patch sites and its unchanged routines): primary evidence."""
        for v, w, where in hit_evidence(self.src, self.dst, site, hit):
            self._note(feature, v, w, f'{where} (m{site.module}, {why})')

    def map_code(self, addr, module, feature, n=2):
        """Target address of a V137 code address (branch or PC-relative
        load target) seen from `module`."""
        q = self._container(module, addr)
        if q is not None:
            if q.address is None:
                raise Refused(f'needs {q.patch["name"]}, which did not port')
            return q.address + addr - q.patch['address'], f'inside {q.patch["name"]}'
        tm = self.src.code_module(module, addr)
        if tm is None:
            raise Refused(f'{addr:#x} is not code visible from module {module}')
        r = self.locate(Site(tm, 'code', addr), n)
        if not isinstance(r, Hit):
            raise Refused(f'{addr:#x}: {type(r).__name__}: {r.reason}')
        seen = self.evidence.get(feature, {}).get(addr, {})
        if set(seen) - {r.address}:
            raise Refused(f'{addr:#x} located at {r.address:#x} but the feature\'s matched '
                          f'stock code calls {sorted(hex(x) for x in seen)}')
        how = f'located m{tm} {addr:#x} -> {r.address:#x}'
        if seen:
            how += f'; agrees with {len(seen[r.address])} matched stock call(s)'
        return r.address, how

    def map_value(self, value, module, feature):
        """Target value of an absolute address constant. First choice: the
        same constant at a corresponding instruction in code matched for the
        feature. Else every other located stock reference, which must agree.
        Code addresses with no such reference go through Locate. Never guessed."""
        thumb, addr = value & 1, value & ~1
        q = self._container(module, addr)
        if q is not None:
            if q.address is None:
                raise Refused(f'needs {q.patch["name"]}, which did not port')
            return q.address + addr - q.patch['address'] | thumb, f'inside {q.patch["name"]}'
        primary = self.evidence.get(feature, {}).get(value, {})
        if len(primary) > 1:
            raise Refused(f'constant {value:#x}: the feature\'s matched stock code disagrees: '
                          + '; '.join(f'{w:#x} by {v[0]}' for w, v in primary.items()))
        overlay = module if module and self.src.seg(module, 'code').holds(addr) else None
        pools = self._pool_slots(value, overlay)
        votes = {}
        for sm, slot in pools:
            r = self.locate(Site(sm, 'code', slot), 4)
            if isinstance(r, Hit):
                w = u32(self.dst.seg(sm, 'code').data, r.address - self.dst.seg(sm, 'code').exec)
                votes.setdefault(w, []).append(f'pool m{sm} {slot:#x} -> {r.address:#x}')
        if primary:
            (w, how), = primary.items()
            others = sum(len(v) for k, v in votes.items() if k != w)
            note = (f'{len(how)} matched stock reference(s) of the feature read {w:#x} ({how[0]}); '
                    f'{len(votes.get(w, ()))} of {len(pools)} other V137 references located and agree')
            if others:
                k, v = next((k, v) for k, v in votes.items() if k != w)
                note += f', {others} read another value ({k:#x} by {v[0]})'
            return w, note
        if not votes and self.src.code_module(module, addr) is not None:
            got, how = self.map_code(addr, module, feature)
            return got | thumb, how
        if len(votes) > 1:
            raise Refused(f'constant {value:#x}: located references disagree: '
                          + '; '.join(f'{w:#x} by {v[0]}' for w, v in votes.items()))
        if not votes:
            raise Refused(f'constant {value:#x}: no located stock reference '
                          f'({len(pools)} V137 pool slot(s), none found in the target)')
        (w, how), = votes.items()
        return w, (f'{len(how)} of {len(pools)} V137 pool slot(s) located, all read {w:#x} '
                   f'(first: {how[0]})')

    def _pool_slots(self, value, overlay):
        """V137 code words equal to `value`: in the overlay itself when the
        value is an overlay address, else anywhere."""
        mods = [overlay] if overlay is not None else range(len(self.src.image.modules))
        pat, out = struct.pack('<I', value), []
        for m in mods:
            s = self.src.seg(m, 'code')
            j = s.data.find(pat)
            while j >= 0:
                if (s.exec + j) % 4 == 0:
                    out.append((m, s.exec + j))
                j = s.data.find(pat, j + 1)
        return out

    # -- phases -------------------------------------------------------------

    def run(self):
        for q in self.ports:
            if q.role != 'stacked':
                self._place(q)
        self._check_routines()
        for q in self.ports:
            if q.role == 'stacked':
                self._place_stacked(q)
            if q.status == 'PORTED':
                self._relocate(q)
        self._close_features()
        return self

    def _place(self, q):
        p = q.patch
        n = len(p['expect'])
        site = Site(p['module'], p['region'], p['address'])
        r = self.locate(site, n)
        if not isinstance(r, Hit):
            return q.fail('UNPORTED', f'site {type(r).__name__.lower()}: {r.reason}')
        D = self.dst.seg(p['module'], p['region'])
        found = D.data[r.address - D.exec:r.address - D.exec + n]
        q.address, q.expect = r.address, found
        self._note_hit(q.feature, site, r, f'{p["name"]} site')
        q.evidence.append(f'site located by a {r.hi - r.lo}-byte masked window '
                          f'[{r.lo:#x}, {r.hi:#x}) -> {r.address:#x}')
        if q.role == 'noop':
            q.replace = found
            q.evidence.append('no-op fixture: replace equals the target bytes')
        elif q.role == 'data' and found != p['expect']:
            q.fail('CONFLICT', f'stock data changed: V137 {p["expect"].hex()}, target {found.hex()}')
        elif q.role == 'cave':
            self._prove_cave(q, D)

    def _prove_cave(self, q, D):
        p = q.patch
        n, a = len(p['expect']), q.address
        if q.expect != p['expect']:
            return q.fail('UNPORTED', f'cave bytes differ: {q.expect.hex()}')
        refs = self.dst.refs_into(p['module'], a, a + n)
        if refs:
            r = refs[0]
            return q.fail('UNPORTED', f'cave referenced: {r[2]} at {r[3]:#x} (m{r[1]}) -> {r[0]:#x}')
        # Module 35's data record overlaps module 0's code on paper in every
        # image (a payload read by service call), so judge overlaps against
        # what the V137 cave already had.
        def overlapping(fw, lo, hi):
            return {m for m in range(len(fw.image.modules)) if m != p['module']
                    and any(s < hi and lo < e for s, e in fw.spans(m))}
        old = overlapping(self.src, p['address'], q.end137)
        new = overlapping(self.dst, a, a + n) - old
        if new:
            return q.fail('UNPORTED', f'cave newly overlaps modules {sorted(new)}')
        proof = (f'cave proof: {n} fill bytes inside module {p["module"]} {p["region"]} '
                 f'[{D.exec:#x}, {D.end:#x}), no reference into [{a:#x}, {a + n:#x}) '
                 f'from any co-resident module, no module mapped over it that V137 did not '
                 f'already have{f" (on paper: {sorted(old)})" if old else ""}')
        if p['expect'] == bytes(n):
            # Zero fill can be a buffer the stock code addresses from below;
            # keep at least the clearance V137 had.
            S = self.src.seg(p['module'], p['region'])
            below_src = self.src.nearest_ref_below(p['module'], p['address'], S.exec)
            below_dst = self.dst.nearest_ref_below(p['module'], a, D.exec)
            gap_src = p['address'] - (below_src if below_src is not None else S.exec)
            gap_dst = a - (below_dst if below_dst is not None else D.exec)
            if gap_dst < gap_src:
                return q.fail('UNPORTED', f'zero cave clearance {gap_dst:#x} < V137 {gap_src:#x}')
            proof += f'; nearest reference below is {gap_dst:#x} bytes away (V137: {gap_src:#x})'
        q.evidence.append(proof)

    def _place_stacked(self, q):
        p = q.patch
        base = self._container(p['module'], p['address'], len(p['expect']), skip=q)
        if base.status != 'PORTED':
            return q.fail('UNPORTED', f'stacks on {base.patch["name"]}, which did not port')
        o = p['address'] - base.patch['address']
        q.address = base.address + o
        q.expect = base.replace[o:o + len(p['expect'])]
        if base.patch['replace'][o:o + len(p['expect'])] != p['expect']:
            return q.fail('UNPORTED', f'expect does not equal {base.patch["name"]} output')
        q.evidence.append(f'stacks on {base.patch["name"]} at +{o:#x}')

    def _check_routines(self):
        self.routines = {}
        for feature, (_, routines) in FEATURES.items():
            problems = []
            for module, start, label, *length in routines:
                end = start + length[0] if length else routine_extent(self.src.seg(module, 'code'), start)
                if end is None:
                    raise ValueError(f'{label}: no routine extent at {start:#x}')
                r = self.locate(Site(module, 'code', start), end - start)
                entry = {'module': module, 'v137': [hex(start), hex(end)], 'label': label}
                if length and isinstance(r, Hit) and self._bytes(self.dst, module, r.address, end - start) \
                        != self._bytes(self.src, module, start, end - start):
                    r = Missing('data differs under the mask only')
                if length and not isinstance(r, Hit):
                    entry['status'] = 'changed'
                    entry['difference'] = self._data_difference(module, start, end)
                    problems.append(f'{label} ({start:#x}, {end - start} bytes): {entry["difference"]}')
                elif isinstance(r, Hit):
                    entry['target'] = hex(r.address)
                    self._note_hit(feature, Site(module, 'code', start), r, label)
                    bad = self._pool_diff(feature, module, start, end, r.address)
                    if bad:
                        problems.append(f'{label} ({start:#x}) literal changed: {bad}')
                        entry['status'] = 'changed'
                    else:
                        entry['status'] = 'same'
                else:
                    entry['status'] = 'changed' if isinstance(r, Missing) else 'ambiguous'
                    at, why = self._target_entry(module, start, end)
                    if at is not None:
                        entry['target'] = hex(at)
                        entry['masked_sha256'] = masked_body_sha(self.dst, module, at)
                        why = self._first_difference(module, start, end, at)
                        reviewed = REVIEWED.get((feature, start), {}).get(entry['masked_sha256'])
                        if reviewed:
                            entry['status'] = 'reviewed'
                            entry['reviewed'] = reviewed
                    entry['difference'] = why
                    if entry['status'] != 'reviewed':
                        problems.append(f'{label} ({start:#x}, {end - start} bytes): {why}')
                self.routines.setdefault(feature, []).append(entry)
            for q in self.ports:
                if q.feature == feature:
                    for e in self.routines.get(feature, ()):
                        if e['status'] == 'same':
                            q.evidence.append(f'routine {e["label"]} m{e["module"]} {e["v137"][0]}'
                                              f' masked body unchanged at {e["target"]}')
                        elif e['status'] == 'reviewed':
                            q.evidence.append(f'routine {e["label"]} m{e["module"]} {e["v137"][0]}'
                                              f' at {e["target"]} differs ({e["difference"]}); '
                                              f'reviewed: {e["reviewed"]}')
                    if problems:
                        q.fail('CONFLICT', 'stock code or data differs: ' + '; '.join(problems))

    def _target_entry(self, module, start, end):
        """(entry, None) for a changed routine whose entry the target still
        has, found from the first 16-byte piece of it that locates; else
        (None, why)."""
        S, D = self.src.seg(module, 'code'), self.dst.seg(module, 'code')
        for probe in S.insns_in(start, end - 16):
            r = self.locate(Site(module, 'code', probe.addr), 16)
            if not isinstance(r, Hit):
                continue
            entry = r.address - (probe.addr - start)
            first = S.insn_at(start)
            o, t = start - S.exec, entry - D.exec
            same = D.holds(entry, first.size) and not any(
                (x ^ y) & k for x, y, k in zip(S.data[o:o + first.size], D.data[t:t + first.size],
                                               S.mask[o:o + first.size]))
            if same and routine_extent(D, entry):
                return entry, None
            return None, (f'entry not found: the piece at +{probe.addr - start:#x} locates to '
                          f'{r.address:#x} but the code before it differs')
        return None, 'no 16-byte piece of the routine locates in the target'
    @staticmethod
    def _bytes(fw, module, addr, n):
        seg = fw.seg(module, 'code')
        return seg.data[addr - seg.exec:addr - seg.exec + n]

    def _data_difference(self, module, start, end):
        """First difference of a changed data block, aligned by whichever
        of its patches the target located (the block's own rows are
        compared byte for byte)."""
        for q in self.ports:
            p = q.patch
            if q.address is not None and p['module'] == module and start <= p['address'] < end:
                base = q.address - (p['address'] - start)
                old, new = self._bytes(self.src, module, start, end - start), \
                    self._bytes(self.dst, module, base, end - start)
                diff = [o for o in range(end - start) if old[o] != new[o]]
                if not diff:
                    return f'block at {base:#x} matches, but it is not the only match'
                return (f'block at {base:#x} differs in {len(diff)} byte(s), first at +{diff[0]:#x}: '
                        f'V137 {old[diff[0] & ~3:(diff[0] & ~3) + 4].hex()}, '
                        f'target {new[diff[0] & ~3:(diff[0] & ~3) + 4].hex()}')
        return 'no patch of the block located in the target'

    def _first_difference(self, module, start, end, entry):
        """Where a changed routine first differs from V137 under the mask."""
        S, D = self.src.seg(module, 'code'), self.dst.seg(module, 'code')
        for ins in S.insns_in(start, end):
            o, t = ins.addr - S.exec, ins.addr - start + entry - D.exec
            a, b, m = S.data[o:o + ins.size], D.data[t:t + ins.size], S.mask[o:o + ins.size]
            if any((x ^ y) & k for x, y, k in zip(a, b, m)):
                return (f'entry at {entry:#x}; first difference at +{ins.addr - start:#x}: '
                        f'V137 {a.hex()}, target {b.hex()}')
        return f'entry at {entry:#x}; body matches but its end or literals differ'

    def _pool_diff(self, feature, module, start, end, addr):
        """Literal words a routine loads must be the same constant, or an
        address in both images (relocated, recorded as evidence)."""
        S, D = self.src.seg(module, 'code'), self.dst.seg(module, 'code')
        delta = addr - start
        for ins in S.insns_in(start, end):
            if ins.op != 'ldr':
                continue
            t = D.insn_at(ins.addr + delta)
            if not (S.holds(ins.ref & ~3, 4) and D.holds(t.ref & ~3, 4)):
                continue
            v, w = u32(S.data, (ins.ref & ~3) - S.exec), u32(D.data, (t.ref & ~3) - D.exec)
            if in_reloc(v) and in_reloc(w):
                self._note(feature, v, w, f'literal of ldr at {ins.addr:#x} (m{module})')
            elif v != w:
                return f'ldr at {ins.addr:#x} loads {w:#x}, V137 {v:#x}'
        return None

    def _relocate(self, q):
        if q.role == 'noop':
            return
        try:
            q.replace = self._relocated(q)
        except Refused as e:
            q.fail('UNPORTED', str(e))

    def _relocated(self, q):
        p = q.patch
        a137, n, delta = p['address'], len(p['replace']), q.address - p['address']
        out = bytearray(p['replace'])
        code = sorted(a for (m, a) in self._code if m == p['module'] and a137 <= a < a137 + n
                      and self._container(m, a) is self._container(p['module'], a137))
        if q.role == 'data' and code:
            raise Refused('control flow reaches a data patch')
        covered = set()
        pending = {}
        for a in code:
            ins = decode(p['replace'], a - a137, a)
            o = a - a137
            if o + ins.size > n:
                raise Refused(f'instruction at {a:#x} straddles the patch end')
            q.code_offsets.append(o)
            covered.update(range(o, o + ins.size))
            raw = p['replace'][o:o + ins.size]
            if ins.op in PCREL:
                inside = a137 <= ins.ref < a137 + n
                if inside:
                    new, how = ins.ref + delta, 'inside this patch'
                elif ins.op in BRANCHES:
                    new, how = self.map_code(ins.ref, p['module'], q.feature)
                else:
                    new, how = self.map_code(ins.ref, p['module'], q.feature, 4)
                enc = encode(ins, raw, a + delta, new)
                if enc is None:
                    raise Refused(f'{ins.op} at {a:#x} cannot reach {new:#x} from {a + delta:#x}')
                out[o:o + ins.size] = enc
                if not inside:
                    q.relocations.append({'offset': o, 'kind': ins.op, 'v137': hex(ins.ref),
                                          'target': hex(new), 'evidence': how})
            elif ins.op == 'movw':
                pending[ins.rd] = (o, ins, raw)
            elif ins.op == 'movt' and ins.rd in pending:
                lo_o, lo_ins, lo_raw = pending.pop(ins.rd)
                value = ins.ref << 16 | lo_ins.ref
                if in_reloc(value):
                    new, how = self.map_value(value, p['module'], q.feature)
                    out[lo_o:lo_o + 4] = encode(lo_ins, lo_raw, 0, new & 0xFFFF)
                    out[o:o + 4] = encode(ins, raw, 0, new >> 16)
                    q.relocations.append({'offset': lo_o, 'movt_offset': o, 'kind': 'movw/movt',
                                          'v137': hex(value), 'target': hex(new), 'evidence': how})
        for o in range((-a137) % 4, n - 3, 4):
            if covered.isdisjoint(range(o, o + 4)):
                v = u32(p['replace'], o)
                if in_reloc(v):
                    new, how = self.map_value(v, p['module'], q.feature)
                    struct.pack_into('<I', out, o, new)
                    q.relocations.append({'offset': o, 'kind': 'word', 'v137': hex(v),
                                          'target': hex(new), 'evidence': how})
        if q.role == 'code':
            # An in-place edit must leave every stock instruction it keeps
            # pointing where the matched stock instruction points.
            self._check_kept(q, out)
        return bytes(out)

    def _check_kept(self, q, out):
        p = q.patch
        S = self.src.seg(p['module'], p['region'])
        delta = q.address - p['address']
        for o in q.code_offsets:
            a = p['address'] + o
            ins = decode(p['replace'], o, a)
            old = S.insn_at(a)
            if ins.op in PCREL and old.op == ins.op and old.ref == ins.ref \
                    and p['expect'][o:o + ins.size] == p['replace'][o:o + ins.size]:
                t = decode(q.expect, o, a + delta)
                mine = decode(bytes(out), o, a + delta)
                if t.ref != mine.ref:
                    raise Refused(f'kept {ins.op} at {a:#x}: stock now points at {t.ref:#x}, '
                                  f'relocation gave {mine.ref:#x}')

    def _close_features(self):
        for feature in FEATURES:
            members = [q for q in self.ports if q.feature == feature]
            bad = [q for q in members if q.status != 'PORTED']
            for q in members:
                if q.status == 'PORTED' and bad:
                    worst = 'CONFLICT' if any(b.status == 'CONFLICT' for b in bad) else 'UNPORTED'
                    q.fail(worst, f'feature {feature} ports whole or not at all: '
                           + ', '.join(f'{b.patch["name"]} is {b.status}' for b in bad))
                if q.status != 'PORTED':
                    q.replace = None

    # -- transplants --------------------------------------------------------

    def transplants(self, names):
        out = []
        for name in names:
            if name != 'vorbis75':
                out.append({'name': name, 'status': 'UNPORTED', 'reason': 'no port rule'})
                continue
            same, ev = [], []
            for region in ('code', 'data'):
                s, d = self.src.seg(75, region), self.dst.seg(75, region)
                same.append(s.exec == d.exec and s.data == d.data)
                ev.append(f'module 75 {region} {d.exec:#x}+{len(d.data):#x} '
                          f'sha256 {hashlib.sha256(d.data).hexdigest()[:16]}')
            m137, mdst = self.src.image.modules[75], self.dst.image.modules[75]
            same.append(m137['bss_exec'] == mdst['bss_exec'] and m137['bss_len'] == mdst['bss_len'])
            if all(same):
                out.append({'name': name, 'status': 'PORTED', 'evidence':
                            ev + ['module 75 record, code and data byte-identical to V137; '
                                  'transplant.py resolves file offsets through the target module table']})
            else:
                out.append({'name': name, 'status': 'UNPORTED',
                            'reason': 'module 75 differs from V137', 'evidence': ev})
        return out


# ---------------------------------------------------------------- output

def _wrap(key, text, width=76):
    words, lines, line = text.split(), [], f'{key}:'
    for w in words:
        if len(line) + 1 + len(w) > width and line.strip():
            lines.append(line)
            line = ' '
        line += ' ' + w
    lines.append(line)
    return '\n'.join(lines)


def patch_text(q, porter):
    p, dst = q.patch, porter.dst
    proof = '; '.join(q.evidence + [f'{r["kind"]} at +{r["offset"]:#x}: {r["v137"]} -> '
                                    f'{r["target"]} ({r["evidence"]})' for r in q.relocations])
    return '\n'.join([
        f'# Ported by tools/port_patches.py from {SOURCE_VERSION} {p["file"]}. Generated:',
        '# rerun the tool instead of editing. Evidence: port_report.json.',
        f'name: {p["name"]}',
        'kind: module',
        f'module: {p["module"]}',
        f'region: {p["region"]}',
        f'address: {q.address:#010x}',
        f'base_sha256: {dst.sha256}',
        f'ported_from: {SOURCE_VERSION} {p["file"]} address {p["address"]:#010x}',
        _wrap('gate', f'build refuses unless the input SHA-256 equals base_sha256 '
                      f'({dst.version}) and the bytes at the target equal `expect`; the '
                      'finished image must pass the build validator'),
        _wrap('rationale', f'{p["rationale"]} Port to {dst.version}: {proof}.'),
        f'expect: {q.expect.hex()}',
        f'replace: {q.replace.hex()}',
        '',
    ])


def report(porter, transplants):
    def row(q):
        p = q.patch
        r = {'file': p['file'], 'name': p['name'], 'feature': q.feature, 'role': q.role,
             'status': q.status, 'module': p['module'], 'region': p['region'],
             'v137_address': hex(p['address']), 'length': len(p['expect']),
             'target_address': hex(q.address) if q.address is not None else None,
             'evidence': q.evidence}
        if q.reason:
            r['reason'] = q.reason
        if q.status == 'PORTED':
            r['relocations'] = q.relocations
            r['code_offsets'] = q.code_offsets
        return r
    rows = [row(q) for q in porter.ports]
    counts = {s: sum(r['status'] == s for r in rows) for s in ('PORTED', 'UNPORTED', 'CONFLICT')}
    return {
        'tool': 'tools/port_patches.py',
        'source': {'version': SOURCE_VERSION, 'sha256': porter.src.sha256},
        'target': {'version': porter.dst.version, 'sha256': porter.dst.sha256,
                   'header_date': OFFICIAL[porter.dst.sha256][1]},
        'summary': counts,
        'patches': rows,
        'transplants': transplants,
        'routines': porter.routines,
        'scope': 'offline evidence only; no ported image has run on hardware',
    }


def readme(rep):
    t = rep['target']
    lines = [f'# Ported patches for {t["version"]}', '',
             f'Generated by `tools/port_patches.py` from the {rep["source"]["version"]} manifest '
             f'(`patches/framework/patches/`) against the official {t["version"]} image '
             f'(SHA-256 `{t["sha256"]}`). Do not edit these files; rerun the tool. '
             'Build with `patches/framework/build.py --base '
             f'{t["version"]} --input DP3_{t["version"]}.img --output OUT.img`, which applies '
             '`manifest.txt` and `transplants.txt` from this directory and lists every '
             'patch that did not port in its build report.', '',
             f'{rep["summary"]["PORTED"]} ported, {rep["summary"]["UNPORTED"]} unported, '
             f'{rep["summary"]["CONFLICT"]} in conflict. Full evidence: `port_report.json`. '
             'Offline evidence only: none of this has run on hardware.', '',
             f'| Patch | Status | V137 -> {t["version"]} | Evidence or reason |',
             '| --- | --- | --- | --- |']
    for r in rep['patches']:
        where = f'`{r["v137_address"]}` -> `{r["target_address"]}`' if r['target_address'] \
            else f'`{r["v137_address"]}` -> none'
        routines = rep['routines'].get(r['feature'], ())
        changed = [e['label'] for e in routines if e['status'] in ('changed', 'ambiguous')]
        if r['status'] == 'CONFLICT' and changed:
            why = 'stock code or data changed in the target: ' + ', '.join(changed)
        else:
            why = r.get('reason') or _summary(r, routines)
        lines.append(f'| {r["file"]} | {r["status"]} | {where} | {why.replace("|", "/")} |')
    for tr in rep['transplants']:
        why = tr.get('reason') or tr['evidence'][-1]
        lines.append(f'| transplant {tr["name"]} | {tr["status"]} | module 75 | {why} |')
    return '\n'.join(lines) + '\n'


def _summary(r, routines):
    bits = [r['role']]
    rel = r.get('relocations') or []
    if rel:
        bits.append(f'{len(rel)} relocation(s)')
    if any(e.startswith('cave proof') for e in r['evidence']):
        bits.append('free-space proof')
    same = sum(e['status'] == 'same' for e in routines)
    reviewed = [e['label'] for e in routines if e['status'] == 'reviewed']
    if same:
        bits.append(f'{same} routine(s) unchanged')
    if reviewed:
        bits.append('reviewed change in ' + ', '.join(reviewed))
    return ', '.join(bits)


def render(source_raw, target_raw):
    """(version, {relative path: text}) for patches/ported/<VERSION>/.
    Only an official target (tools/official_images.py) gets a version."""
    porter = Porter(source_raw, target_raw)
    if porter.dst.version is None:
        raise ValueError(f'target SHA-256 {porter.dst.sha256} is not an official image')
    porter.run()
    tr = porter.transplants(_load_build().load_transplant_names(TRANSPLANTS))
    rep = report(porter, tr)
    files = {q.patch['file']: patch_text(q, porter) for q in porter.ports if q.status == 'PORTED'}
    files['manifest.txt'] = ''.join(f'{q.patch["file"]}\n' for q in porter.ports if q.status == 'PORTED')
    files['transplants.txt'] = ''.join(f'{t["name"]}\n' for t in tr if t['status'] == 'PORTED')
    files['port_report.json'] = json.dumps(rep, indent=2) + '\n'
    files['README.md'] = readme(rep)
    return porter.dst.version, files


def write(version, files, root=PORTED):
    out = root / version
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.patch'):
        if old.name not in files:
            old.unlink()
    for name, text in files.items():
        (out / name).write_text(text)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', type=Path, default=REPO / 'DP3_V137.img')
    ap.add_argument('--target', type=Path, required=True, action='append',
                    help='official image to port to (repeatable)')
    ap.add_argument('--out', type=Path, default=PORTED)
    ap.add_argument('--check', action='store_true',
                    help='compare with the files under --out instead of writing')
    a = ap.parse_args()
    source = a.source.read_bytes()
    stale = 0
    for path in a.target:
        version, files = render(source, path.read_bytes())
        rep = json.loads(files['port_report.json'])
        if a.check:
            for name, text in files.items():
                f = a.out / version / name
                if not f.exists() or f.read_text() != text:
                    print(f'STALE {f}')
                    stale += 1
        else:
            print(f'wrote {write(version, files, a.out)}')
        print(f'{version}: ' + ', '.join(f'{k} {v}' for k, v in rep['summary'].items()))
        for r in rep['patches']:
            print(f'  {r["status"]:8} {r["file"]:38} {r["v137_address"]:>10} -> '
                  f'{r["target_address"] or "-":>10}  {r.get("reason", "")[:110]}')
    return 1 if stale else 0


if __name__ == '__main__':
    sys.exit(main())
