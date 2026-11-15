"""Draft-only optimization: compare an in-memory prototype with accepted CE.

No on-disk image, manifest or release artifact is modified.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'patches/player_ui')]
from rknano_image import Image
from build_player_repaint import FULL, payloads
from test_player_repaint import draw
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

BASELINE = '08054971d2a5ef837c5186a8b31e20f720bedbc1ddb41978885b0f4e32d105c9'

def check(raw):
    assert hashlib.sha256(raw).hexdigest() == BASELINE, 'rebaseline explicitly after release changes'
    image = Image(raw)
    off, _ = image.module_region(0, 'code')
    at = off + FULL - image.modules[0]['code_exec']
    baseline = payloads()[1]
    assert raw[at:at + len(baseline)] == baseline
    # Preserve the accepted prologue, native window call, stores and fallback.
    # Two consecutive stores per loop halve loop-control work, keeping the
    # exact same sequence of 16-byte framebuffer writes.
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(
        '''push {r4,r5,r6,lr};ldr r6,=0x30238b8;ldrh r4,[r6];cbnz r4,fallback;ldr r4,[r6,#20];cbnz r4,fallback;
        ldrh r4,[sp,#16];orr r4,r4,r4,lsl #16;bl 0x3063f10;
        mov r1,r4;mov r2,r4;mov r3,r4;ldr r0,=0x30065a8;movw r5,#3600;
        upper:stmia r0!,{r1,r2,r3,r4};stmia r0!,{r1,r2,r3,r4};subs r5,#1;bne upper;
        ldr r0,=0x306f224;movw r5,#1200;
        lower:stmia r0!,{r1,r2,r3,r4};stmia r0!,{r1,r2,r3,r4};subs r5,#1;bne lower;
        movs r0,#1;str r0,[r6,#12];movs r0,#0;strh r0,[r6,#32];strh r0,[r6,#34];pop {r4,r5,r6,pc};
        fallback:pop.w {r4,r5,r6,lr};b.w 0x30632fa;.ltorg''', FULL)[0])
    assert len(code) <= 98, 'reserved pocket exceeded'
    prototype = bytearray(raw)
    prototype[at:at + len(code)] = code
    cases = 0
    counts = None
    for rotation in (0, 1):
        for color in (0, 0xffff, 0x39c7, 0x7222):
            args = (0, 0, 239, 319, color)
            before = draw(raw, FULL, args, rotation=rotation, count=True)
            after = draw(bytes(prototype), FULL, args, rotation=rotation, count=True)
            assert before[:2] == after[:2], 'framebuffer/display-context difference'
            # draw independently enforces stack, callee registers and write bounds.
            if rotation == 0:
                assert after[2] < before[2]
                counts = (before[2], after[2])
            else:
                assert before[2] == after[2], 'fallback work changed'
            cases += 1
    return dict(cases=cases, framebuffer_bytes_per_case=153600,
                context_bytes_per_case=40, mismatching_bytes=0,
                baseline_instructions=counts[0], prototype_instructions=counts[1],
                instruction_ratio=round(counts[1]/counts[0], 4),
                prototype_code_bytes=len(code), release_image_modified=False)

if __name__ == '__main__':
    print(json.dumps(check((ROOT / 'release/DP3_V137_CE.img').read_bytes()), indent=2))
