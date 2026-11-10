#!/usr/bin/env python3
"""Phase D milestone-2 driver: Job 1 (FLAC PCM capture) and Job 2 (gapless
R1 transition traces). Produces the deliverable trace logs in this folder.

Run with the workspace venv:  ~/workspace/fosi-dap-neo/venv/bin/python run_m2.py
Offline only; reads test44.flac / test48.flac, writes logs + pcm*.bin here.
"""
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness2 import H3, CODEC_STATE  # noqa: E402

HERE = Path(__file__).resolve().parent


def ffprobe_frames(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                          '-show_frames', '-of', 'csv', str(path)],
                         capture_output=True, text=True).stdout
    data = Path(path).read_bytes()
    frames = []
    for line in out.strip().split('\n'):
        f = line.split(',')
        frames.append({'samples': int(f[10]), 'assign': data[int(f[12]) + 3] >> 4})
    return frames


def assemble_stereo(frames, meta):
    """frames: H3.lpc_frames entries (cnt, ch0, ch1raw); meta: ffprobe list.
    Applies the FLAC channel-assignment conversion fn 0x2E9A performs."""
    out = bytearray()
    for fi, (cnt, c0s, c1s) in enumerate(frames):
        a = meta[fi]['assign'] if fi < len(meta) else 8
        for k in range(cnt):
            x, y = c0s[k], c1s[k]
            if a <= 7:
                l, r = x, y
            elif a == 8:      # left + side
                l, r = x, x - y
            elif a == 9:      # side + right
                l, r = x + y, y
            else:             # mid + side
                mid = (x << 1) | (y & 1)
                l, r = (mid + y) // 2, (mid - y) // 2
            out += struct.pack('<hh', l, r)
    return bytes(out)


def open_current(h):
    h.open_notified = False
    h.info_reported = None
    h.eos_sent = False
    h.send_info65()
    assert h.run_slices(400, until=lambda: h.open_notified), 'no 0x66 open-accepted'
    h.send_ch1(1)
    assert h.run_slices(600, until=lambda: h.info_reported not in (None, 'pending-param')), \
        'no stream-info report'
    h.lpc_frames.clear()       # drop the seek-info probe frame assembly
    return h.snapshot('open')


def decode_to_eos(h, max_polls=30):
    """Poll the position command until decoded_samples stops advancing.
    Returns (accepted_frames, decoded_samples). Assemblies that arrive
    after the decoded counter stops (stale post-EOS 0x2E9A) are rejected."""
    accepted = []
    cum = 0
    stall = 0
    for _ in range(max_polls):
        before = len(h.lpc_frames)
        h.send_ch1(4)
        h.run_slices(4000)
        decoded = h.rd64(CODEC_STATE + 0x28)
        new = h.lpc_frames[before:]
        got = False
        for fr in new:
            if cum < decoded:
                accepted.append(fr)
                cum += fr[0]
                got = True
        if h.eos_sent:
            break
        if not got:
            stall += 1
            if stall >= 2:
                break
        else:
            stall = 0
    return accepted, h.rd64(CODEC_STATE + 0x28)


def compare(pcm, ref_path):
    ref = Path(ref_path).read_bytes()
    n = min(len(pcm), len(ref))
    exact = pcm[:n] == ref[:n]
    w_d = struct.unpack(f'<{n // 2}h', pcm[:n])
    w_r = struct.unpack(f'<{n // 2}h', ref[:n])
    ok_l = sum(1 for i in range(0, len(w_d), 2) if w_d[i] == w_r[i])
    ok_r = sum(1 for i in range(1, len(w_d), 2) if w_d[i] == w_r[i])
    return {'bytes': len(pcm), 'ref_bytes': len(ref), 'prefix_bitexact': exact,
            'L_exact': ok_l, 'R_exact': ok_r, 'pairs': len(w_d) // 2}


def diff_snaps(a, b, out):
    """Write the curated-field + data-window diff of two snapshots."""
    fields = ['fmt_word', 'file_size', 'handle_tab3', 'freq_flag', 'dma_flags',
              'total_samples', 'decoded_samples', 'event_bitmap', 'flac_30',
              'flac_34', 'flac_40', 'out_idx', 'out_cell']
    out.append(f"--- snapshot diff: {a['label']} (A) vs {b['label']} (B) ---")
    for f in fields:
        va, vb = a[f], b[f]
        if isinstance(va, bytes):
            va, vb = va.hex(), vb.hex()
        mark = '  ' if va == vb else '**'
        out.append(f'{mark} {f}: A={va} B={vb}')
    for f in ('ctrl_block', 'fs_struct', 'fill_table', 'stream_state'):
        out.append(f'{"  " if a[f] == b[f] else "**"} {f}: '
                   f'{"equal" if a[f] == b[f] else "A=" + a[f].hex() + " B=" + b[f].hex()}')
    pa, pb = a['param_page'], b['param_page']
    out.append(f'{"  " if pa == pb else "**"} param_page (144 B): '
               f'{"identical" if pa == pb else "DIFFERS"}')
    if pa != pb:
        for i in range(0, 144, 4):
            wa = struct.unpack('<I', pa[i:i + 4])[0]
            wb = struct.unpack('<I', pb[i:i + 4])[0]
            if wa != wb:
                out.append(f'    page+{i:#04x}: A={wa:#010x} B={wb:#010x}')
    wa, wb = a['data_window'], b['data_window']
    regions = []
    for base in range(0, len(wa), 0x1000):
        seg_a, seg_b = wa[base:base + 0x1000], wb[base:base + 0x1000]
        if seg_a != seg_b:
            regions.append((0x01020000 + base,
                            sum(1 for x, y in zip(seg_a, seg_b) if x != y)))
    out.append(f'data window differing 4 KiB regions: {len(regions)} of 64 '
               f'({sum(c for _, c in regions)} bytes differ)')
    for addr, cnt in regions:
        out.append(f'    {addr:#010x}: {cnt} bytes differ')
    return out


def job1():
    print('== JOB 1: FLAC PCM capture ==')
    for name, refn in (('test44.flac', 'ref44_s16.raw'), ('test48.flac', 'ref48_s16.raw')):
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', name, '-f', 's16le', refn],
                       cwd=HERE, check=True)
        log = f'run_log_m2_pcm{"" if name == "test44.flac" else "48"}.txt'
        h = H3(76, name, trace_path=str(HERE / log))
        assert h.boot()
        open_current(h)
        frames, decoded = decode_to_eos(h)
        meta = ffprobe_frames(HERE / name)
        pcm = assemble_stereo(frames, meta)
        Path(HERE / f'pcm{name[4:6]}_final.bin').write_bytes(pcm)
        res = compare(pcm, HERE / refn)
        total = h.rd64(CODEC_STATE + 0x18)
        with open(HERE / log, 'a') as f:
            f.write(f'\n[RESULT] {name}: frames decoded={len(frames)} '
                    f'decoded_samples={decoded} decoder_total={total}\n')
            f.write(f'[RESULT] PCM {res["bytes"]} bytes vs ffmpeg {res["ref_bytes"]}: '
                    f'prefix bit-exact={res["prefix_bitexact"]} '
                    f'L {res["L_exact"]}/{res["pairs"]} R {res["R_exact"]}/{res["pairs"]}\n')
        print(name, res, 'decoded', decoded, 'of decoder total', total)


def job2():
    print('== JOB 2: gapless R1 transition traces ==')
    meta_a = ffprobe_frames(HERE / 'test44.flac')
    meta_b = ffprobe_frames(HERE / 'test48.flac')

    # (b)+(d) load-skipped: A to EOS, then B on the resident decoder
    h = H3(76, 'test44.flac', trace_path=str(HERE / 'run_log_m2_transition.txt'))
    assert h.boot()
    snap_boot = h.snapshot('L:boot')
    open_current(h)
    frames_a, dec_a = decode_to_eos(h)
    snap_a_eos = h.snapshot('L:A-eos')
    pcm_a = assemble_stereo(frames_a, meta_a)
    h.switch_media(str(HERE / 'test48.flac'))
    snap_b_skip = open_current(h)
    frames_b, dec_b = decode_to_eos(h)
    pcm_b = assemble_stereo(frames_b, meta_b)
    res_b = compare(pcm_b, HERE / 'ref48_s16.raw')
    with open(HERE / 'run_log_m2_transition.txt', 'a') as f:
        f.write(f'\n[RESULT] load-skipped: A decoded={dec_a}; B on resident decoder: '
                f'frames={len(frames_b)} decoded={dec_b} PCM={res_b}\n')
    print('load-skipped B:', res_b, 'decoded', dec_b)

    # stock-reload reference for B: fresh instance
    hs = H3(76, 'test48.flac', trace_path=str(HERE / 'run_log_m2_stockB.txt'))
    assert hs.boot()
    snap_b_stock = open_current(hs)
    frames_bs, dec_bs = decode_to_eos(hs)
    print('stock B decoded', dec_bs, 'frames', len(frames_bs))

    # (d) diffs
    lines = ['PARAMETER-PAGE / STATE DIFF (gapless R3)',
             'A = load-skipped instance, B = fresh stock-reload instance; both at post-open of file B (test48.flac).',
             '']
    diff_snaps(snap_b_skip, snap_b_stock, lines)
    lines += ['', 'Within the load-skipped instance (page stability across the session):']
    diff_snaps(snap_a_eos, snap_b_skip, lines)
    Path(HERE / 'run_log_m2_diff.txt').write_text('\n'.join(lines) + '\n')
    print('diff written')

    # (c) stop -> replay same file on the resident decoder
    hr = H3(76, 'test44.flac', trace_path=str(HERE / 'run_log_m2_stop_replay.txt'))
    assert hr.boot()
    open_current(hr)
    for _ in range(3):
        hr.send_ch1(4)
        hr.run_slices(4000)
    dec_mid = hr.rd64(CODEC_STATE + 0x28)
    hr.send_ch1(0x0D, 0)                     # stop-class: ch1 cmd 0x0D -> cmd word 6 -> sel 15 CLOSE
    hr.run_slices(2000)
    snap_stop = hr.snapshot('R:after-stop')
    snap_re = open_current(hr)
    frames_r, dec_r = decode_to_eos(hr)
    pcm_r = assemble_stereo(frames_r, meta_a)
    res_r = compare(pcm_r, HERE / 'ref44_s16.raw')
    res_a = compare(pcm_a, HERE / 'ref44_s16.raw')
    with open(HERE / 'run_log_m2_stop_replay.txt', 'a') as f:
        f.write(f'\n[RESULT] stop at decoded={dec_mid}; replay on resident decoder: '
                f'frames={len(frames_r)} decoded={dec_r} PCM={res_r}; '
                f'fresh-boot baseline PCM={res_a}; replay == baseline: {pcm_r == pcm_a}\n')
    print('stop-replay:', res_r, 'decoded', dec_r, '== baseline:', pcm_r == pcm_a)


if __name__ == '__main__':
    job1()
    job2()
