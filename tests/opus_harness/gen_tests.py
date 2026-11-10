#!/usr/bin/env python3
"""Generate the Opus/WMA test files and ffmpeg reference decodes for the
module 72 harness validation. Run with the system python3; uses ffmpeg
on PATH (libopus encoder/decoder, wmav2 encoder/decoder)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEDIA = HERE / 'media'
MEDIA.mkdir(exist_ok=True)


def run(*args):
    print('+', ' '.join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], check=True)


# --- sources: music-ish synthetic (harmonics + vibrato + amplitude swell) ---
EXPR_L = ("0.30*sin(2*PI*196*t)*(0.7+0.3*sin(2*PI*0.5*t))"
          "+0.20*sin(2*PI*392*t+1.5*sin(2*PI*3*t))"
          "+0.12*sin(2*PI*587*t)+0.08*sin(2*PI*784*t)*(0.5+0.5*sin(2*PI*0.25*t))")
EXPR_R = ("0.28*sin(2*PI*262*t)*(0.7+0.3*sin(2*PI*0.4*t+1))"
          "+0.18*sin(2*PI*523*t+1.2*sin(2*PI*2.5*t))"
          "+0.10*sin(2*PI*659*t)+0.06*sin(2*PI*988*t)")


def make_src(name, rate, secs):
    out = MEDIA / name
    run('ffmpeg', '-y', '-v', 'error',
        '-f', 'lavfi', '-i', f'aevalsrc={EXPR_L}|{EXPR_R}:s={rate}:d={secs}',
        '-c:a', 'pcm_s16le', out)
    return out


def main():
    src10 = make_src('src10.wav', 48000, 10)
    src44 = make_src('src44.wav', 44100, 5)
    src5 = make_src('src5.wav', 48000, 5)
    src3 = make_src('src3.wav', 48000, 3)

    # Opus: 48 kHz stereo, 128 kbps, 20 ms frames, 10 s (decode + efficiency)
    run('ffmpeg', '-y', '-v', 'error', '-i', src10, '-c:a', 'libopus',
        '-b:a', '128k', '-frame_duration', '20', MEDIA / 'opus48.opus')
    # Opus: from a 44.1 kHz source, 128 kbps, 5 s
    run('ffmpeg', '-y', '-v', 'error', '-i', src44, '-c:a', 'libopus',
        '-b:a', '128k', MEDIA / 'opus44.opus')
    # Opus with an OpusTags packet over 50 KB (long comment), 5 s, 96 kbps
    big_comment = 'CE validation tag payload ' + 'x' * 56000
    run('ffmpeg', '-y', '-v', 'error', '-i', src5, '-c:a', 'libopus',
        '-b:a', '96k', '-metadata', f'comment={big_comment}',
        MEDIA / 'opus_tags.opus')
    # Opus worst case: 2.5 ms frames at 256 kbps, 4 s
    run('ffmpeg', '-y', '-v', 'error', '-i', src5, '-t', '4', '-c:a', 'libopus',
        '-b:a', '256k', '-frame_duration', '2.5', MEDIA / 'opus_worst.opus')
    # Opus long file for seeking: 90 s mono tone sweep, 64 kbps
    run('ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
        'aevalsrc=0.4*sin(2*PI*(200+300*t/90)*t):s=48000:d=90',
        '-ac', '1', '-c:a', 'libopus', '-b:a', '64k', MEDIA / 'opus_long.opus')
    # Opus second file for the gapless R1 miniature: 48 kHz stereo 96 kbps, 3 s
    run('ffmpeg', '-y', '-v', 'error', '-i', src3, '-c:a', 'libopus',
        '-b:a', '96k', MEDIA / 'opus_b.opus')

    # WMA control files (wmav2)
    run('ffmpeg', '-y', '-v', 'error', '-i', src3, '-c:a', 'wmav2',
        '-b:a', '96k', MEDIA / 'wma_small.wma')
    run('ffmpeg', '-y', '-v', 'error', '-i', src10, '-c:a', 'wmav2',
        '-b:a', '128k', MEDIA / 'wma48.wma')

    # Reference decodes (float decoders, s16le out)
    for name in ('opus48', 'opus44', 'opus_tags', 'opus_worst', 'opus_long',
                 'opus_b'):
        run('ffmpeg', '-y', '-v', 'error', '-c:a', 'libopus',
            '-i', MEDIA / f'{name}.opus',
            '-f', 's16le', MEDIA / f'{name}.ref.raw')
    for name in ('wma_small', 'wma48'):
        run('ffmpeg', '-y', '-v', 'error', '-i', MEDIA / f'{name}.wma',
            '-f', 's16le', MEDIA / f'{name}.ref.raw')

    # facts
    for f in sorted(MEDIA.iterdir()):
        print(f.name, f.stat().st_size)
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_packets',
                          '-select_streams', 'a:0', '-of', 'csv',
                          str(MEDIA / 'opus_tags.opus')],
                         capture_output=True, text=True).stdout
    sizes = [int(l.split(',')[4]) for l in out.strip().split('\n')[:3]]
    print('opus_tags first packet sizes:', sizes)


if __name__ == '__main__':
    sys.exit(main())
