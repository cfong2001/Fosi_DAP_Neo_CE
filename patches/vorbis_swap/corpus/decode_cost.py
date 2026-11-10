#!/usr/bin/env python3
"""Dynamic instruction count for stock vs transplanted module 75 on one
corpus file, via Unicorn block hooks + Capstone disassembly of each
unique executed block (cached). Block hooks are the counting mechanism
emu75.py sanctions (code hooks mis-execute Thumb IT blocks on
Unicorn 2.1). The count covers the identical session path for both
modules: rt_prepare, OPEN, rt_after_open, the full play loop, CLOSE.

Run:  venv/bin/python work/vorbis_corpus/decode_cost.py music_q5_48000.ogg
"""
import importlib.util
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SWAP = HERE.parent / "patches" / "vorbis_swap"
sys.path.insert(0, str(SWAP))
spec = importlib.util.spec_from_file_location("emu75", SWAP / "emu75.py")
emu75 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emu75)

import capstone
from unicorn import UC_HOOK_BLOCK

MD = capstone.Cs(capstone.CS_ARCH_ARM,
                 capstone.CS_MODE_THUMB | capstone.CS_MODE_MCLASS)


def run(segs, ogg):
    e = emu75.Emu(segs, str(ogg))
    cache = {}
    count = [0]
    blocks = [0]

    def hook(u, addr, size, data):
        key = (addr, size)
        c = cache.get(key)
        if c is None:
            code = bytes(u.mem_read(addr, size))
            c = sum(1 for _ in MD.disasm(code, addr))
            cache[key] = c
        count[0] += c
        blocks[0] += 1

    e.u.hook_add(UC_HOOK_BLOCK, hook)
    t0 = time.time()
    e.rt_prepare()
    if e.call(emu75.SUB["OPEN"]) != 1:
        sys.exit("OPEN failed")
    e.rate = e.get("GETSAMPLERATE")
    e.rt_after_open()
    with open("/tmp/cost_pcm.s16", "wb") as out:
        frames, _ = emu75.play(e, out, 0)
    e.call(emu75.SUB["CLOSE"], a1=1)
    wall = time.time() - t0
    return count[0], blocks[0], len(cache), frames, e.rate, wall


def main():
    ogg = HERE / "corpus" / (sys.argv[1] if len(sys.argv) > 1 else "music_q5_48000.ogg")
    res = {}
    for mod, segs in (("stock", f"{SWAP}/module75_stock_code.bin,{SWAP}/module75_stock_data.bin"),
                      ("patched", f"{SWAP}/module75_patched_code.bin,{SWAP}/module75_patched_data.bin")):
        ins, blocks, uniq, frames, rate, wall = run(segs, ogg)
        secs = frames / rate
        res[mod] = (ins, frames, rate)
        print(f"{mod}: instructions {ins:,}  blocks {blocks:,} (unique {uniq:,})  "
              f"frames {frames} @ {rate} Hz = {secs:.3f} s  "
              f"-> {ins / secs:,.0f} insn/s of audio  (wall {wall:.1f} s)")
    s, p = res["stock"][0], res["patched"][0]
    print(f"ratio patched/stock = {p / s:.4f}  ({(p / s - 1) * 100:+.2f} %)")


if __name__ == "__main__":
    main()
