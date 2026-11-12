#!/usr/bin/env python3
"""Track-transition fixture: measures the system-side gap of a track change.

Runs the real system-core code of a natural end-of-track advance (the
playback task's 0xEC handler, 0x03089AD6 with r0 = 0) and of a user NEXT
(dispatcher message 0x106) under Unicorn, with a virtual clock. The gap
is measured from the moment the playback task takes the end-of-track
event to the I2S DMA restart (0x0305FF74, channel 5, destination
0x40030024), the first instant new audio can reach the DAC.

Measured, not modelled: every instruction (at the system clock), every
busy-wait delay_ms/delay_us, the order of mailbox messages, CRU writes
(core-1 reset and clock gate), module loads and DAC I2C transactions.
Modelled, with the parameters printed in the report:
  - core 1: answers each mailbox wait after Decoder.reply ms, but only
    while its reset is released and its clock ungated; a halted core
    answers nothing, so the wait runs to its cap (timeout);
  - storage: module loads read at Machine.flash_bps;
  - I2C: each DAC register write takes Decoder.i2c ms on the wire;
  - the file service: open/close/step return at once.
Not covered: decoder-side work (opening the next file over the HifiFile
RPC, decoding its first frame), which runs on core 1 in parallel with the
waits counted here, and the playback task's poll latency for 0xEC.

Cases:
  stock  natural advance, user skip, codec change
  CE     the same three; plus two mutations of the CE image:
         - 0024 reverted (stock shutdown halts core 1): the gate must
           see the halt and fall back to a full reload, with no timeout;
         - 0024 reverted and the gate's core-1 check removed (the v1
           logic): the rig must report the open-exchange timeout.

Usage: test_transition.py [CE_IMAGE]   (default release/DP3_V137_CE.img)
Exit 0 when every assertion holds.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scenario import Scenario, ROOT, I2S_TX  # noqa: E402

STOCK_SHA = 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
DECODERS = range(71, 81)
SHUTDOWN = 0x030893C4
STOCK_SHUTDOWN = bytes.fromhex(
    'cf4810b500680a2828bf10bddfe800f0051b1b1b1b1b1b1b1b1bfff7c6ffe3f793fb'
    '01210e20c9f717f901210f20c9f713f900216e20c9f7d7f80021bde810407e20c9f7'
    'd1b8fff7b0ffbde81040e3f77bbb')
GATE_CORE1_CHECK = 0x0305166E          # cbz r2, miss (0022)

fails = []


def check(name, ok, detail=''):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f': {detail}' if detail else ''))
    if not ok:
        fails.append(name)


def patch_exec(raw, module, addr, data):
    s = Scenario(raw)
    im = s.m.im
    off, size = im.module_region(module, 'code')
    base = im.modules[module]['code_exec']
    assert base <= addr and addr + len(data) <= base + size
    out = bytearray(raw)
    out[off + addr - base:off + addr - base + len(data)] = data
    return bytes(out)


def run(raw, how, ext=b'FLA', first=b'FLA'):
    s = Scenario(raw, ext=first)
    s.start_first()
    s.ext = ext
    getattr(s, how)()
    m = s.m
    return {
        'first_audio': s.first_audio_ms(),
        'halted': any(k == 'reset' and on for k, on, _ in m.core1_log),
        'decoder_loads': [i for i, *_ in m.loads if i in DECODERS],
        'loads': m.loads,
        'timeouts': [w for w in m.waits if w[3] == 'timeout'],
        'round_trips': len(m.waits),
        'i2c': s.i2c,
        'delay_ms': sum(n for _, k, n, _ in m.delays if k == 'ms'
                        and _ < (s.first_audio_ms() or 1e9)),
        'copy_before_i2s': _copy_first(s),
        'prints': [p for p, _ in m.prints],
    }


def _copy_first(s):
    t_i2s = s.first_audio_ms()
    return t_i2s is not None and any(
        dst != I2S_TX and t <= t_i2s for _, _, dst, _, t in s.dma)


def row(label, r):
    fa = r['first_audio']
    print(f"  {label:<34} first audio {fa if fa is None else f'{fa:8.3f} ms'}"
          f"  halt={'y' if r['halted'] else 'n'}"
          f"  decoder reload={r['decoder_loads'] or '-'}"
          f"  core-1 waits={r['round_trips']}"
          f"  i2c={r['i2c']}  delay_ms before audio={r['delay_ms']}"
          + (f"  TIMEOUTS={len(r['timeouts'])}" if r['timeouts'] else ''))


def main():
    stock = (ROOT / 'DP3_V137.img').read_bytes()
    assert hashlib.sha256(stock).hexdigest() == STOCK_SHA, 'stock SHA gate'
    ce_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'release' / 'DP3_V137_CE.img'
    ce = ce_path.read_bytes()
    d = Scenario(stock).dec
    print(f'model: core-1 reply {d.reply} ms, storage {Scenario(stock).m.flash_bps / 1e6:g} MB/s, '
          f'I2C write {d.i2c_ms} ms, system clock 120 MHz')

    print('stock (DP3_V137.img)')
    s_nat = run(stock, 'run'); row('natural advance FLAC->FLAC', s_nat)
    s_skip = run(stock, 'skip'); row('user NEXT FLAC->FLAC', s_skip)
    s_chg = run(stock, 'run', b'APE'); row('natural advance FLAC->APE', s_chg)
    print(f'CE ({ce_path.name})')
    c_nat = run(ce, 'run'); row('natural advance FLAC->FLAC', c_nat)
    c_skip = run(ce, 'skip'); row('user NEXT FLAC->FLAC', c_skip)
    c_chg = run(ce, 'run', b'APE'); row('natural advance FLAC->APE', c_chg)
    c_ape = run(ce, 'run', b'APE', b'APE'); row('natural advance APE->APE', c_ape)
    halting = patch_exec(ce, 33, SHUTDOWN, STOCK_SHUTDOWN)
    m1 = run(halting, 'run'); row('mutant: 0024 reverted', m1)
    v1 = patch_exec(halting, 0, GATE_CORE1_CHECK, b'\x00\xbf')
    m2 = run(v1, 'run'); row('mutant: v1 logic', m2)

    print('checks')
    for name, r in (('stock natural', s_nat), ('stock skip', s_skip),
                    ('stock codec change', s_chg)):
        check(f'{name}: halts and reboots core 1, no timeout',
              r['halted'] and r['decoder_loads'] and not r['timeouts'])
        check(f'{name}: I2S restarts', r['first_audio'] is not None)
    check('CE natural: core 1 never halted', not c_nat['halted'])
    check('CE natural: no decoder reload', not c_nat['decoder_loads'])
    check('CE natural: no core-1 timeout', not c_nat['timeouts'])
    check('CE natural: a fresh frame is copied before I2S restarts',
          c_nat['copy_before_i2s'])
    check('CE natural: codec open reported success',
          'audio codec open success.' in c_nat['prints'])
    check('CE natural: gap shorter than stock',
          c_nat['first_audio'] < s_nat['first_audio'],
          f"{c_nat['first_audio']:.3f} vs {s_nat['first_audio']:.3f} ms")
    check('CE skip: halts and fully reloads, no timeout',
          c_skip['halted'] and c_skip['decoder_loads'] and not c_skip['timeouts'])
    check('CE APE->APE: fast path is FLAC-only, so it halts and fully reloads',
          c_ape['halted'] and c_ape['decoder_loads'] and not c_ape['timeouts'])
    check('CE codec change: loads the new decoder, no timeout',
          c_chg['decoder_loads'] and not c_chg['timeouts'])
    check('mutant 0024 reverted: gate falls back to a full reload',
          m1['halted'] and m1['decoder_loads'] and not m1['timeouts'])
    check('mutant v1 logic: rig reports the open-exchange timeout',
          bool(m2['timeouts']))
    print('FAILED: ' + ', '.join(fails) if fails else 'all checks passed')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
