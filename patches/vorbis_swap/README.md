# Full-precision Vorbis (`vorbis75` transplant)

Shipped in both images (Standard and Minimal). The low-precision Tremor build
inside the stock OGG module 75 is replaced with the full-precision build, with
the module size (116,572 bytes) unchanged, and its float-to-16-bit output is
rounded to nearest. The framework applies it as the `vorbis75` transplant
([`../framework/patches/transplants.txt`](../framework/patches/transplants.txt)).

On a pinned 40-file corpus, stock measures 38.1 to 42.1 dB signal-to-noise
against a reference decode; after the rounding fix, CE sits 0.01 to 0.21 dB
under each file's 16-bit ceiling of 85.1 to 97.4 dB. All measurements are
offline, in emulation.

- [`vorbis_swap.md`](vorbis_swap.md): how the decoder was isolated, the ABI checks and the measurements.
- [`vorbis_rounding.md`](vorbis_rounding.md): the rounding fix.
- [`corpus/vorbis_corpus.md`](corpus/vorbis_corpus.md): the 40-file measurement.
- [`DEPENDENCY.md`](DEPENDENCY.md): pinned inputs and provenance.
