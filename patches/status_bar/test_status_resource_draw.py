"""Census native icon draws over a nonblack ground; no firmware mutation.

These isolated resource calls identify possible fixed-color sources. They do
not establish which status-window path produced a reported physical box.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'patches/design_refresh_v4')]
from test_keyed_transport import Machine, DRAWAT, fb_fill, fb_read

BASELINE = '08054971d2a5ef837c5186a8b31e20f720bedbc1ddb41978885b0f4e32d105c9'
GROUND = 0x7222

def check(raw):
    assert hashlib.sha256(raw).hexdigest() == BASELINE, 'accepted release changed; rebaseline explicitly'
    results = []
    # Resource 133 is drawn at (10,7) by the real player repaint at
    # 0x0307F024. Others are small neighboring indicator resources;
    # their live status-window call sites remain to be traced.
    for rid in (133, 143, 144, *range(145, 155)):
        m = Machine(raw, real_store=True)
        m.stage([rid])
        m.u.mem_write(0x030238B8, bytes(40))
        m.u.mem_write(0x0302385C, struct.pack('<6H', 0xffff, GROUND, 1, 0, 240, 320))
        fb_fill(m, GROUND)
        m.call(DRAWAT, rid, 10, 7)
        e = m.entries[rid]
        pixels = fb_read(m, 10, 7, e['width'], e['height'])
        black = sum(c == 0 for c in pixels.values())
        dark = sum(c == 0x10a2 for c in pixels.values())
        results.append(dict(resource=rid, width=e['width'], height=e['height'],
                            black_pixels=black, stock_dark_pixels=dark,
                            changed_pixels=sum(c != GROUND for c in pixels.values())))
    return dict(baseline_sha256=BASELINE, native_draw_cases=len(results),
                resources=results, live_status_writer_identified=False,
                release_image_modified=False)

if __name__ == '__main__':
    print(json.dumps(check((ROOT / 'release/DP3_V137_CE.img').read_bytes()), indent=2))
