# Output-preserving performance work (draft)

Baseline: the accepted Standard CE image, SHA-256
`08054971d2a5ef837c5186a8b31e20f720bedbc1ddb41978885b0f4e32d105c9`.
This work covers the firmware beyond drawing. The release image, manifest,
clocks and decoder binaries remain unchanged in this initial draft. Experiments
run in memory and are not flash candidates.

## Measured opportunities

| Path | Baseline | Experiment / next step | Equality gate |
| --- | --- | --- | --- |
| Opus metadata Unicode conversion | ASCII fixture: 19,471 instructions | ASCII fast path: 16,489 (-15.3%); long title: 13,461 to 10,815 (-19.7%) | All 1,366 record bytes identical in eleven cases; same native file/sector read counts; stack, record guards and watchdog checks pass |
| Metadata key scanning / storage | Unknown key length 5: 23 file reads; length 24: 41 reads | Byte-at-a-time key reads are a measured I/O target. Prototype bounded segment-aware batching, then compare read counts and malformed returns | Exact records, packet/segment boundaries, first-value policy, bounded stack and watchdog interval |
| Natural sorting | Unequal prefix: 16 instructions, zero DB reads. Numeric cold: 1,175 instructions / two reads; warm: 1,157 / zero reads | Existing two-entry cache removes reads but barely reduces transform work. Profile repeated normalization before choosing cache or comparator changes | Entire sorted records and comparator results; accents, articles, numbers, buffer initialization and cache invalidation |
| Input service | Hidden wake: 44 instructions; 20 continuous visible steps cause zero art requests | Preserve the inexpensive wake path; measure idle passes and timer callbacks before changing polling | Identical consumed wheel counts, event sequence, volatile registers and debounce behavior |
| Playback routing / transitions | Native Opus route and same-codec reuse already have executable harnesses | Profile module loads, file RPC, mailbox waits and repeated content probes; separate modeled waits from CPU instructions | Same codec/module selection, next-track order, errors and audible PCM |
| Audio decoders / DSP | Transplanted fixed-point decoders and clock tables have separate gates | Count instructions per decoded sample and profile hot arithmetic before selecting an optimization; retain existing clocks | Byte-identical PCM over non-silent vectors, all supported rates/channels, saturation and error behavior |
| Full-player fill | 28,854 instructions | Double stores per loop: 19,254 (-33.3%), 92 code bytes | All 153,600 framebuffer bytes and 40 context bytes match in eight cases; ABI, bounds and rotated fallback checked |

The metadata ASCII prototype grows its function from 64 to 82 bytes. It runs
at an emulator-only scratch address, not a qualified code home. Placement and
source-to-patch integration are required before proposing it for the release.
The Unicode-only fixture costs 360 extra instructions (+1.7%); two malformed
UTF-8 cases cost 12 and three extra instructions respectively;
this is recorded rather than hidden by an average. No storage-read saving is
claimed for the ASCII conversion change.

## Reproduce

Install the repo's pinned Unicorn, Keystone and Capstone dependencies. The
metadata experiment additionally requires reference LLVM 22.1.3 on PATH.

```sh
python patches/performance/profile_nonrender.py
python patches/performance/test_metadata_ascii.py
python patches/performance/test_fill_unroll.py
```

`profile_nonrender.py` uses generated metadata and real native file, sort and
wheel paths, with storage leaves modeled by the existing harnesses. Results
are work counts, not physical latency. No personal music or device data is used.

Before release: select changes with measured benefit, qualify their code homes,
rebuild and pin artifacts, run the repair/format/transition gates and confirm
hardware behavior. Preserve error behavior and watchdog servicing. A faster
average must not hide a correctness change or unbounded worst case.
