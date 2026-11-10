#!/usr/bin/env python3
"""Full harness validation driver for the module 72 Opus transplant.

Runs, in stages (argv[1], default 'all'):
  A  the shipped candidate (work/opus_transplant/module72_opus.bin) on
     opus_b.opus: the open is expected to hang; the runtime fault dump
     is captured from the console port.
  B  stock module 72 control: wma_small.wma decode + comparison, and
     stock behaviour on opus_b.opus.
  C  the no-zeroing control build (module72_opus_onstock.bin, built by
     applying the HIFIEC52 diff to stock bytes without transplant.py's
     zero-first step): the full route-plan matrix (decode comparisons,
     seek, gapless miniature, canaries, negative Vorbis test).
  D  efficiency: instruction counts, variant Opus vs stock WMA on the
     same 10 s excerpt.

Writes validation_results.json and prints a summary. Traces go to
logs/<stage>.log. Run with the project venv python.
"""
import contextlib
import json
import struct
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness72          # noqa: E402
import compare as cmp     # noqa: E402
from unicorn import UC_HOOK_BLOCK                     # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0           # noqa: E402

MEDIA = HERE / 'media'
LOGS = HERE / 'logs'
LOGS.mkdir(exist_ok=True)
RESULTS = {}


def fresh(media, transplant_bin=None, count=False, tag='run'):
    log = LOGS / f'{tag}.log'
    if transplant_bin is not None:
        harness72.TRANSPLANT_BIN = transplant_bin
    h = harness72.H72(media=media, transplant=transplant_bin is not None,
                      trace_path=str(log), count_insns=count)
    return h


def decode_file(media, transplant_bin=None, tag='run', count=False):
    """Boot, open, decode to EOS, close. Returns (harness, info, wall_s)."""
    t0 = time.time()
    with contextlib.redirect_stdout(open(LOGS / f'{tag}.stdout.log', 'w')):
        h = fresh(media, transplant_bin, count=count, tag=tag)
        assert h.boot(), 'boot failed'
        if count:
            h.counting = True
        inf = h.open_current()
        polls = h.decode_to_eos() if inf else 0
        closed = h.close_current() if inf else False
        if count:
            h.counting = False
    return h, inf, polls, closed, time.time() - t0


def ref(name):
    return (MEDIA / f'{name}.ref.raw').read_bytes()


# ---------------------------------------------------------------- A: shipped
def stage_a():
    out = {}
    with contextlib.redirect_stdout(open(LOGS / 'A.stdout.log', 'w')):
        h = fresh(MEDIA / 'opus_b.opus',
                  transplant_bin=harness72.WS / 'work/opus_transplant/module72_opus.bin',
                  tag='A_candidate')
        out['boot'] = h.boot()
        h.open_notified = False
        h.send_info65()
        out['open_notified'] = bool(h.run_slices(500, until=lambda: h.open_notified))
        console = []
        def hook(u, addr, size, data):
            if addr == 0x198:
                console.append(u.reg_read(UC_ARM_REG_R0) & 0xFF)
        h.u.hook_add(UC_HOOK_BLOCK, hook)
        h.send_ch1(1)
        h.run_slices(60)          # the open never returns; bounded look
        out['open_info'] = h.info_reported
        out['open_failed'] = h.open_failed
        out['console_dump'] = bytes(console).decode('latin1')
        out['hang'] = h.info_reported is None and not h.open_failed
    RESULTS['A_shipped_candidate'] = out
    print('A:', out)


# ---------------------------------------------------------------- B: stock
def stage_b():
    out = {}
    h, inf, polls, closed, wall = decode_file(MEDIA / 'wma_small.wma', None, tag='B_stock_wma')
    c = cmp.compare(bytes(h.pcm), ref('wma_small'), 2)
    out['wma_small'] = {'open': inf, 'polls': polls, 'eos': h.eos_sent,
                        'closed': closed, 'pcm_bytes': len(h.pcm), 'compare': c,
                        'wall_s': round(wall, 1)}
    # stock behaviour on an Opus file (control observation, no gate)
    with contextlib.redirect_stdout(open(LOGS / 'B2.stdout.log', 'w')):
        h2 = fresh(MEDIA / 'opus_b.opus', None, tag='B2_stock_on_opus')
        assert h2.boot()
        inf2 = h2.open_current(max_slices=600)
        out['stock_on_opus'] = {'open_info': inf2, 'open_failed': h2.open_failed,
                                'eos': h2.eos_sent}
    RESULTS['B_stock_control'] = out
    print('B:', json.dumps(out, default=str)[:600])


# ---------------------------------------------------------------- C: variant
def stage_c():
    out = {}
    variant = HERE / 'module72_opus_onstock.bin'
    # step 2: decode matrix
    matrix = {}
    for name in ('opus_b', 'opus48', 'opus44', 'opus_tags', 'opus_worst'):
        h, inf, polls, closed, wall = decode_file(MEDIA / f'{name}.opus', variant,
                                                  tag=f'C_{name}')
        c = cmp.compare(bytes(h.pcm), ref(name), inf['channels'] if inf else 2)
        matrix[name] = {'open': inf, 'polls': polls, 'eos': h.eos_sent,
                        'closed': closed, 'pcm_bytes': len(h.pcm),
                        'blocks': h.pcm_blocks[:3], 'compare': c,
                        'wall_s': round(wall, 1)}
        print(f'C {name}: frames={c.get("harness_frames")} ref={c.get("ref_frames")} '
              f'lag={c.get("lag_frames")} snr={c.get("snr_db")} max_err={c.get("max_abs_err")}')
    out['decode_matrix'] = matrix
    # negative test: a Vorbis file must fail open cleanly, not hang
    with contextlib.redirect_stdout(open(LOGS / 'C_vorbis.stdout.log', 'w')):
        hv = fresh(MEDIA / 'vorbis_b.ogg', variant, tag='C_vorbis')
        assert hv.boot()
        vinf = hv.open_current(max_slices=1500)
        out['vorbis_negative'] = {'open_info': vinf, 'open_failed': hv.open_failed}
    print('C vorbis negative:', out['vorbis_negative'])
    # step 3: seek to 60 s in the 90 s file
    with contextlib.redirect_stdout(open(LOGS / 'C_seek.stdout.log', 'w')):
        hs = fresh(MEDIA / 'opus_long.opus', variant, tag='C_seek')
        assert hs.boot()
        inf = hs.open_current()
        for _ in range(3):
            hs.poll_decode()
        hs.seek_replied = None
        hs.send_ch1(0x0B, 60000)
        hs.run_slices(4000, until=lambda: hs.seek_replied not in (None, 'pending-param'))
        seek_reply = hs.seek_replied
        base = len(hs.pcm)
        for _ in range(160):
            if not hs.poll_decode():
                break
            if len(hs.pcm) - base >= 48000 * 4 * 5:
                break
        seg = bytes(hs.pcm[base:])
        t_after = hs.info()['time_ms']
        # opus_long.opus is mono; the plug-in outputs dual-mono stereo
        # and reports 2 channels, so compare its left channel against
        # the mono reference starting at frame 60000 ms * 48 = 2,880,000
        import numpy as np
        left = np.frombuffer(seg, dtype=np.int16).reshape(-1, 2)[:, 0].tobytes()
        cref = cmp.compare(left, ref('opus_long')[2880000 * 2:], 1)
        out['seek'] = {'open': inf, 'seek_reply_param': seek_reply,
                       'time_ms_after': t_after, 'seg_bytes': len(seg),
                       'compare_vs_ref_at_60s': cref}
    print('C seek:', json.dumps(out['seek'], default=str)[:400])
    # step 5: gapless miniature: opus_b to EOS, then opus44 on the resident decoder
    with contextlib.redirect_stdout(open(LOGS / 'C_gapless.stdout.log', 'w')):
        hg = fresh(MEDIA / 'opus_b.opus', variant, tag='C_gapless')
        assert hg.boot()
        inf_a = hg.open_current()
        hg.decode_to_eos()
        eos_a = hg.eos_sent
        pcm_a = bytes(hg.pcm)
        hg.switch_media(MEDIA / 'opus44.opus')
        inf_b = hg.open_current()
        hg.decode_to_eos()
        pcm_b = bytes(hg.pcm[len(pcm_a):])
        ca = cmp.compare(pcm_a, ref('opus_b'), 2)
        cb = cmp.compare(pcm_b, ref('opus44'), 2)
        out['gapless'] = {'a_open': inf_a, 'a_eos': eos_a, 'a_compare': ca,
                          'b_open': inf_b, 'b_eos': hg.eos_sent, 'b_compare': cb}
    print('C gapless: A', out['gapless']['a_compare'], '\nC gapless: B', out['gapless']['b_compare'])
    # step 6: canaries on a dedicated run
    with contextlib.redirect_stdout(open(LOGS / 'C_canary.stdout.log', 'w')):
        hk = fresh(MEDIA / 'opus_b.opus', variant, tag='C_canary')
        hk.u.mem_write(harness72.STACK_FLOOR,
                       b'\x5a' * (harness72.STACK_TOP - harness72.STACK_FLOOR))
        assert hk.boot()
        page_after_boot = hk.rd(0x01020000, 0x90)
        flags_after_boot = hk.rd(*[harness72.EVENT_FLAGS[0],
                                   harness72.EVENT_FLAGS[1] - harness72.EVENT_FLAGS[0]])
        inf = hk.open_current()
        hk.decode_to_eos()
        flags_after_decode = hk.rd(harness72.EVENT_FLAGS[0],
                                   harness72.EVENT_FLAGS[1] - harness72.EVENT_FLAGS[0])
        hk.close_current()
        page_after = hk.rd(0x01020000, 0x90)
        stack = hk.rd(harness72.STACK_FLOOR,
                      harness72.STACK_TOP - harness72.STACK_FLOOR)
        # the stack grows down from STACK_TOP; the untouched watermark is
        # the run of 0x5A bytes at the low end of the window
        clean_low = 0
        for b in stack:
            if b == 0x5A:
                clean_low += 1
            else:
                break
        watermark_used = len(stack) - clean_low
        flag_words = struct.unpack('<16I', flags_after_decode)
        out['canaries'] = {
            'param_page_identical_after_session': page_after == page_after_boot,
            'stack_watermark_bytes_used': watermark_used,
            'stack_window': len(stack),
            'event_flags_after_boot_nonzero': [hex(x) for x in
                                               struct.unpack('<16I', flags_after_boot) if x],
            'event_flags_after_decode': [hex(x) for x in flag_words],
        }
    print('C canaries:', out['canaries'])
    RESULTS['C_variant_control_build'] = out


# ---------------------------------------------------------------- D: counts
def stage_d():
    out = {}
    variant = HERE / 'module72_opus_onstock.bin'
    # both excerpts are the same 10 s source; rates are per excerpt second
    h, inf, polls, closed, wall = decode_file(MEDIA / 'opus48.opus', variant,
                                              tag='D_opus', count=True)
    out['opus48_variant'] = {'insns': h.insn_count, 'blocks': h.block_count,
                             'pcm_seconds': 10.0,
                             'insn_per_audio_s': h.insn_count / 10.0,
                             'wall_s': round(wall, 1)}
    print('D opus:', out['opus48_variant'])
    h, inf, polls, closed, wall = decode_file(MEDIA / 'wma48.wma', None,
                                              tag='D_wma', count=True)
    out['wma48_stock'] = {'insns': h.insn_count, 'blocks': h.block_count,
                          'pcm_seconds': 10.0,
                          'insn_per_audio_s': h.insn_count / 10.0,
                          'wall_s': round(wall, 1)}
    print('D wma:', out['wma48_stock'])
    if out['opus48_variant']['insn_per_audio_s'] and out['wma48_stock']['insn_per_audio_s']:
        out['ratio_opus_per_wma'] = (out['opus48_variant']['insn_per_audio_s']
                                     / out['wma48_stock']['insn_per_audio_s'])
    RESULTS['D_efficiency'] = out


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    prev = HERE / 'validation_results.json'
    if prev.exists():
        RESULTS.update(json.loads(prev.read_text()))
    if which in ('all', 'A'):
        stage_a()
    if which in ('all', 'B'):
        stage_b()
    if which in ('all', 'C'):
        stage_c()
    if which in ('all', 'D'):
        stage_d()
    (HERE / 'validation_results.json').write_text(json.dumps(RESULTS, indent=1, default=str))
    print('wrote validation_results.json')
