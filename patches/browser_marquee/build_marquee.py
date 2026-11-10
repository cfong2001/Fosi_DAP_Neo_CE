#!/usr/bin/env python3
"""Browser dwell-scroll metadata display (experimental variant).

Builds the module 31 growth payload for the marquee feature, the
hook patches and the variant manifest:

  marquee_payload.bin   code + state + compose buffer, loaded by
                        build.py as the module 31 code growth
  0300-marquee-painter-tail-gate.patch
                        BL at the browser painter's tail test site
                        (0x0307ECA0) rerouted to mq_gate
  0301-marquee-key-reset.patch
                        B.W at the browser Key callback entry
                        (0x0307E5B8) rerouted to mq_key
  0302-marquee-exit-reset.patch
                        B.W at the browser exit callback (0x0307D776)
                        rerouted to mq_exit
  0303-marquee-view-toggle.patch
                        BL inside the browser Key handler, after the
                        event word is final (0x0307E5E6, displacing
                        the ldr.w of the local context pointer),
                        rerouted to mq_toggle
  0310-marquee-fill-mode-a-band.patch
                        BL at the mode A row loop's band fill call
                        (0x0307EA30) rerouted to mq_fillsub
  0311-marquee-fill-mode-a-accent.patch
                        BL at the mode A selected band fill call
                        (0x0307EA72) rerouted to mq_fillsub
  0312-marquee-fill-mode-a-separator.patch
                        BL at the mode A separator fill call
                        (0x0307EA94) rerouted to mq_fillsub
  0313-marquee-fill-mode-b-accent.patch
                        BL at the mode B selected band fill call
                        (0x0307EBDC) rerouted to mq_fillsub
  0314-marquee-fill-window-ground.patch
                        BL at the paint framework's window ground
                        fill call (0x0306358C, module 0) rerouted
                        to mq_fillsub
  0315-marquee-fill-stepper-erase.patch
                        BL at the marquee stepper's text-rect erase
                        call (0x03063024, module 0) rerouted to
                        mq_fillsub
  manifest.txt          default 32 + the ten hooks above

Design and evidence: patches/browser_marquee/design.md. Stock already
scrolls a wide selected name through the module 0 marquee engine
(registrar 0x0306302A, stepper 0x03062F54, context 0x03023888) with a
30-tick step interval and no dwell. This variant adds a 100-tick dwell
and swaps the scroll string for a composed metadata string. Files
with usable tags scroll ARTIST - TITLE (plus - ALBUM) parsed by the
firmware's own tag dispatcher (module 0 FUN_0306C51C, the entry the
library scan and the playback open path call); everything else
scrolls the v1 name / format / size string built from the browser
node's own FAT dirent copy. The stepper, the erase and the text draw
stay stock.

v3: the tag string is uncapped (each field is carried in full, up to
its 127-unit struct bound, so an entry buffer holds the worst case
3 x 127 + 2 x 3 + NUL = 388 units), and a long press of Vol+ toggles
the browser between the tag view and the file view for the rest of
the session (payload state only; reset on window exit). The v3
design section in design.md carries the key census behind the
choice and the cover-thumbnail feasibility verdict.

v4: the cover thumbnail (superseded by v5; the v4 variant stays
as built then). At dwell expiry the payload located the selected
file's embedded picture with the firmware's own picture pipeline
(the module 18 scan body for MP3, the locator's own case heads
for FLAC, APE and WAV, all handle-direct), decoded it once at a
36x36 target through module 18's setup and painter consumer, and
cached the produced raster in the payload, shifting the selected
row's text right while the thumbnail was active. OGG is not
covered: its locator case reaches the picture only through a
temp-file extraction in module 0 that closes the registered
picture handle, which is not handle-direct (probe evidence in
design.md).

v5: one full-screen background, and the enriched label. The
selected row's displayed string is one metadata-enriched label
from the selecting paint onward: TITLE, then ARTIST (with the
album-artist fallback), then ALBUM; when the title is absent the
FILE NAME leads and the artist still never leads; the file view
keeps the v1 composed string. The label is installed by the
payload's own render over the stock name the row loop drew (the
gate runs at the painter tail, after the row loop, so no earlier
hook can supply the string). Rows draw no pictures and keep the
stock layout. Instead, the selected file's cover renders behind
the whole browser client area (0,40) to (239,319), darkened at
capture for legibility: the decode runs in the selecting paint
through the v4 direct route, samples the produced image's
centre crop into a single background store at reduced
resolution in RGB565, mixing each pixel 55 percent toward
black (dark theme) or 75 percent toward the paper colour
[242, 237, 230] (light theme), the theater finalize mixes.
One store, keyed by the selected node's identity; reselecting
the same node is free, and selecting a folder or a
picture-less or unsupported file restores the stock ground.
While the background is installed, hooks on the painter's fill
call sites (the row band, selection band and separator fills
in module 31, the window ground fill and the marquee stepper's
erase in module 0) substitute the matching slice of the stored
background for the flat colour, the selection band's slice
mixed halfway toward the accent, so no flat fill creeps back
over the art. The v4 thumbnail hooks (0304 to 0309) are gone.

The payload lives at the module 31 code growth base 0x0307EE48 (the
same window the M3U composition uses; in this standalone variant it
is the only occupant). State is payload-resident (transient UI
state, never SAVEINFO): node pointer, dwell stamp, phase, view mode,
the composed string buffer, the 0x556-byte tag struct the dispatcher
fills, and a two entry tag cache keyed by node. The background store
shares the tag struct's reservation: the struct is scratch for a
parse at the selecting paint and for the open name-out inside a
decode, and the store is written by the decode later in the same
paint, after the parse's contents have been composed into the tag
cache. Overwrites happen only inside the gate, between the row
loop and mq_show's repaint at the gate exit, so no paint ever
reads a half-overwritten store. The slice routines build each
output row in a line buffer in the package-gap tail (the census
home), never in the store's own span.
"""
import hashlib
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(REPO / 'patches' / 'framework'))

from keystone import (Ks, KS_ARCH_ARM, KS_MODE_THUMB,       # noqa: E402
                      KS_MODE_V8)
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB          # noqa: E402
from rknano_image import Image                               # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'

BASE = 0x0307EE48              # module 31 code growth base
STATE_LEN = 52                 # payload state (background fields
                               # at +0x19..+0x2E, see below)
BUF_UNITS = 68                 # 48 name + up to 19 suffix + NUL
NAME_CAP = 48
DWELL_TICKS = 100              # 1.0 s at the proven 10 ms tick (chosen)

# Tag support (v2, uncapped in v3). The field-length routine takes
# a cap; v3 passes the dispatcher struct's own field bound, 127
# units, for every field, so the composed tag string carries the
# full title, artist and album as parsed. Worst case string:
# 127 + 3 + 127 + 3 + 127 + NUL = 388 units.
ARTIST_CAP = 127
TITLE_CAP = 127
ALBUM_CAP = 127
TAG_BUF_UNITS = 192            # tag string buffer, units incl.
                               # NUL (v2 to v4: 388; v5 spends the
                               # difference on the window key table
                               # and the larger code, and field_put
                               # enforces the bound)
TAG_STRUCT_LEN = 0x556         # dispatcher output struct (stock size)
CACHE_ENTRIES = 2              # two entries (was four in v3; the
                               # union background store took the
                               # freed span in v4 and keeps it)
CACHE_ENTRY_LEN = 20 + TAG_BUF_UNITS * 2   # key 16 + flags 4 + buf

# Background store (v5). One darkened cover for the selected
# node, held in the span the tag struct uses as parse scratch
# (the union discipline is in the module docstring). The store
# is raw RGB565 at BG_W x BG_H, sized to the client area's
# aspect (240 x 280, 6:7) and to what the payload window holds
# after code: the census homes are this window and the
# package-gap tail (2,044 B at 0x0307BFB4, delivered with
# build.py --tail); the tail carries the slice line buffer
# (240 halfwords) as scratch, the store lives in the window.
# At 2 bytes per pixel: 36 x 42 = 1,512 px = 3,024 B.
BG_W = 30
BG_H = 35
BG_BYTES = BG_W * BG_H * 2
BG_BOX = 56                    # pipeline decode box (square)
ART_X0 = 0                     # client area: (0, 40) to
ART_Y0 = 40                    # (239, 319), 240 x 280
ART_W = 240
ART_H = 280
TAIL_BASE = 0x0307BFB4         # gap-tail arena (framework --tail)
TAIL_LEN = 2044
LINEBUF = TAIL_BASE            # slice line scratch, 480 B
# The single background key entry (node, directory cluster,
# file cluster, ordinal, slot pad, result): the one-entry
# discipline of the earlier key table, reduced to one entry
# because the background serves the current selection only.
KEY_ENTRIES = 1
KEY_LEN = 20
STRUCT_SPAN = max(TAG_STRUCT_LEN, BG_BYTES)
# State bytes for the background: +0x19 installed, +0x1A
# install draw pending, +0x1B ground restore pending, +0x1C
# key entry valid, +0x1D theme captured at decode (0 dark,
# 1 light), +0x20 produced width, +0x22 produced height,
# +0x24 crop width, +0x26 crop height, +0x28 crop left,
# +0x2A crop top, +0x2C next store row to capture, +0x2E
# produced rows seen. +0x2B stays the label render flag.
BG_ACTIVE = 0x19
BG_FRESH = 0x1A
BG_GONE = 0x1B
BG_VALID = 0x1C
BG_THEME = 0x1D
BG_PW = 0x20
BG_PH = 0x22
BG_CW = 0x24
BG_CH = 0x26
BG_X0 = 0x28
BG_Y0 = 0x2A
LABEL_FRESH = 0x0A             # (moved off +0x2B: the BG_Y0 halfword
                               # at +0x2A spans +0x2A..+0x2B)
BG_SY = 0x2C
BG_CY = 0x2E

# View toggle (v3). The Key-handler event word for a long press of
# Vol+ (type 2, mask 0x0010). The census in design.md shows this
# event reaches the handler's default exit with no stock action in
# the browser window; every other producible long press is either
# assigned (OK) or unsafe (Power). The state byte at STATE + 0x18
# holds the view mode: 0 = tag view, 1 = file view.
TOGGLE_EVENT = 0x20000010
# Extensions the tag dispatcher handles inside module 0, minus WMA:
# its case delegates to an overlay-resident ASF parser (0x0307E134 in
# the shared window span when the mode byte at 0x03023151 is 0, else
# module 33 at 0x0308B560); neither residency holds while the browser
# window is active, so WMA files keep the v1 string.
TAG_EXTS = (b'MP1', b'MP2', b'MP3', b'AAC', b'WAV', b'APE', b'FLA',
            b'OGG', b'M4A', b'MP4', b'3GP', b'DSF')

# Stock entry points and cells (module 0 unless noted).
SET_BIT = 0x0306723C           # event post (module 27/31 code calls it)
CLEAR_BIT = 0x0306727E         # event clear
TEST_BIT = 0x0306729C          # event test, no clear
MQ_SETUP = 0x0306302A          # marquee registrar
MEASURE = 0x0306295A           # rendered string width (painter's own)
RENDER = 0x03062CEE            # row text render (painter's own)
FILL = 0x030632FA              # rect fill (painter's own)
PENSET = 0x0306316E            # draw parameter set (painter's own)
CLOCK = 0x03023298             # 100 Hz tick cell (stepper's own gate)
MCTX = 0x03023888              # marquee context
BCTX = 0x030228A8              # browser state context
LCTX = 0x03025928              # browser local context (+0xC = string)
FSOPEN = 0x030589B6            # open by (directory cluster, index)
FSCLOSE = 0x03058E8E           # close handle
TAGPARSE = 0x0306C51C          # tag dispatcher (scan/playback entry)
BZERO = 0x03054E66             # bzero(dst, len)
MODE_STR = 0x0306E828          # stock "R" mode string (module 33 too)
FSTYPE = 0x0307A024            # FS type byte cell
PAL_ACCENT = 0x030235B8        # palette accent cell (band colour)
PAL_BG = 0x030235B4            # palette cell 0 (light ground)
PAL_ACCENT3 = 0x030235B8       # the accent cell: the painter's
                               # own source for the selection
                               # band and stepper erase colour
                               # (the literal in the mode A and B
                               # loops; same cell as PAL_ACCENT)
SAVEINFO = 0x030232A0          # config block; +0x2D8 theme byte
                               # (0 dark, nonzero light)

# Picture pipeline (module 18 unless noted; v4 thumbnail).
SEEK = 0x030594A0              # stream seek (offset, whence, handle)
SCAN = 0x03082BF6              # ID3 picture scan body (handle, out)
CASE_FLA = 0x0308364E          # locator case head: FLAC
CASE_APE = 0x030834DA          # locator case head: APE
CASE_WAV = 0x0308337C          # locator case head: WAV (id3 chunk)
SETUP = 0x0308389E             # picture setup (handle, mode)
CONSUMER = 0x03083B36          # painter consumer (one row per call)
SET_D4 = 0x03083A90            # request descriptor +4 setter
SET_D8 = 0x03083A8A            # request descriptor +8 setter
BITMAP = 0x0306333E            # row blitter (consumer's own)
REQ = 0x0302598C               # request globals: box w/h, dest x/y
DESC = 0x030259D4              # request descriptor (+0 located cell)
CTX = 0x03026CA0               # picture context (+0x14/+0x18 scaled
                               # width/height, +0x28 row buffer ptr,
                               # +0x2C row cursor)
# Admitted picture routes by dirent extension: the MP3 scan body
# directly, the three locator case heads for the rest. The case
# heads share the locator dispatch's stack frame and exit through
# its epilogue; mq_loccase rebuilds that frame. OGG is absent on
# purpose (its case extracts through a temp file, not the handle);
# DSF, DFF and the MP4 family have no handle-direct picture entry;
# WMA and OPUS stay gated out as in the tag path.
PIC_ROUTES = ((b'MP3', SCAN), (b'FLA', CASE_FLA),
              (b'APE', CASE_APE), (b'WAV', CASE_WAV))
PIC_ENTRY_LEN = 8              # ext 3 + pad 1 + route word 4

GATE_SITE = 0x0307ECA0         # painter tail: bl TEST_BIT (module 31)
KEY_SITE = 0x0307E5B8          # Key callback entry (module 31)
EXIT_SITE = 0x0307D776         # exit callback: mov.w r0, #0x148 (m31)
TOGGLE_SITE = 0x0307E5E6       # Key handler: ldr.w sb, [pc] (m31);
                               # r4 holds the final event word there
FILLA_SITE = 0x0307EA30        # mode A row loop: bl FILL (band)
FILLB_SITE = 0x0307EA72        # mode A row loop: bl FILL (accent)
FILLC_SITE = 0x0307EA94        # mode A row loop: bl FILL (separator)
FILLD_SITE = 0x0307EBDC        # mode B row loop: bl FILL (accent)
FILLE_SITE = 0x0306358C        # paint framework: bl FILL (window
                               # ground, module 0)
FILLF_SITE = 0x03063024        # marquee stepper: bl FILL (text
                               # erase, module 0)

# The asm sources use {STATE} / {BUF} placeholders, filled after a
# sizing pass: literal-pool sizes do not depend on the values, so the
# code length is identical in both passes (asserted).


def routines(state, buf, xref, data=None):
    S = state
    B = buf
    if data is None:
        data = {'struct': buf + 0x1000, 'cache': buf + 0x2000,
                'exttab': buf + 0x3000, 'keytab': buf + 0x3800}
    data = dict(data)
    data.setdefault('picext', buf + 0x4000)
    data.setdefault('keytab', buf + 0x3800)
    gate = [
        # BL from GATE_SITE. r0 = 0x148 on entry (the site's own
        # argument to the displaced test). Returns the test result in
        # r0: 1 lets the stock painter tail step the marquee, 0
        # suppresses the step this paint. Preserves r4-r6.
        'mq_gate:',
        '  push {r4, r5, r6, lr}',
        f'  ldr r4, ={S}',
        '  bl {NODE}',                    # r0 = node, r1 = row
        '  cmp r0, #0',
        '  beq gate_stock',
        '  mov r5, r0',                    # node
        '  mov r6, r1',                    # row
        '  ldr r1, [r4]',
        '  cmp r1, r5',
        '  beq gate_same',
        '  str r5, [r4]',                  # state.node = node
        f'  ldr r0, ={CLOCK}',
        '  ldr r0, [r0]',
        '  str r0, [r4, #4]',              # state.since = now
        '  movs r0, #0',
        '  strb r0, [r4, #8]',             # phase = DWELL
        '  strb r0, [r4, #9]',             # dirty = 0
        '  str r0, [r4, #0x10]',           # cur_entry = none
        f'  ldr r0, ={B}',
        '  str r0, [r4, #0x14]',           # active string = BUF
        '  movs r0, #1',
        f'  strb r0, [r4, #{LABEL_FRESH:#x}]',  # this paint's row
                               # loop drew the stock name over the
                               # label: mq_show owes a label render
                               # at the gate exit; the background
                               # itself is resolved at gate_same,
                               # below, which sets the fresh and
                               # gone flags mq_show also consumes
        # Selection paint: resolve the node's tags now, so the
        # bounded parse cost lands inside the dwell, not at expiry
        # (v2). Then install the row's label (v5): the enriched
        # tag string when the parse produced one, the composed
        # file string otherwise. The label is the row's string
        # from this paint onward; the dwell below governs only
        # the marquee's first step, and nothing is swapped in at
        # expiry. In the file view there is nothing to parse: the
        # file view label is composed from the node alone.
        '  ldrb r0, [r4, #0x18]',          # view mode
        '  cmp r0, #0',
        '  bne gate_decide',               # file view: no parse
        '  mov r0, r5',
        '  bl {TAGS}',                     # -> state.cur_entry
        'gate_decide:',
        '  ldrb r0, [r4, #0x18]',          # view mode
        '  cmp r0, #0',
        '  bne gate_decide_v1',            # file view: file string
        '  ldr r0, [r4, #0x10]',           # cur_entry
        '  cmp r0, #0',
        '  beq gate_decide_v1',
        '  ldrb r1, [r0, #0x10]',          # entry flags
        '  tst r1, #2',                    # has_tags?
        '  beq gate_decide_v1',
        '  add r0, r0, #0x14',             # entry buffer
        '  str r0, [r4, #0x14]',           # active string = label
        '  b gate_same',
        'gate_decide_v1:',
        '  mov r0, r5',
        '  bl {UNITS}',                    # name units (capped 49)
        f'  cmp r0, #{NAME_CAP}',
        '  bhi gate_decide_none',
        '  mov r0, r5',
        '  bl {COMPOSE}',                 # composed string -> BUF
        f'  ldr r0, ={B}',
        '  str r0, [r4, #0x14]',           # active string = BUF
        '  b gate_same',
        'gate_decide_none:',
        # Name over the compose cap: no label is installed; the
        # expiry fallback registers the stock name scroll, as v1.
        '  movs r0, #0',
        '  str r0, [r4, #0x14]',           # active string = none
        'gate_same:',
        # Resolve the background for this paint's selection:
        # the selected node's picture is decoded here, in the
        # selecting paint, when the selection's identity is not
        # the one the single store already holds; a folder or a
        # picture-less file marks the background gone instead.
        # Same-node paints cost a four-word compare. Preserves
        # r4-r6.
        '  mov r0, r5',
        '  bl {BG}',
        '  ldrb r0, [r4, #8]',
        '  cmp r0, #1',
        '  beq gate_scroll',
        '  cmp r0, #2',
        '  beq gate_pass',
        # DWELL: hold the step until the dwell expires. Keep bit
        # 0x148 posted so the framework keeps dispatching paints.
        f'  ldr r0, ={CLOCK}',
        '  ldr r0, [r0]',
        '  ldr r1, [r4, #4]',
        '  subs r0, r0, r1',
        f'  cmp r0, #{DWELL_TICKS}',
        '  blo gate_dwell_wait',
        # Dwell expired. The label was installed on the selecting
        # paint and the background by the resolution above; what
        # remains is the v1 decision, re-derived identically: the
        # tag view prefers the cached tag string for this node
        # over the composed dirent string, the file view always
        # composes. Widths are judged against the stock 220 px
        # (v5 has no text shift).
        '  ldrb r0, [r4, #0x18]',          # view mode
        '  cmp r0, #0',
        '  bne gate_v1',                   # file view: v1 string
        '  ldr r0, [r4, #0x10]',           # cur_entry
        '  cmp r0, #0',
        '  beq gate_v1',
        '  ldrb r1, [r0, #0x10]',          # entry flags
        '  tst r1, #2',                    # has_tags?
        '  beq gate_v1',
        '  add r0, r0, #0x14',             # entry buffer
        '  str r0, [r4, #0x14]',           # active string = entry
        f'  bl {MEASURE:#x}',
        '  movs r1, #0xdc',
        '  cmp r0, r1',
        '  bls gate_fits',
        '  bl {NODE}',                    # refresh r0/r1 after calls
        '  mov r2, r1',
        '  ldr r0, [r4, #0x14]',
        '  mov r1, r2',
        '  bl {REGISTER}',
        '  movw r0, #0x148',
        f'  bl {SET_BIT:#x}',
        '  movs r0, #1',
        '  strb r0, [r4, #8]',             # phase = SCROLL
        '  movs r0, #0',
        '  b gate_out0',
        'gate_v1:',
        '  mov r0, r5',
        '  bl {UNITS}',                   # name units (capped 49)
        f'  cmp r0, #{NAME_CAP}',
        '  bhi gate_fallback',
        '  mov r0, r5',
        '  bl {COMPOSE}',                 # composed string -> BUF
        f'  ldr r0, ={B}',
        '  str r0, [r4, #0x14]',           # active string = BUF
        f'  bl {MEASURE:#x}',
        '  movs r1, #0xdc',
        '  cmp r0, r1',
        '  bls gate_fits',
        '  bl {NODE}',                    # refresh r0/r1 after calls
        '  mov r2, r1',
        f'  ldr r0, ={B}',
        '  mov r1, r2',
        '  bl {REGISTER}',
        '  movw r0, #0x148',
        f'  bl {SET_BIT:#x}',
        '  movs r0, #1',
        '  strb r0, [r4, #8]',             # phase = SCROLL
        '  movs r0, #0',
        '  b gate_out0',
        'gate_fits:',
        # Composed fits, so the name fits: nothing scrolls. Clear the
        # bit the dwell kept posted and go passive.
        '  movs r0, #2',
        '  strb r0, [r4, #8]',             # phase = PASS
        '  movw r0, #0x148',
        f'  bl {CLEAR_BIT:#x}',
        '  movs r0, #0',
        '  b gate_out0',
        'gate_fallback:',
        # Name longer than the compose cap: register the stock name
        # scroll directly (the row loop may not run on this paint).
        '  movs r0, #2',
        '  strb r0, [r4, #8]',             # phase = PASS
        '  bl {NODE}',
        '  mov r2, r1',
        '  add r0, r0, #0x70',
        '  mov r1, r2',
        '  bl {REGISTER}',
        '  movw r0, #0x148',
        f'  bl {SET_BIT:#x}',
        '  movs r0, #0',
        '  b gate_out0',
        'gate_dwell_wait:',
        '  movw r0, #0x148',
        f'  bl {TEST_BIT:#x}',
        '  cmp r0, #0',
        '  bne gate_zero',
        '  movw r0, #0x148',
        f'  bl {SET_BIT:#x}',
        '  movs r0, #0',
        '  b gate_out0',
        'gate_scroll:',
        # If a list or chrome paint re-registered the stock name,
        # take the registration back, preserving the scroll offset,
        # direction and tick stamp around the registrar call.
        f'  ldr r0, ={LCTX}',
        '  ldr r0, [r0, #0xc]',
        '  ldr r1, [r4, #0x14]',           # active string
        '  cmp r0, r1',
        '  beq gate_stock',
        f'  ldr r2, ={MCTX}',
        '  ldrh r0, [r2, #8]',
        '  strh r0, [r4, #0xa]',
        '  ldrh r0, [r2, #0xa]',
        '  strh r0, [r4, #0xc]',
        '  ldrh r0, [r2, #0x28]',
        '  strh r0, [r4, #0xe]',
        '  bl {NODE}',
        '  mov r2, r1',
        '  ldr r0, [r4, #0x14]',           # active string
        '  mov r1, r2',
        '  bl {REGISTER}',
        f'  ldr r2, ={MCTX}',
        '  ldrh r0, [r4, #0xa]',
        '  strh r0, [r2, #8]',
        '  ldrh r0, [r4, #0xc]',
        '  strh r0, [r2, #0xa]',
        '  ldrh r0, [r4, #0xe]',
        '  strh r0, [r2, #0x28]',
        '  b gate_stock',
        'gate_pass:',
        '  ldrb r0, [r4, #9]',
        '  cmp r0, #0',
        '  beq gate_stock',
        '  movs r0, #0',
        '  strb r0, [r4, #9]',             # consume the key reset
        '  movw r0, #0x148',
        f'  bl {TEST_BIT:#x}',
        '  cmp r0, #0',
        '  beq gate_stock',
        '  bl {NODE}',
        '  mov r2, r1',
        '  add r0, r0, #0x70',
        '  mov r1, r2',
        '  bl {REGISTER}',                # offset restarts at 0
        'gate_stock:',
        # Every exit passes through mq_show first: it repaints
        # the pictured rows' rasters (the row loop of a list paint
        # has just repainted the bands over them) and, when a
        # label render is owed, erases the stock name the loop
        # drew and renders the label in its place.
        '  bl {SHOW}',
        '  movw r0, #0x148',
        f'  bl {TEST_BIT:#x}',
        '  pop {r4, r5, r6, pc}',
        'gate_out0:',
        '  bl {SHOW}',
        '  pop {r4, r5, r6, pc}',
        'gate_zero:',
        '  movs r0, #0',
        '  b gate_out0',
    ]
    node = [
        # Selected node from the browser context: walk the node
        # chain from the first visible node by (selected - first).
        # Returns r0 = node (0 if none), r1 = visible row 0..6.
        # Clobbers r0-r3 only.
        'mq_node:',
        f'  ldr r0, ={BCTX}',
        '  ldrh r1, [r0, #0x1cc]',         # level
        '  add r1, r0, r1, lsl #1',
        '  ldrh r1, [r1, #0x1ce]',         # first visible index
        '  ldrh r2, [r0, #0x1ee]',         # selected index
        '  subs r3, r2, r1',
        '  cmp r3, #6',
        '  bhi mq_node_none',
        '  ldr r0, [r0]',                  # first visible node
        '  cmp r0, #0',
        '  beq mq_node_none',
        '  mov r1, r3',
        '  cmp r3, #0',
        '  beq mq_node_done',
        'mq_node_walk:',
        '  ldr r0, [r0, #4]',
        '  cmp r0, #0',
        '  beq mq_node_none',
        '  subs r3, r3, #1',
        '  bne mq_node_walk',
        'mq_node_done:',
        '  bx lr',
        'mq_node_none:',
        '  movs r0, #0',
        '  bx lr',
    ]
    units = [
        # r0 = node -> r0 = UTF-16 units in the name, capped at 49
        # (49 means "over the compose cap"). Clobbers r0-r2.
        'mq_units:',
        '  add r0, r0, #0x70',
        '  movs r1, #0',
        'mq_units_loop:',
        '  ldrh r2, [r0, r1, lsl #1]',
        '  cmp r2, #0',
        '  beq mq_units_done',
        '  add r1, r1, #1',
        '  cmp r1, #49',
        '  blo mq_units_loop',
        'mq_units_done:',
        '  mov r0, r1',
        '  bx lr',
    ]
    compose = [
        # r0 = node. Writes the composed scroll string into BUF:
        # name, then for files " - EXT" (when the dirent extension is
        # non-blank) and " - SIZE". Folders compose the name only.
        # Preserves r4-r6; r5 is the destination cursor throughout.
        'mq_compose:',
        '  push {r4, r5, r6, lr}',
        '  mov r4, r0',
        f'  ldr r5, ={B}',
        '  add r0, r4, #0x70',
        'mq_cp_name:',
        '  ldrh r1, [r0]',
        '  cmp r1, #0',
        '  beq mq_cp_named',
        '  strh r1, [r5]',
        '  add r0, r0, #2',
        '  add r5, r5, #2',
        '  b mq_cp_name',
        'mq_cp_named:',
        '  ldrb r1, [r4, #0x5a]',          # dirent attr
        '  tst r1, #0x10',
        '  bne mq_cp_end',                 # directory: name only
        '  add r0, r4, #0x57',             # dirent extension
        '  ldrb r1, [r0]',
        '  cmp r1, #0x20',
        '  beq mq_cp_size',
        '  bl mq_put_sep',
        '  movs r6, #3',
        'mq_cp_ext:',
        '  ldrb r1, [r0]',
        '  add r0, r0, #1',
        '  cmp r1, #0x20',
        '  beq mq_cp_ext_next',
        '  strh r1, [r5]',
        '  add r5, r5, #2',
        'mq_cp_ext_next:',
        '  subs r6, r6, #1',
        '  bne mq_cp_ext',
        'mq_cp_size:',
        '  bl mq_put_sep',
        '  ldr r0, [r4, #0x6b]',           # dirent file size
        '  bl mq_put_size',
        'mq_cp_end:',
        '  movs r1, #0',
        '  strh r1, [r5]',
        '  pop {r4, r5, r6, pc}',
        # " - " at r5; clobbers r1.
        'mq_put_sep:',
        '  movs r1, #0x20',
        '  strh r1, [r5]',
        '  movs r1, #0x2d',
        '  strh r1, [r5, #2]',
        '  movs r1, #0x20',
        '  strh r1, [r5, #4]',
        '  add r5, r5, #6',
        '  bx lr',
        # r0 = size. Appends "N B" / "N KB" / "N.N MB" / "N.N GB"
        # at r5 (no leading separator; caller emitted it).
        'mq_put_size:',
        '  push {r4, lr}',
        '  ldr r1, =0x100000',
        '  cmp r0, r1',
        '  blo mq_ps_kb',
        '  ldr r1, =0x40000000',
        '  cmp r0, r1',
        '  blo mq_ps_mb',
        # GB: whole = size >> 30; tenth = ((size & 0x3FFFFFFF) >> 3)
        # * 10 >> 27 (shifted to stay inside 32 bits).
        '  lsrs r2, r0, #30',
        '  ldr r1, =0x3fffffff',
        '  and r0, r0, r1',
        '  lsrs r0, r0, #3',
        '  movs r1, #10',
        '  mul r0, r0, r1',
        '  lsrs r0, r0, #27',
        '  mov r4, r0',                    # tenth
        '  mov r0, r2',
        '  bl mq_put_dec',
        '  bl mq_put_dot',
        '  mov r0, r4',
        '  bl mq_put_dec1',
        '  movs r1, #0x47',                # 'G'
        '  movs r2, #0x42',                # 'B'
        '  bl mq_put_unit2',
        '  pop {r4, pc}',
        'mq_ps_mb:',
        # whole = size >> 20; tenth = (size & 0xFFFFF) * 10 >> 20.
        '  lsrs r2, r0, #20',
        '  lsls r0, r0, #12',
        '  lsrs r0, r0, #12',
        '  movs r1, #10',
        '  mul r0, r0, r1',
        '  lsrs r0, r0, #20',
        '  mov r4, r0',
        '  mov r0, r2',
        '  bl mq_put_dec',
        '  bl mq_put_dot',
        '  mov r0, r4',
        '  bl mq_put_dec1',
        '  movs r1, #0x4d',                # 'M'
        '  movs r2, #0x42',                # 'B'
        '  bl mq_put_unit2',
        '  pop {r4, pc}',
        'mq_ps_kb:',
        '  ldr r1, =1024',
        '  cmp r0, r1',
        '  blo mq_ps_b',
        '  add r0, r0, #512',              # round to nearest KB
        '  lsrs r0, r0, #10',
        '  bl mq_put_dec',
        '  movs r1, #0x4b',                # 'K'
        '  movs r2, #0x42',                # 'B'
        '  bl mq_put_unit2',
        '  pop {r4, pc}',
        'mq_ps_b:',
        '  bl mq_put_dec',
        '  movs r1, #0x20',
        '  strh r1, [r5]',
        '  movs r1, #0x42',                # 'B'
        '  strh r1, [r5, #2]',
        '  add r5, r5, #4',
        '  pop {r4, pc}',
        # Decimal, no leading zeros, at r5. r0 = value <= 9999.
        'mq_put_dec:',
        '  push {r4, lr}',
        '  mov r4, r0',
        '  ldr r3, =1000',
        '  movs r2, #0',                   # started flag
        'mq_pd_loop:',
        '  udiv r0, r4, r3',
        '  cmp r0, #0',
        '  bne mq_pd_write',
        '  cmp r2, #0',
        '  bne mq_pd_write',
        '  cmp r3, #1',
        '  beq mq_pd_write',
        '  b mq_pd_next',
        'mq_pd_write:',
        '  movs r2, #1',
        '  mls r4, r0, r3, r4',
        '  add r0, r0, #0x30',
        '  strh r0, [r5]',
        '  add r5, r5, #2',
        'mq_pd_next:',
        '  cmp r3, #1',
        '  beq mq_pd_done',
        '  movs r0, #10',
        '  udiv r3, r3, r0',
        '  b mq_pd_loop',
        'mq_pd_done:',
        '  pop {r4, pc}',
        'mq_put_dot:',
        '  movs r1, #0x2e',
        '  strh r1, [r5]',
        '  add r5, r5, #2',
        '  bx lr',
        'mq_put_dec1:',                    # r0 = single digit 0..9
        '  add r0, r0, #0x30',
        '  strh r0, [r5]',
        '  add r5, r5, #2',
        '  bx lr',
        # " XY" at r5: r1 = first letter, r2 = second letter.
        'mq_put_unit2:',
        '  movs r0, #0x20',
        '  strh r0, [r5]',
        '  strh r1, [r5, #2]',
        '  strh r2, [r5, #4]',
        '  add r5, r5, #6',
        '  bx lr',
    ]
    register = [
        # r0 = string, r1 = row. Mirrors the painter's own row
        # registration: stores the string pointer at LCTX+0xC, then
        # calls the stock registrar with the row rect, the packed
        # position (x0 | y0 << 16), flags 0x100000 and interval 30.
        # The rect is the stock one (left edge 11, right edge
        # 231): with the background model nothing shifts the
        # row's text. Draws nothing. Preserves r4.
        'mq_register:',
        '  push {r4, lr}',
        '  mov r4, r0',
        '  movs r2, #40',
        '  mul r1, r1, r2',
        '  add r1, r1, #53',               # y0
        '  sub sp, #16',
        '  str r4, [sp]',                  # stack arg: string
        '  movs r0, #30',
        '  str r0, [sp, #4]',              # stack arg: interval
        '  movs r0, #11',
        '  strh r0, [sp, #8]',             # rect x0
        '  strh r1, [sp, #10]',            # rect y0
        '  movw r0, #231',
        '  strh r0, [sp, #12]',            # rect x1
        '  add r0, r1, #15',
        '  strh r0, [sp, #14]',            # rect y1
        f'  ldr r2, ={LCTX}',
        '  str r4, [r2, #0xc]',
        '  ldrh r2, [sp, #8]',
        '  bfi r2, r1, #16, #16',          # packed position
        '  mov r1, r2',
        '  ldr r2, =0x100000',
        '  movs r3, #0',
        '  add r0, sp, #8',
        f'  bl {MQ_SETUP:#x}',
        '  add sp, #16',
        '  pop {r4, pc}',
    ]
    key = [
        # B.W from KEY_SITE. Any key press restarts the dwell for
        # the current selection: phase back to DWELL, stamp = now,
        # and the dirty flag tells the gate to re-register a pass
        # phase stock string (offset reset) at the next paint. Then
        # performs the displaced push and resumes the stock handler.
        'mq_key:',
        '  push {r0, r1, r2, r3}',
        f'  ldr r0, ={S}',
        f'  ldr r1, ={CLOCK}',
        '  ldr r1, [r1]',
        '  str r1, [r0, #4]',
        '  movs r1, #0',
        '  strb r1, [r0, #8]',
        '  movs r1, #1',
        '  strb r1, [r0, #9]',
        # The repaint a key provokes may redraw the rows: owe a
        # label render at the next gate exit.
        f'  strb r1, [r0, #{LABEL_FRESH:#x}]',
        '  pop {r0, r1, r2, r3}',
        '  push.w {r4, r5, r6, r7, r8, sb, lr}',
        f'  b.w {KEY_SITE + 4:#x}',
    ]
    toggle = [
        # BL from TOGGLE_SITE, inside the stock Key handler at the
        # point where r4 holds the final event word (after the
        # handler's own fetch and its 0x131 override). A long press
        # of Vol+ (event 0x20000010) flips the view mode byte and
        # clears state.node, so the next paint re-runs the gate's
        # selection path under the new mode: in the tag view that
        # re-resolves through the cache (a hit needs no re-read),
        # in the file view it skips the parse entirely. mq_key has
        # already reset the dwell stamp and phase for this same key
        # event, so the scroll restarts from the dwell in the new
        # view. Any other event word is ignored. The stub preserves
        # r0-r3 (r2 carries a cell pointer the volume paths use),
        # leaves r4-r8 untouched, then performs the displaced
        # instruction (sb = the browser local context pointer).
        'mq_toggle:',
        '  push {r0, r1, r2, r3}',
        f'  ldr r0, ={TOGGLE_EVENT:#x}',
        '  cmp r4, r0',
        '  bne mq_toggle_done',
        f'  ldr r1, ={S}',
        '  ldrb r0, [r1, #0x18]',          # view mode
        '  eor r0, r0, #1',
        '  strb r0, [r1, #0x18]',
        '  movs r0, #0',
        '  str r0, [r1]',                  # node = none: re-resolve
        'mq_toggle_done:',
        '  pop {r0, r1, r2, r3}',
        f'  ldr sb, ={LCTX}',
        '  bx lr',
    ]
    exit_ = [
        # B.W from EXIT_SITE. Zeroes the marquee state (which
        # carries the background's active and key-valid flags,
        # so no background and no picture knowledge survives the
        # window), the tag cache's valid bytes and the key
        # entry's result, then performs the displaced clear of
        # bit 0x148 exactly as stock (mov.w r0, #0x148; tail
        # branch to the clear helper).
        'mq_exit:',
        f'  ldr ip, ={S}',
        '  movs r0, #0',
        f'  movs r1, #{STATE_LEN // 4}',
        'mq_exit_state:',
        '  str r0, [ip]',
        '  add ip, ip, #4',
        '  subs r1, r1, #1',
        '  bne mq_exit_state',
        '  movs r0, #0',
        f'  ldr ip, ={data["cache"]}',
        f'  movs r1, #{CACHE_ENTRIES}',
        'mq_exit_loop:',
        '  strb r0, [ip, #0x10]',
        f'  add ip, ip, #{CACHE_ENTRY_LEN}',
        '  subs r1, r1, #1',
        '  bne mq_exit_loop',
        f'  ldr ip, ={data["keytab"]}',
        '  movs r3, #0xff',
        '  strb r3, [ip, #0x10]',          # slot = none
        '  strb r0, [ip, #0x11]',          # result = unknown
        '  movw r0, #0x148',
        f'  b.w {CLEAR_BIT:#x}',
    ]
    tags = [
        # r0 = node. Resolve the node's tag string into the cache
        # and set state.cur_entry (0 when the node carries no cache
        # entry: folders and over-cap names are never parsed). Runs
        # on the selecting paint, inside the dwell. The file is
        # opened by (directory cluster, enumeration index) through
        # the stock open the scan and the player use, parsed by the
        # stock tag dispatcher, and closed, all inside this call.
        # Preserves r4-r6.
        'mq_tags:',
        '  push {r4, r5, r6, r7, lr}',
        '  mov r4, r0',                    # node
        '  ldrb r1, [r4, #0x5a]',          # dirent attr
        '  tst r1, #0x10',
        '  bne mq_tags_done',              # folder: never a file read
        '  mov r0, r4',
        '  bl {UNITS}',                    # name units (capped 49)
        f'  cmp r0, #{NAME_CAP}',
        '  bhi mq_tags_done',              # stock name scroll instead
        # Cache lookup: key = node, directory cluster, file
        # cluster, ordinal (mq_ident; the directory cluster comes
        # from the browser context's per-level record, +0x14, or
        # +0x18 on FS type 3, whose context word doubles as the
        # cluster cell); a directory change therefore misses and
        # re-parses.
        '  mov r0, r4',
        '  bl {IDENT}',                   # r0 dir, r1 file, r2 ord
        '  mov r6, r0',                    # directory cluster
        '  mov r7, r1',                    # file cluster
        '  lsr r0, r4, #4',
        f'  and r0, r0, #{CACHE_ENTRIES - 1}',
        f'  movs r1, #{CACHE_ENTRY_LEN}',
        '  mul r0, r0, r1',
        f'  ldr r1, ={data["cache"]}',
        '  add r0, r0, r1',                # entry -> r5
        '  mov r5, r0',
        '  ldrb r1, [r5, #0x10]',
        '  tst r1, #1',
        '  beq mq_tags_miss',              # not valid
        '  ldr r1, [r5]',
        '  cmp r1, r4',
        '  bne mq_tags_miss',
        '  ldr r1, [r5, #4]',
        '  cmp r1, r6',
        '  bne mq_tags_miss',
        '  ldr r1, [r5, #8]',
        '  cmp r1, r7',
        '  bne mq_tags_miss',
        '  ldr r1, [r5, #0xc]',
        '  cmp r1, r2',
        '  bne mq_tags_miss',
        'mq_tags_hit:',
        f'  ldr r0, ={S}',
        '  str r5, [r0, #0x10]',           # cur_entry = entry
        '  pop {r4, r5, r6, r7, pc}',
        'mq_tags_miss:',
        # Claim the entry for this key now, marked parsed with no
        # tags; the parse below upgrades it in place.
        '  str r4, [r5]',
        '  str r6, [r5, #4]',
        '  str r7, [r5, #8]',
        '  str r2, [r5, #0xc]',
        '  movs r1, #1',
        '  strb r1, [r5, #0x10]',          # valid, has_tags = 0
        f'  ldr r0, ={S}',
        '  str r5, [r0, #0x10]',
        # Extension gate: only formats the dispatcher parses
        # inside module 0 (WMA excluded, see design.md).
        '  add r0, r4, #0x57',             # dirent extension
        f'  ldr r1, ={data["exttab"]}',
        f'  movs r2, #{len(TAG_EXTS)}',
        'mq_tags_ext:',
        '  ldrb r3, [r0]',
        '  ldrb ip, [r1]',
        '  cmp r3, ip',
        '  bne mq_tags_ext_next',
        '  ldrb r3, [r0, #1]',
        '  ldrb ip, [r1, #1]',
        '  cmp r3, ip',
        '  bne mq_tags_ext_next',
        '  ldrb r3, [r0, #2]',
        '  ldrb ip, [r1, #2]',
        '  cmp r3, ip',
        '  beq mq_tags_open',
        'mq_tags_ext_next:',
        '  add r1, r1, #3',
        '  subs r2, r2, #1',
        '  bne mq_tags_ext',
        '  pop {r4, r5, r6, r7, pc}',      # unsupported: v1 string
        'mq_tags_open:',
        f'  ldr r0, ={data["struct"]}',    # doubles as name-out
        '  mov r1, r6',                    # directory cluster
        '  ldr r2, [r4, #0xc]',            # ordinal (0-based)
        '  movs r3, #3',                   # stock playback value
        f'  ldr ip, ={MODE_STR:#x}',       # "R" mode string
        '  push {ip}',
        f'  bl {FSOPEN:#x}',
        '  add sp, sp, #4',
        '  cmp r0, #0',
        '  blt mq_tags_done',              # open failed: v1 string
        '  mov r6, r0',                    # handle
        # The struct span is shared with the background store
        # (the union in the module docstring): zeroing and
        # filling it here overwrites the previous selection's
        # art, inside the gate, before mq_show repaints at the
        # gate exit, so no paint observes the contention.
        f'  ldr r0, ={data["struct"]}',
        f'  movw r1, #{TAG_STRUCT_LEN:#x}',
        f'  bl {BZERO:#x}',                # zero the struct (stock)
        '  mov r0, r6',
        f'  ldr r1, ={data["struct"]}',
        '  add r2, r4, #0x57',             # extension (3 bytes)
        f'  bl {TAGPARSE:#x}',
        '  mov r0, r6',
        f'  bl {FSCLOSE:#x}',
        '  mov r0, r5',                    # entry
        '  mov r1, r4',                    # node (label lead rule)
        '  bl {TAGSTR}',                   # compose into the entry
        'mq_tags_done:',
        '  pop {r4, r5, r6, r7, pc}',
    ]
    tagstr = [
        # r0 = cache entry, r1 = node. Compose the entry's tag
        # string from the dispatcher struct. Composition order is
        # TITLE, ARTIST, ALBUM (v5; v2 to v4 led with the artist),
        # joined by " - ". Fields are trimmed of leading and
        # trailing units <= 0x20 and carried in full up to the
        # struct's 127-unit field bound (v3; v2 capped them at
        # 24/24/13); the joined result is bounded by the entry
        # buffer (264 units in v5, enforced by field_put). The
        # artist falls back to the album artist when
        # empty (the playback rule). Lead rule: the artist never
        # leads; when the title is absent the file name leads
        # instead, with the artist and the album appended after
        # it. When neither the title nor the artist survives, no
        # tag string is claimed and the gate falls back to the v1
        # file string; the album alone is not a usable tag. Sets
        # the entry's has_tags flag exactly when a title or an
        # artist survived. Preserves r4-r7.
        'mq_tagstr:',
        '  push {r4, r5, r6, r7, r8, lr}',
        '  mov r4, r0',                    # entry
        '  mov r7, r1',                    # node
        '  add r5, r4, #0x14',             # destination cursor
        '  movs r6, #0',                   # fields written so far
        f'  movw r8, #{TAG_BUF_UNITS - 1}',  # unit budget for the
                               # entry buffer (v5: the buffer is
                               # 264 units; field_put enforces the
                               # bound, fields are read uncapped)
        # title: struct +0x60.
        f'  ldr r0, ={data["struct"]}',
        '  add r0, r0, #0x60',
        f'  movs r1, #{TITLE_CAP}',
        '  bl mq_field_len',
        '  bl mq_field_put',
        # artist: struct +0x15E, else album artist at +0x458.
        f'  ldr r0, ={data["struct"]}',
        '  add r0, r0, #0x15e',
        f'  movs r1, #{ARTIST_CAP}',
        '  bl mq_field_len',
        '  cmp r2, #0',
        '  bne mq_ts_artist',
        f'  ldr r0, ={data["struct"]}',
        '  add r0, r0, #0x458',
        f'  movs r1, #{ARTIST_CAP}',
        '  bl mq_field_len',
        'mq_ts_artist:',
        '  cmp r2, #0',
        '  beq mq_ts_album',               # no artist at all
        '  cmp r6, #0',
        '  bne mq_ts_put_artist',          # the title leads
        # No title: the file name leads, the artist follows it.
        '  push {r0, r2}',                 # keep the artist field
        '  add r0, r7, #0x70',             # display name
        f'  movs r1, #{NAME_CAP}',
        '  bl mq_field_len',
        '  cmp r2, #0',
        '  beq mq_ts_no_lead',             # degenerate empty
                               # name: claim no tag string rather
                               # than let the artist lead
        '  bl mq_field_put',               # the name leads
        '  pop {r0, r2}',
        'mq_ts_put_artist:',
        '  bl mq_field_put',
        '  b mq_ts_album',
        'mq_ts_no_lead:',
        '  pop {r0, r2}',
        '  b mq_ts_end',
        'mq_ts_album:',
        # album: struct +0x25C, only when a lead field exists.
        '  cmp r6, #0',
        '  beq mq_ts_end',
        f'  ldr r0, ={data["struct"]}',
        '  add r0, r0, #0x25c',
        f'  movs r1, #{ALBUM_CAP}',
        '  bl mq_field_len',
        '  bl mq_field_put',
        'mq_ts_end:',
        '  movs r1, #0',
        '  strh r1, [r5]',                 # terminate
        '  cmp r6, #0',
        '  beq mq_ts_ret',
        '  movs r1, #3',                   # valid + has_tags
        '  strb r1, [r4, #0x10]',
        'mq_ts_ret:',
        '  pop {r4, r5, r6, r7, r8, pc}',
        # mq_field_len: r0 = field (UTF-16, 127 units max), r1 =
        # cap. Returns r0 = first kept unit, r2 = kept units
        # (after trimming both ends, capped). Clobbers r0-r3.
        'mq_field_len:',
        '  movs r2, #0',                   # leading skip
        'mq_fl_lead:',
        '  cmp r2, #127',
        '  bhs mq_fl_empty',
        '  ldrh r3, [r0, r2, lsl #1]',
        '  cmp r3, #0',
        '  beq mq_fl_empty',
        '  cmp r3, #0x20',
        '  bhi mq_fl_body',
        '  add r2, r2, #1',
        '  b mq_fl_lead',
        'mq_fl_body:',
        '  rsb r3, r2, #127',              # budget = 127 - skip
        '  add r0, r0, r2, lsl #1',        # first kept unit
        '  movs r2, #0',                   # raw length from here
        'mq_fl_len:',
        '  cmp r2, r3',
        '  bhs mq_fl_trim',
        '  ldrh ip, [r0, r2, lsl #1]',
        '  cmp ip, #0',
        '  beq mq_fl_trim',
        '  add r2, r2, #1',
        '  b mq_fl_len',
        'mq_fl_trim:',
        '  cmp r2, #0',
        '  beq mq_fl_done',
        '  sub r3, r2, #1',
        '  ldrh r3, [r0, r3, lsl #1]',
        '  cmp r3, #0x20',
        '  bhi mq_fl_done',
        '  sub r2, r2, #1',
        '  b mq_fl_trim',
        'mq_fl_done:',
        '  cmp r2, r1',
        '  bls mq_fl_ret',
        '  mov r2, r1',                    # apply the cap
        'mq_fl_ret:',
        '  bx lr',
        'mq_fl_empty:',
        '  movs r2, #0',
        '  bx lr',
        # mq_field_put: r0 = first kept unit, r2 = units, r8 =
        # units of room left in the entry buffer (r8 because
        # mq_field_len spends ip as its own scratch). When units
        # > 0: emits " - " first unless this is the first field,
        # copies the units to r5 (truncating at the buffer
        # bound), counts the field in r6. Clobbers r0-r3;
        # advances r5 and spends r8.
        'mq_field_put:',
        '  cmp r2, #0',
        '  beq mq_fp_ret',
        '  cmp r6, #0',
        '  beq mq_fp_copy',
        '  cmp r8, #3',
        '  bls mq_fp_ret',                 # no room to join
        '  sub r8, r8, #3',
        '  movs r3, #0x20',
        '  strh r3, [r5]',
        '  movs r3, #0x2d',
        '  strh r3, [r5, #2]',
        '  movs r3, #0x20',
        '  strh r3, [r5, #4]',
        '  add r5, r5, #6',
        'mq_fp_copy:',
        '  cmp r8, #0',
        '  beq mq_fp_count',               # buffer bound reached
        '  ldrh r3, [r0]',
        '  strh r3, [r5]',
        '  add r0, r0, #2',
        '  add r5, r5, #2',
        '  sub r8, r8, #1',
        '  subs r2, r2, #1',
        '  bne mq_fp_copy',
        'mq_fp_count:',
        '  add r6, r6, #1',
        'mq_fp_ret:',
        '  bx lr',
    ]
    ident = [
        # r0 = node -> r0 = directory cluster, r1 = file cluster,
        # r2 = enumeration ordinal: the cache key both the tag
        # cache and the raster cache are keyed by. The directory
        # cluster comes from the browser context's per-level
        # record (+0x14, or +0x18 on FS type 3, whose context word
        # doubles as that mode's cluster cell). Clobbers r0-r3.
        'mq_ident:',
        f'  ldr r3, ={BCTX}',
        '  ldrh r1, [r3, #0x1cc]',         # level
        '  movs r2, #56',
        '  mul r1, r1, r2',
        '  add r3, r3, r1',                # level record
        f'  ldr r1, ={FSTYPE:#x}',
        '  ldrb r1, [r1]',
        '  cmp r1, #3',
        '  beq mq_ident_fs3',
        '  ldr r1, [r3, #0x14]',           # directory cluster
        '  b mq_ident_file',
        'mq_ident_fs3:',
        '  ldr r1, [r3, #0x18]',
        'mq_ident_file:',
        '  ldrh r2, [r0, #0x69]',          # file cluster low
        '  ldrh r3, [r0, #0x63]',          # file cluster high
        '  orr r2, r2, r3, lsl #16',       # file cluster
        '  ldr r3, [r0, #0xc]',            # enumeration ordinal
        '  mov r0, r1',
        '  mov r1, r2',
        '  mov r2, r3',
        '  bx lr',
    ]
    bg = [
        # r0 = node. Bring the background store in line with the
        # selection. The single key entry holds the identity of
        # the node the store (or the negative result) belongs to;
        # when it already matches, reselecting the same node is
        # free. Otherwise the identity is claimed and mq_decode
        # resolves the picture, setting the entry's result byte
        # and the state's fresh and gone flags for mq_show.
        # Preserves r4-r6.
        'mq_bg:',
        '  push {r4, r5, lr}',
        '  mov r4, r0',                    # node
        f'  ldr r5, ={data["keytab"]}',    # the single entry
        f'  ldr r0, ={S}',
        f'  ldrb r1, [r0, #{BG_VALID:#x}]',
        '  cmp r1, #0',
        '  beq mq_bg_claim',
        '  ldr r1, [r5]',
        '  cmp r1, r4',
        '  bne mq_bg_claim',
        '  mov r0, r4',
        '  bl {IDENT}',                   # r0 dir, r1 file, r2 ord
        '  ldr r3, [r5, #4]',
        '  cmp r3, r0',
        '  bne mq_bg_claim2',
        '  ldr r3, [r5, #8]',
        '  cmp r3, r1',
        '  bne mq_bg_claim2',
        '  ldr r3, [r5, #0xc]',
        '  cmp r3, r2',
        '  bne mq_bg_claim2',
        '  pop {r4, r5, pc}',              # identity holds: free
        'mq_bg_claim:',
        '  mov r0, r4',
        '  bl {IDENT}',
        'mq_bg_claim2:',
        '  str r4, [r5]',
        '  str r0, [r5, #4]',
        '  str r1, [r5, #8]',
        '  str r2, [r5, #0xc]',
        '  movs r0, #0',
        '  strb r0, [r5, #0x11]',          # result = unknown
        f'  ldr r0, ={S}',
        '  movs r1, #1',
        f'  strb r1, [r0, #{BG_VALID:#x}]',
        '  mov r0, r4',
        '  mov r1, r5',
        '  bl {DECODE}',
        '  pop {r4, r5, pc}',
    ]
    decode = [
        # r0 = node, r1 = the single background key entry (its
        # identity fields are already claimed). Resolve the
        # node's picture into the background store and set the
        # entry's result byte (1 pictured, 2 negative) with the
        # state's BG_ACTIVE, BG_FRESH and BG_GONE flags. Runs
        # inside the gate, in the selecting paint. A folder and
        # a format without a picture route resolve negative
        # without a file open; an open that fails resolves
        # negative for this selection (window exit clears the
        # key's validity, so a later visit re-resolves). The
        # file is opened by (directory cluster, ordinal) through
        # the stock open, located through the direct route (the
        # MP3 scan body, or the locator case head for FLAC, APE
        # and WAV through mq_loccase), set up at a square decode
        # box through module 18's setup, and the consumer's rows
        # are captured into the store: the produced image's
        # centre crop at the store's aspect, every stored pixel
        # darkened at capture (55 percent toward black in the
        # dark theme, 75 percent toward the paper colour in the
        # light theme, the theater finalize mixes). The consumer
        # draws the raw produced image at the client area's top
        # left while it decodes; mq_show overdraws the darkened
        # store over the whole client area in the same paint.
        # Preserves r4-r6.
        'mq_decode:',
        '  push {r4, r5, r6, r7, r8, r9, lr}',
        '  mov r4, r0',                    # node
        '  mov r5, r1',                    # key entry
        f'  ldr r8, ={S}',
        '  ldrb r0, [r4, #0x5a]',          # dirent attr
        '  tst r0, #0x10',
        '  bne mq_dec_negative0',          # folder: no picture
        # Route from the dirent extension (picext table: 3-byte
        # extension, pad, stock entry point word).
        '  add r0, r4, #0x57',
        f'  ldr r1, ={data["picext"]}',
        f'  movs r2, #{len(PIC_ROUTES)}',
        'mq_dec_ext:',
        '  ldrb r3, [r0]',
        '  ldrb ip, [r1]',
        '  cmp r3, ip',
        '  bne mq_dec_ext_next',
        '  ldrb r3, [r0, #1]',
        '  ldrb ip, [r1, #1]',
        '  cmp r3, ip',
        '  bne mq_dec_ext_next',
        '  ldrb r3, [r0, #2]',
        '  ldrb ip, [r1, #2]',
        '  cmp r3, ip',
        '  beq mq_dec_route',
        'mq_dec_ext_next:',
        f'  add r1, r1, #{PIC_ENTRY_LEN}',
        '  subs r2, r2, #1',
        '  bne mq_dec_ext',
        '  b mq_dec_negative0',            # no picture route
        'mq_dec_route:',
        '  ldr r6, [r1, #4]',              # stock entry point
        '  sub sp, sp, #8',                # frame: mode/out, handle
        f'  ldr ip, ={MODE_STR:#x}',
        '  str ip, [sp]',                  # mode stack arg
        f'  ldr r0, ={data["struct"]}',    # name-out scratch
        '  ldr r1, [r5, #4]',              # directory cluster
        '  ldr r2, [r5, #12]',             # enumeration ordinal
        '  movs r3, #3',                   # stock playback value
        f'  bl {FSOPEN:#x}',
        '  cmp r0, #0',
        '  blt mq_dec_negative',           # open failed: negative
        '  str r0, [sp, #4]',              # handle
        '  mov r2, r0',
        '  movs r0, #0',
        '  movs r1, #0',
        f'  bl {SEEK:#x}',                 # rewind (locator rule)
        # The MP3 case zeroes the descriptor's located cell
        # before scanning; a stale value from an earlier picture
        # (the player's, or a previous selection's) fails the
        # scan.
        f'  ldr r0, ={DESC:#x}',
        '  movs r1, #0',
        '  str r1, [r0]',
        # Locate: the scan body directly, or a locator case head
        # through the shared-frame helper. The mode word lands in
        # the frame's out cell at [sp].
        '  mov r0, r6',                    # route
        f'  ldr r1, ={SCAN:#x}',
        '  cmp r0, r1',
        '  beq mq_dec_scan',
        '  ldr r1, [sp, #4]',              # handle
        '  mov r2, sp',                    # out cell
        '  bl {LOCCASE}',
        '  b mq_dec_located',
        'mq_dec_scan:',
        '  ldr r0, [sp, #4]',              # handle
        '  mov r1, sp',                    # out cell
        f'  bl {SCAN:#x}',
        'mq_dec_located:',
        '  cmp r0, #0',
        '  beq mq_dec_nopic',
        '  ldr r1, =0x80000000',
        '  cmp r0, r1',
        '  bhs mq_dec_nopic',
        # Request globals and descriptor setters for the setup:
        # a square decode box, drawn at the client area's top
        # left while the consumer runs.
        f'  ldr r0, ={REQ:#x}',
        f'  movs r1, #{BG_BOX}',
        '  str r1, [r0]',                  # box width
        '  str r1, [r0, #4]',              # box height
        '  movs r1, #0',
        '  str r1, [r0, #8]',              # dest x
        f'  movs r1, #{ART_Y0}',
        '  str r1, [r0, #0xc]',            # dest y
        '  movs r0, #0',
        f'  bl {SET_D4:#x}',
        '  movs r0, #1',
        f'  bl {SET_D8:#x}',
        '  ldr r0, [sp, #4]',              # handle
        '  ldr r1, [sp]',                  # mode from the out cell
        f'  bl {SETUP:#x}',
        '  cmp r0, #0',
        '  beq mq_dec_nopic',
        # Theme for the capture mix, read once per decode.
        f'  ldr r0, ={SAVEINFO:#x}',
        '  ldrb r0, [r0, #0x2d8]',
        '  cmp r0, #0',
        '  ite eq',
        '  moveq r0, #0',
        '  movne r0, #1',
        f'  strb r0, [r8, #{BG_THEME:#x}]',
        # Produced geometry and the centre crop at the store's
        # aspect: if pw * BG_H > ph * BG_W the image is too
        # wide (crop the sides), else too tall (crop the top
        # and bottom).
        f'  ldr r6, ={CTX:#x}',
        '  ldr r0, [r6, #0x14]',           # produced width
        f'  cmp r0, #{BG_BOX}',
        '  bls mq_dec_pw',
        f'  movs r0, #{BG_BOX}',           # defensive clamp
        'mq_dec_pw:',
        f'  strh r0, [r8, #{BG_PW:#x}]',
        '  ldr r1, [r6, #0x18]',           # produced height
        f'  cmp r1, #{BG_BOX}',
        '  bls mq_dec_ph',
        f'  movs r1, #{BG_BOX}',
        'mq_dec_ph:',
        f'  strh r1, [r8, #{BG_PH:#x}]',
        '  cmp r0, #0',
        '  beq mq_dec_nopic',
        '  cmp r1, #0',
        '  beq mq_dec_nopic',
        f'  movs r2, #{BG_H}',
        '  mul r2, r0, r2',                # pw * BG_H
        f'  movs r3, #{BG_W}',
        '  mul r3, r1, r3',                # ph * BG_W
        '  cmp r2, r3',
        '  bhi mq_dec_wide',
        '  mov r2, r0',                    # cw = pw
        f'  movs r3, #{BG_H}',
        '  mul r3, r0, r3',
        f'  movs ip, #{BG_W}',
        '  udiv r3, r3, ip',               # ch = pw * BG_H / BG_W
        '  b mq_dec_crop',
        'mq_dec_wide:',
        '  mov r3, r1',                    # ch = ph
        f'  movs r2, #{BG_W}',
        '  mul r2, r1, r2',
        f'  movs ip, #{BG_H}',
        '  udiv r2, r2, ip',               # cw = ph * BG_W / BG_H
        'mq_dec_crop:',
        '  cmp r2, #0',
        '  beq mq_dec_nopic',
        '  cmp r3, #0',
        '  beq mq_dec_nopic',
        f'  strh r2, [r8, #{BG_CW:#x}]',
        f'  strh r3, [r8, #{BG_CH:#x}]',
        '  subs r0, r0, r2',
        '  lsr r0, r0, #1',
        f'  strh r0, [r8, #{BG_X0:#x}]',   # x0 = (pw - cw) / 2
        '  subs r1, r1, r3',
        '  lsr r1, r1, #1',
        f'  strh r1, [r8, #{BG_Y0:#x}]',   # y0 = (ph - ch) / 2
        '  movs r0, #0',
        f'  strh r0, [r8, #{BG_SY:#x}]',   # next store row
        '  movs r7, #0',                   # produced rows consumed
        # Capture: the consumer returns 1 exactly when it
        # decoded and blitted a new row (the row buffer then
        # holds it); its cursor, less the descriptor base, is
        # the row index. A produced row is captured into every
        # store row whose sample row it is.
        'mq_dec_cap:',
        f'  ldrh r0, [r8, #{BG_PH:#x}]',
        '  cmp r7, r0',
        '  bhs mq_dec_fill',
        '  ldr r0, [r6, #0x2c]',           # cursor
        f'  ldr r1, ={DESC:#x}',
        '  ldr r1, [r1, #0xc]',
        '  subs r0, r0, r1',               # row index
        '  cmp r0, r7',
        '  bne mq_dec_fill',               # sequence broke: stop
        f'  bl {CONSUMER:#x}',
        '  cmp r0, #0',
        '  beq mq_dec_fill',               # no new row: done
        'mq_dec_caprow:',
        f'  ldrh r0, [r8, #{BG_SY:#x}]',
        f'  cmp r0, #{BG_H}',
        '  bhs mq_dec_next',               # store full
        f'  ldrh r1, [r8, #{BG_CH:#x}]',
        '  mul r1, r0, r1',
        f'  movs r2, #{BG_H}',
        '  udiv r1, r1, r2',               # (SY * CH) / BG_H
        f'  ldrh r2, [r8, #{BG_Y0:#x}]',
        '  add r1, r1, r2',                # sample row for SY
        '  cmp r1, r7',
        '  bne mq_dec_next',               # not this row
        '  bl mq_dec_row',                 # capture row r7
        f'  ldrh r0, [r8, #{BG_SY:#x}]',
        '  add r0, r0, #1',
        f'  strh r0, [r8, #{BG_SY:#x}]',
        '  b mq_dec_caprow',
        'mq_dec_next:',
        '  add r7, r7, #1',
        '  b mq_dec_cap',
        'mq_dec_fill:',
        '  ldr r0, [sp, #4]',
        f'  bl {FSCLOSE:#x}',
        '  cmp r7, #0',
        '  beq mq_dec_negative',           # no produced rows
        f'  ldrh r0, [r8, #{BG_SY:#x}]',
        '  cmp r0, #0',
        '  beq mq_dec_negative',           # nothing captured
        # Replicate the last captured store row over any rows
        # the sampling never reached (a produced height below
        # the store's leaves the bottom rows to fill).
        'mq_dec_fill_loop:',
        f'  cmp r0, #{BG_H}',
        '  bhs mq_dec_pub',
        f'  ldr r1, ={data["struct"]}',
        f'  movs r2, #{BG_W}',
        '  mul r3, r0, r2',
        '  add r1, r1, r3, lsl #1',        # dest row
        '  sub r3, r0, #1',
        '  mul r3, r3, r2',
        f'  ldr r2, ={data["struct"]}',
        '  add r2, r2, r3, lsl #1',        # source row
        f'  movs r3, #{BG_W}',
        'mq_dec_fill_px:',
        '  ldrh ip, [r2]',
        '  strh ip, [r1]',
        '  add r2, r2, #2',
        '  add r1, r1, #2',
        '  subs r3, r3, #1',
        '  bne mq_dec_fill_px',
        '  add r0, r0, #1',
        '  b mq_dec_fill_loop',
        'mq_dec_pub:',
        '  movs r0, #1',
        '  strb r0, [r5, #0x11]',          # entry result = pictured
        f'  strb r0, [r8, #{BG_ACTIVE:#x}]',
        f'  strb r0, [r8, #{BG_FRESH:#x}]',
        '  movs r0, #0',
        f'  strb r0, [r8, #{BG_GONE:#x}]',
        '  add sp, sp, #8',
        '  pop {r4, r5, r6, r7, r8, r9, pc}',
        'mq_dec_nopic:',
        '  ldr r0, [sp, #4]',
        f'  bl {FSCLOSE:#x}',
        '  b mq_dec_negative',
        'mq_dec_negative0:',               # no frame allocated yet
        '  sub sp, sp, #8',
        'mq_dec_negative:',
        '  movs r0, #2',
        '  strb r0, [r5, #0x11]',          # entry result = negative
        f'  ldrb r0, [r8, #{BG_ACTIVE:#x}]',
        f'  strb r0, [r8, #{BG_GONE:#x}]',  # gone = was active
        '  movs r0, #0',
        f'  strb r0, [r8, #{BG_ACTIVE:#x}]',
        f'  strb r0, [r8, #{BG_FRESH:#x}]',
        '  add sp, sp, #8',
        '  pop {r4, r5, r6, r7, r8, r9, pc}',
        # Local: capture the row buffer's current row (the one
        # the consumer just decoded) into store row BG_SY.
        # Clobbers r0-r3; preserves the decode registers.
        'mq_dec_row:',
        '  push {r4, r5, r6, lr}',
        f'  ldr r4, ={CTX:#x}',
        '  ldr r4, [r4, #0x28]',           # row buffer
        f'  ldr r5, ={data["struct"]}',
        f'  ldrh r0, [r8, #{BG_SY:#x}]',
        f'  movs r1, #{BG_W}',
        '  mul r0, r0, r1',
        '  add r5, r5, r0, lsl #1',        # dest store row
        '  movs r6, #0',                   # sx
        'mq_dec_rpx:',
        f'  ldrh r0, [r8, #{BG_CW:#x}]',
        '  mul r0, r6, r0',
        f'  movs r1, #{BG_W}',
        '  udiv r0, r0, r1',               # (sx * CW) / BG_W
        f'  ldrh r1, [r8, #{BG_X0:#x}]',
        '  add r0, r0, r1',                # cx
        '  ldrh r0, [r4, r0, lsl #1]',     # produced pixel
        '  bl mq_dec_mix',
        '  strh r0, [r5]',
        '  add r5, r5, #2',
        '  add r6, r6, #1',
        f'  cmp r6, #{BG_W}',
        '  blo mq_dec_rpx',
        '  pop {r4, r5, r6, pc}',
        # Local: darken one RGB565 pixel (r0) by the theme
        # captured at decode. Dark: 45 percent of each channel
        # (a 55 percent mix toward black). Light: 25 percent of
        # each channel plus 75 percent of the paper colour
        # [242, 237, 230] (R5 29, G6 59, B5 28). Clobbers
        # r0-r3 and ip; the divisions are exact.
        'mq_dec_mix:',
        '  lsr r2, r0, #11',               # R5
        '  lsr r3, r0, #5',
        '  and r3, r3, #63',               # G6
        '  and r0, r0, #31',               # B5
        f'  ldr ip, ={S}',
        f'  ldrb ip, [ip, #{BG_THEME:#x}]',
        '  cmp ip, #0',
        '  bne mq_dec_mix_light',
        '  movs ip, #45',
        '  mul r2, r2, ip',
        '  mul r3, r3, ip',
        '  mul r0, r0, ip',
        '  movs ip, #100',
        '  udiv r2, r2, ip',
        '  udiv r3, r3, ip',
        '  udiv r0, r0, ip',
        '  b mq_dec_mix_join',
        'mq_dec_mix_light:',
        '  movs ip, #25',
        '  mul r2, r2, ip',
        '  mul r3, r3, ip',
        '  mul r0, r0, ip',
        '  ldr ip, =2175',                 # 29 * 75
        '  add r2, r2, ip',
        '  ldr ip, =4425',                 # 59 * 75
        '  add r3, r3, ip',
        '  movw ip, #2100',                # 28 * 75
        '  add r0, r0, ip',
        '  movs ip, #100',
        '  udiv r2, r2, ip',
        '  udiv r3, r3, ip',
        '  udiv r0, r0, ip',
        'mq_dec_mix_join:',
        '  lsl r2, r2, #11',
        '  lsl r3, r3, #5',
        '  orr r2, r2, r3',
        '  orr r0, r2, r0',
        '  bx lr',
    ]
    loccase = [
        # r0 = locator case head, r1 = handle, r2 = out cell.
        # The FLAC, APE and WAV picture locators are case bodies
        # inside the locator dispatch: they run on the dispatch's
        # stack frame (the register push set plus a 0x224-byte
        # frame), read r5 = handle and r6 = out cell, and leave
        # through the shared epilogue at 0x03083712, which restores
        # the pushed registers and returns through the pushed pc
        # slot. This helper rebuilds exactly that state, with the
        # pc slot holding the trampoline below, and jumps in.
        # Returns the case's result in r0. Preserves r4-r11 except
        # through the case's own epilogue discipline (it restores
        # what it received); clobbers r0-r3 and ip.
        'mq_loccase:',
        '  push {lr}',
        '  mov ip, r0',                    # case head
        '  adds ip, ip, #1',               # bx needs the thumb bit
        '  adr r0, mq_locret',
        '  add r0, r0, #1',                # thumb bit for the pop
        '  mov lr, r0',
        '  push {r4, r5, r6, r7, r8, sb, lr}',
        '  mov r5, r1',                    # handle
        '  mov r6, r2',                    # out cell
        '  sub sp, sp, #0x224',
        '  bx ip',
        'mq_locret:',
        '  pop {lr}',
        '  bx lr',
    ]
    slice_ = [
        # r0 = x0, r1 = y0, r2 = x1, r3 = y1 (inclusive, already
        # clipped to the client area), ip = tint flag (0 plain,
        # 1 mixed halfway toward the accent). Draw the stored
        # background's slice for the rect: output pixel (px, py)
        # is store[(py - 40) * BG_H / 280][px * BG_W / 240],
        # drawn row by row through the row blitter with the row
        # built in the tail line buffer. Preserves r4-r10.
        'mq_slice:',
        '  push {r4, r5, r6, r7, r8, r9, r10, lr}',
        '  mov r5, r0',                    # x0
        '  mov r6, r1',                    # py
        '  mov r7, r2',                    # x1
        '  mov r8, r3',                    # y1
        '  mov r9, ip',                    # tint flag
        f'  ldr r10, ={PAL_ACCENT3:#x}',
        '  ldrh r10, [r10]',               # accent (tint target)
        'mq_slice_row:',
        f'  sub r0, r6, #{ART_Y0}',
        f'  movs r1, #{BG_H}',
        '  mul r0, r0, r1',
        f'  movw r1, #{ART_H}',
        '  udiv r0, r0, r1',               # sy
        f'  movs r1, #{BG_W}',
        '  mul r0, r0, r1',
        f'  ldr r1, ={data["struct"]}',
        '  add r0, r1, r0, lsl #1',        # store row
        '  mov r4, r5',                    # px = x0
        f'  ldr r1, ={LINEBUF:#x}',
        'mq_slice_px:',
        f'  movs r2, #{BG_W}',
        '  mul r2, r4, r2',
        f'  movw r3, #{ART_W}',
        '  udiv r2, r2, r3',               # sx
        '  ldrh r2, [r0, r2, lsl #1]',     # stored pixel
        '  cmp r9, #0',
        '  beq mq_slice_put',
        # Tint: each channel averaged with the accent's (r9
        # is free once the flag is tested).
        '  and r9, r2, #31',               # B5 of the pixel
        '  lsr ip, r10, #5',
        '  and ip, ip, #63',               # G6 of the accent
        '  lsr r3, r2, #5',
        '  and r3, r3, #63',               # G6 of the pixel
        '  add r3, r3, ip',
        '  lsr r3, r3, #1',
        '  lsl r3, r3, #5',                # G result
        '  lsr ip, r2, #11',               # R5 of the pixel
        '  lsr r2, r10, #11',              # R5 of the accent
        '  add ip, ip, r2',
        '  lsr ip, ip, #1',
        '  lsl ip, ip, #11',               # R result
        '  orr r3, r3, ip',
        '  and ip, r10, #31',              # B5 of the accent
        '  add r9, r9, ip',
        '  lsr r9, r9, #1',                # B result
        '  orr r2, r3, r9',                # composed pixel
        '  movs r9, #1',                   # restore the tint flag
        'mq_slice_put:',
        '  strh r2, [r1]',
        '  add r1, r1, #2',
        '  add r4, r4, #1',
        '  cmp r4, r7',
        '  bls mq_slice_px',
        '  sub sp, sp, #8',
        '  movs r0, #0x10',
        '  str r0, [sp]',                  # stack arg: mode
        f'  ldr r0, ={LINEBUF:#x}',
        '  str r0, [sp, #4]',              # stack arg: pixels
        '  mov r0, r5',
        '  mov r1, r6',
        '  sub r2, r7, r5',
        '  add r2, r2, #1',                # width
        '  movs r3, #1',
        f'  bl {BITMAP:#x}',
        '  add sp, sp, #8',
        '  add r6, r6, #1',
        '  cmp r6, r8',
        '  bls mq_slice_row',
        '  pop {r4, r5, r6, r7, r8, r9, r10, pc}',
    ]
    fillsub = [
        # The fill helper's contract (r0 = x0, r1 = y0, r2 = x1,
        # r3 = y1, colour at [sp]), entered by BL from the
        # painter's fill call sites and from mq_show. While a
        # background is installed and the fill's colour is one
        # of the flat colours the art replaces (the ground, the
        # separator, the palette ground), the matching slice of
        # the store is drawn instead; the accent colour draws
        # the slice mixed halfway toward the accent, which is
        # what keeps the selection band and the stepper's erase
        # (both accent) distinguishable over art. Anything else
        # (no background, a colour outside the set, a rect
        # outside the client area) tail-branches to the stock
        # fill with its arguments untouched. The first
        # instructions touch only ip and the saved registers, so
        # the pass-through stack is exactly the caller's.
        'mq_fillsub:',
        '  ldr ip, [sp]',                  # the fill's colour
        '  push {r4, r5, r6, r7, r8, r9, lr}',
        '  mov r4, r0',                    # x0
        '  mov r5, r1',                    # y0
        '  mov r6, r2',                    # x1
        '  mov r7, r3',                    # y1
        '  mov r8, ip',                    # colour
        f'  ldr r9, ={S}',
        f'  ldrb r0, [r9, #{BG_ACTIVE:#x}]',
        '  cmp r0, #0',
        '  beq mq_fill_stock',             # no background
        # Clip the rect to the client area.
        '  cmp r4, #0',
        '  it lt',
        '  movlt r4, #0',
        '  cmp r5, #40',
        '  it lt',
        '  movlt r5, #40',
        '  movw r0, #239',
        '  cmp r6, r0',
        '  it gt',
        '  movgt r6, r0',
        '  movw r0, #319',
        '  cmp r7, r0',
        '  it gt',
        '  movgt r7, r0',
        '  cmp r4, r6',
        '  bgt mq_fill_stock',
        '  cmp r5, r7',
        '  bgt mq_fill_stock',
        # Colour class: accent tints; ground, separator and
        # palette ground draw the plain slice; the rest is
        # stock.
        f'  ldr r0, ={PAL_ACCENT3:#x}',
        '  ldrh r0, [r0]',
        '  cmp r8, r0',
        '  beq mq_fill_tint',
        '  cmp r8, #0',
        '  beq mq_fill_plain',             # dark ground
        f'  ldr r0, ={LCTX:#x}',
        '  ldrh r0, [r0]',
        '  cmp r8, r0',
        '  beq mq_fill_plain',             # separator colour
        f'  ldr r0, ={PAL_BG:#x}',
        '  ldrh r0, [r0]',
        '  cmp r8, r0',
        '  bne mq_fill_stock',
        'mq_fill_plain:',
        '  movs ip, #0',
        '  b mq_fill_draw',
        'mq_fill_tint:',
        '  movs ip, #1',
        'mq_fill_draw:',
        '  mov r0, r4',
        '  mov r1, r5',
        '  mov r2, r6',
        '  mov r3, r7',
        '  bl {SLICE}',
        '  pop {r4, r5, r6, r7, r8, r9, pc}',
        'mq_fill_stock:',
        '  mov r0, r4',
        '  mov r1, r5',
        '  mov r2, r6',
        '  mov r3, r7',
        '  pop {r4, r5, r6, r7, r8, r9, lr}',
        f'  b {FILL:#x}',
    ]
    show = [
        # Gate exit hook. Three duties, in order. (1) When the
        # background went away on this paint (BG_GONE), repaint
        # the client area with the theme's flat ground, exactly
        # stock: black in the dark theme, the palette ground in
        # the light theme. (2) When a background was installed
        # on this paint (BG_FRESH), draw the store's slice over
        # the whole client area; the row loop of this paint drew
        # flat bands (or, when the previous selection was
        # pictured, substituted slices of the old art), and the
        # install draw is what makes the new art the paint's
        # final word. (3) When a label render is owed
        # (LABEL_FRESH: set by the selection branch and by any
        # key), erase the stock name the row loop drew and
        # render the label in its place, in the stock rect. The
        # erase goes through mq_fillsub with the accent colour,
        # so over an installed background it draws the tinted
        # slice and otherwise the flat accent, as stock did.
        # Steady paints do none of this: the background keeps
        # itself through the fill hooks, and while the marquee
        # is in its scroll phase the stepper owns the selected
        # row's text. Preserves r0 and r4-r6.
        'mq_show:',
        '  push {r0, r4, r5, r6, r7, lr}',
        f'  ldr r4, ={S}',
        f'  ldrb r5, [r4, #{BG_GONE:#x}]',
        '  movs r0, #0',
        f'  strb r0, [r4, #{BG_GONE:#x}]',
        '  cmp r5, #0',
        '  beq mq_show_fresh',
        # (1) ground restore, the exact stock flat.
        f'  ldr r0, ={SAVEINFO:#x}',
        '  ldrb r0, [r0, #0x2d8]',
        '  cmp r0, #0',
        '  bne mq_show_ground_light',
        '  movs r6, #0',                   # dark ground
        '  b mq_show_ground_go',
        'mq_show_ground_light:',
        f'  ldr r6, ={PAL_BG:#x}',
        '  ldrh r6, [r6]',                 # palette ground
        'mq_show_ground_go:',
        '  sub sp, sp, #16',
        '  str r6, [sp]',                  # fill colour (stack)
        '  movs r0, #0',
        f'  movs r1, #{ART_Y0}',
        '  movw r2, #239',
        '  movw r3, #319',
        f'  bl {FILL:#x}',
        '  add sp, sp, #16',
        'mq_show_fresh:',
        f'  ldrb r5, [r4, #{BG_FRESH:#x}]',
        '  movs r0, #0',
        f'  strb r0, [r4, #{BG_FRESH:#x}]',
        '  cmp r5, #0',
        '  beq mq_show_label',
        # (2) the install draw: the whole client area, plain,
        # except the selected row's band, which is drawn as
        # the tinted slice, so every paint ends in the same
        # state (plain art, tinted selected band) whatever the
        # row loop did before the gate resolved the selection.
        '  bl {NODE}',                    # r1 = selected row
        '  movs r7, #40',
        '  mul r7, r1, r7',
        '  add r7, r7, #40',               # band top
        '  cmp r7, #40',
        '  beq mq_show_band',
        '  movs ip, #0',
        '  movs r0, #0',
        '  movs r1, #40',
        '  movw r2, #239',
        '  sub r3, r7, #1',
        '  bl {SLICE}',                    # above the band
        'mq_show_band:',
        '  movs ip, #1',
        '  movs r0, #0',
        '  mov r1, r7',
        '  movw r2, #239',
        '  add r3, r7, #39',
        '  bl {SLICE}',                    # the band, tinted
        '  add r0, r7, #40',
        '  movw r3, #319',
        '  cmp r0, r3',
        '  bhi mq_show_label',
        '  movs ip, #0',
        '  mov r1, r0',
        '  movs r0, #0',
        '  movw r2, #239',
        '  movw r3, #319',
        '  bl {SLICE}',                    # below the band
        'mq_show_label:',
        f'  ldrb r5, [r4, #{LABEL_FRESH:#x}]',
        '  movs r0, #0',
        f'  strb r0, [r4, #{LABEL_FRESH:#x}]',
        '  cmp r5, #0',
        '  beq mq_show_out',
        '  bl {NODE}',                    # r0 = node, r1 = row
        '  cmp r0, #0',
        '  beq mq_show_out',
        '  mov r7, r1',                    # selected row
        '  ldrb r0, [r4, #8]',             # phase
        '  cmp r0, #1',
        '  beq mq_show_out',               # SCROLL: stepper's row
        '  ldr r0, [r4, #0x14]',           # active string
        '  cmp r0, #0',
        '  beq mq_show_out',               # no label (fallback)
        '  movs r0, #11',
        '  bl mq_show_fill',
        '  movs r0, #11',
        '  bl mq_show_render',
        'mq_show_out:',
        '  pop {r0, r4, r5, r6, r7, pc}',
        # Local: fill the selected row's text rect from x0 (r0)
        # to 231 with the accent colour, through mq_fillsub so
        # an installed background shows through as the tinted
        # slice. Clobbers r0-r3.
        'mq_show_fill:',
        '  push {r4, lr}',
        '  movs r4, #40',
        '  mul r4, r7, r4',
        '  add r4, r4, #53',               # text y0
        '  sub sp, sp, #16',
        f'  ldr r1, ={PAL_ACCENT3:#x}',
        '  ldrh r1, [r1]',
        '  str r1, [sp]',                  # fill colour (stack)
        '  mov r1, r4',
        '  movw r2, #231',
        '  add r3, r4, #15',
        '  bl {FILLSUB}',
        '  add sp, sp, #16',
        '  pop {r4, pc}',
        # Local: render the active string into the selected row's
        # text rect from x0 (r0), mirroring the painter's own row
        # render (pen from the palette cell, the draw parameter
        # set and restored around the call).
        'mq_show_render:',
        '  push {r4, r5, lr}',
        f'  ldr r4, ={S}',
        '  movs r5, #40',
        '  mul r5, r7, r5',
        '  add r5, r5, #53',               # text y0
        '  sub sp, sp, #16',
        '  strh r0, [sp, #8]',
        '  strh r5, [sp, #10]',
        '  movw r0, #231',
        '  strh r0, [sp, #12]',
        '  add r0, r5, #15',
        '  strh r0, [sp, #14]',
        '  ldrh r0, [sl]',
        '  strh r0, [sb]',                 # pen = palette cell
        '  movs r0, #1',
        f'  bl {PENSET:#x}',
        '  mov r5, r0',                    # previous parameter
        '  add r0, sp, #8',
        '  mov r1, r0',
        '  ldr r2, [r4, #0x14]',           # active string
        '  movs r3, #0',
        f'  bl {RENDER:#x}',
        '  mov r0, r5',
        f'  bl {PENSET:#x}',               # restore parameter
        '  add sp, sp, #16',
        '  pop {r4, r5, pc}',
    ]

    def fill(lines):
        keys = ('{NODE}', '{UNITS}', '{COMPOSE}', '{REGISTER}',
                '{TAGS}', '{TAGSTR}', '{IDENT}', '{BG}',
                '{DECODE}', '{LOCCASE}', '{SLICE}', '{SHOW}',
                '{FILLSUB}')
        return [ln.format(NODE=f'{xref["node"]:#x}',
                          UNITS=f'{xref["units"]:#x}',
                          COMPOSE=f'{xref["compose"]:#x}',
                          REGISTER=f'{xref["register"]:#x}',
                          TAGS=f'{xref["tags"]:#x}',
                          TAGSTR=f'{xref["tagstr"]:#x}',
                          IDENT=f'{xref["ident"]:#x}',
                          BG=f'{xref["bg"]:#x}',
                          DECODE=f'{xref["decode"]:#x}',
                          LOCCASE=f'{xref["loccase"]:#x}',
                          SLICE=f'{xref["slice"]:#x}',
                          SHOW=f'{xref["show"]:#x}',
                          FILLSUB=f'{xref["fillsub"]:#x}')
                if any(k in ln for k in keys) else ln
                for ln in lines]
    return [('gate', fill(gate)), ('node', node), ('units', units),
            ('compose', compose), ('register', register),
            ('key', key), ('toggle', toggle), ('exit', exit_),
            ('tags', fill(tags)), ('tagstr', fill(tagstr)),
            ('ident', ident), ('bg', fill(bg)),
            ('decode', fill(decode)), ('loccase', loccase),
            ('slice', fill(slice_)), ('fillsub', fill(fillsub)),
            ('show', fill(show))]


import re

_BRANCH_LABEL = re.compile(
    r'^(\s*)(b(?:eq|ne|lo|ls|hi|hs|cc|cs|ge|lt|gt|le|mi|pl|vs|vc)?)'
    r'\s+(mq_\S+|gate_\S+)$')


def widen(lines):
    """Force wide (4-byte) encodings for every label branch.

    Keystone mis-sizes short conditional branches between its two
    passes, which shifts its internal address counter and corrupts
    the displacement of every later absolute BL by +2 (observed:
    calls to the event helpers landed one halfword into the callee).
    Wide encodings size identically in both passes. Absolute-address
    branches (bl 0x...) are already 4 bytes and are left alone, as
    are bx lr and the push/pop lines (their braces are not labels).
    """
    out = []
    for ln in lines:
        m = _BRANCH_LABEL.match(ln)
        if m:
            out.append(f'{m.group(1)}{m.group(2)}.w {m.group(3)}')
        else:
            out.append(ln)
    return out


def assemble(state, buf, xref=None, data=None):
    # Cross-routine calls use absolute addresses (Keystone resolves
    # only labels inside one listing). A dummy first pass fixes every
    # routine's length (a BL is 4 bytes whatever its target), then
    # the real pass links against the computed entries.
    if xref is None:
        xref = {k: BASE for k in ('node', 'units', 'compose',
                                  'register', 'tags', 'tagstr',
                                  'ident', 'bg', 'decode',
                                  'loccase', 'slice', 'show',
                                  'fillsub')}
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_V8)
    payload = bytearray()
    entries = {}
    for name, lines in routines(state, buf, xref, data):
        addr = BASE + len(payload)
        code, _ = ks.asm('\n'.join(widen(lines)), addr)
        entries[name] = addr
        payload += bytes(code)
    return bytes(payload), entries


def verify_branches(payload, entries):
    """Every branch in the payload must land exactly: intra-payload
    targets on a decoded instruction boundary of their own routine
    (or on another routine's entry), extra-payload targets on the
    known stock entry points. Disassembly is per routine because
    each routine's literal pool sits between routines."""
    allowed = {SET_BIT, CLEAR_BIT, TEST_BIT, MEASURE, MQ_SETUP,
               FSOPEN, FSCLOSE, TAGPARSE, BZERO,
               RENDER, FILL, PENSET, SEEK, SCAN, SETUP, CONSUMER,
               SET_D4, SET_D8, BITMAP,
               KEY_SITE + 4} | set(entries.values())
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    starts = sorted(entries.items(), key=lambda kv: kv[1])
    for i, (name, addr) in enumerate(starts):
        end = (starts[i + 1][1] if i + 1 < len(starts)
               else BASE + len(payload))
        insns = list(md.disasm(payload[addr - BASE:end - BASE], addr))
        bounds = {x.address for x in insns}
        for x in insns:
            if not (x.mnemonic == 'bl' or x.mnemonic == 'blx'
                    or x.mnemonic.startswith('b')):
                continue
            if not x.op_str.startswith('#0x'):
                continue
            tgt = int(x.op_str[1:], 16)
            if BASE <= tgt < BASE + len(payload):
                if tgt not in bounds and tgt not in allowed:
                    raise ValueError(
                        f'{name}: branch at {x.address:#x} lands '
                        f'mid-instruction at {tgt:#x}')
            elif tgt not in allowed:
                raise ValueError(
                    f'{name}: branch at {x.address:#x} targets '
                    f'unexpected address {tgt:#x}')


def roundtrip(payload, entries):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    starts = sorted(entries.items(), key=lambda kv: kv[1])
    for i, (name, addr) in enumerate(starts):
        end = (starts[i + 1][1] if i + 1 < len(starts)
               else BASE + len(payload))
        insns = list(md.disasm(payload[addr - BASE:end - BASE], addr))
        if not insns or insns[0].address != addr:
            raise ValueError(f'{name}: round-trip disassembly failed')
        text = ' '.join(f'{x.mnemonic} {x.op_str}' for x in insns)
        if 'udf' in text or '.byte' in text:
            raise ValueError(f'{name}: round-trip contains bad bytes')


def branch(site, target, link=False):
    """Thumb-2 B/BL encoder (same construction as build_focus.py)."""
    delta = target - (site + 4)
    if delta & 1 or not -(1 << 24) <= delta < (1 << 24):
        raise ValueError('invalid branch displacement')
    s, i1, i2 = (delta >> 24) & 1, (delta >> 23) & 1, (delta >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    return struct.pack('<HH', 0xF000 | (s << 10) | ((delta >> 12) & 0x3FF),
                       (0xD000 if link else 0x9000) | (j1 << 13)
                       | (j2 << 11) | ((delta >> 1) & 0x7FF))


def stock_bytes(stock, module, address, length):
    # Mirrors the framework's own patch addressing (build.py
    # apply_patches): the module is declared, never searched,
    # because the window overlays share exec ranges.
    img = Image(stock)
    off, _ln = img.module_region(module, 'code')
    base = img.modules[module]['code_exec']
    rel = address - base
    return stock[off + rel:off + rel + length]


PATCH_DEFS = [
    # (number, name, site, target-entry, note)
    ('0300', 'marquee-painter-tail-gate', GATE_SITE, 'gate',
     'the painter tail marquee test site (bl test-noclear 0x148); the '
     'gate decides per paint whether the stock stepper may advance'),
    ('0301', 'marquee-key-reset', KEY_SITE, 'key',
     'the browser Key callback entry (displaced push.w replicated by '
     'the stub, which resumes the stock handler at site + 4)'),
    ('0302', 'marquee-exit-reset', EXIT_SITE, 'exit',
     'the browser exit callback (displaced mov.w r0, #0x148 performed '
     'by the stub before its tail branch to the stock clear helper)'),
    ('0303', 'marquee-view-toggle', TOGGLE_SITE, 'toggle',
     'inside the browser Key handler where r4 holds the final event '
     'word (displaced ldr.w sb, [pc, #0x400] performed by the stub); '
     'a long press of Vol+ flips the tag/file view mode byte'),
    ('0310', 'marquee-fill-mode-a-band', FILLA_SITE, 'fillsub',
     'the mode A row loop band fill call; the stub substitutes '
     'the background slice for the flat ground while a '
     'background is installed', 31),
    ('0311', 'marquee-fill-mode-a-accent', FILLB_SITE, 'fillsub',
     'the mode A selected band fill call; the stub substitutes '
     'the accent-tinted background slice while a background is '
     'installed', 31),
    ('0312', 'marquee-fill-mode-a-separator', FILLC_SITE, 'fillsub',
     'the mode A separator fill call; the stub substitutes the '
     'background slice while a background is installed', 31),
    ('0313', 'marquee-fill-mode-b-accent', FILLD_SITE, 'fillsub',
     'the mode B selected band fill call; same substitution as '
     '0311', 31),
    ('0314', 'marquee-fill-window-ground', FILLE_SITE, 'fillsub',
     'the paint framework window ground fill call (module 0); '
     'the stub substitutes the full background slice while a '
     'background is installed, and passes through untouched '
     'for every other window', 0),
    ('0315', 'marquee-fill-stepper-erase', FILLF_SITE, 'fillsub',
     'the marquee stepper text erase call (module 0); the stub '
     'substitutes the accent-tinted slice inside the browser '
     'while a background is installed, and passes through '
     'untouched elsewhere', 0),
]


def main():
    stock_path = REPO / 'DP3_V137.img'
    stock = stock_path.read_bytes()
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('stock image hash mismatch; refusing')
    # Sizing pass with placeholder data addresses, then the real
    # pass at the final addresses (literal sizes are value-stable;
    # the equality assert proves it for this source).
    probe, probe_entries = assemble(BASE + 0x1000, BASE + 0x1020)
    code_len = (len(probe) + 3) & ~3
    state = BASE + code_len
    buf = state + STATE_LEN
    exttab = buf + BUF_UNITS * 2
    struct = (exttab + len(TAG_EXTS) * 3 + 3) & ~3
    keytab = (struct + STRUCT_SPAN + 3) & ~3
    cache = keytab + KEY_ENTRIES * KEY_LEN
    picext = cache + CACHE_ENTRIES * CACHE_ENTRY_LEN
    data = {'struct': struct, 'cache': cache, 'exttab': exttab,
            'picext': picext, 'keytab': keytab}
    payload_code, entries = assemble(state, buf, probe_entries, data)
    if len(payload_code) != len(probe):
        raise ValueError('code length changed between passes')
    roundtrip(payload_code, entries)
    verify_branches(payload_code, entries)

    total = picext + len(PIC_ROUTES) * PIC_ENTRY_LEN - BASE
    if total > 7436:
        raise ValueError(f'payload {total} bytes exceeds the '
                         f'module 31 growth window (7,436)')
    payload = bytearray(payload_code)
    payload += bytes(total - len(payload))
    for i, ext in enumerate(TAG_EXTS):
        payload[exttab - BASE + 3 * i:exttab - BASE + 3 * i + 3] = ext
    for i, (ext, route) in enumerate(PIC_ROUTES):
        at = picext - BASE + PIC_ENTRY_LEN * i
        payload[at:at + 3] = ext
        payload[at + 4:at + 8] = route.to_bytes(4, 'little')
    assert len(payload) == total
    (HERE / 'marquee_payload.bin').write_bytes(bytes(payload))

    lines = []
    for num, name, site, entry, note, *mod in PATCH_DEFS:
        module = mod[0] if mod else 31
        expect = stock_bytes(stock, module, site, 4).hex()
        link = site in (GATE_SITE, TOGGLE_SITE, FILLA_SITE,
                        FILLB_SITE, FILLC_SITE, FILLD_SITE,
                        FILLE_SITE, FILLF_SITE)
        replace = branch(site, entries[entry], link=link).hex()
        text = (f'# Browser marquee (experimental variant): {name}.\n'
                f'# Design and census: patches/browser_marquee/'
                f'design.md.\n'
                f'name: {name}\n'
                f'kind: module\n'
                f'module: {module}\n'
                f'region: code\n'
                f'address: {site:#x}\n'
                f'gate: stock byte precondition; variant-only patch, '
                f'never in the default manifest; validated by '
                f'test_browser_marquee.py under emulation\n'
                f'rationale: Hook at {note}. Payload routine at '
                f'{entries[entry]:#x} in the module 31 code growth '
                f'(marquee_payload.bin).\n'
                f'expect: {expect}\n'
                f'replace: {replace}\n')
        (HERE / f'{num}-{name}.patch').write_text(text)
        lines.append(f'{num}-{name}.patch')

    default_manifest = (REPO / 'patches' / 'framework' / 'patches'
                        / 'manifest.txt').read_text().splitlines()
    base_entries = [ln.strip() for ln in default_manifest
                    if ln.strip() and not ln.startswith('#')]
    out = ['# Browser marquee variant manifest: the default 32 plus '
           'the ten marquee hooks in this directory. Use ONLY with '
           '--grow 31:code:marquee_payload.bin --tail '
           'marquee_tail.bin (see design.md).', '']
    out += [f'../framework/patches/{n}' for n in base_entries]
    out += lines
    (HERE / 'manifest.txt').write_text('\n'.join(out) + '\n')

    # The package-gap tail ships as plain zeros: the payload
    # uses its first 480 bytes as the slice line buffer (the
    # census home; see the module docstring), and the rest is
    # unused.
    (HERE / 'marquee_tail.bin').write_bytes(bytes(TAIL_LEN))
    print(f'payload: {len(payload)} bytes (code {len(payload_code)}, '
          f'state {STATE_LEN} at {state:#x}, buffer {BUF_UNITS * 2} '
          f'at {buf:#x}, ext table {len(TAG_EXTS) * 3} at '
          f'{exttab:#x}, struct span {STRUCT_SPAN} at {struct:#x}, '
          f'key table {KEY_ENTRIES} x {KEY_LEN} at {keytab:#x}, '
          f'cache {CACHE_ENTRIES} x {CACHE_ENTRY_LEN} '
          f'(tag buffer {TAG_BUF_UNITS * 2}) at {cache:#x}, '
          f'picture routes {len(PIC_ROUTES) * PIC_ENTRY_LEN} at '
          f'{picext:#x}); background store {BG_W} x {BG_H} '
          f'RGB565 ({BG_BYTES} bytes) in the struct span; slice '
          f'line buffer 480 at {LINEBUF:#x} in the gap tail '
          f'({TAIL_LEN} bytes)')
    for name, addr in entries.items():
        print(f'  {name:9s} {addr:#x}')
    print(f'manifest entries: {len(base_entries)} + {len(lines)}')


if __name__ == '__main__':
    main()
