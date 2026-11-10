#!/usr/bin/env python3
"""Summarise each stub-family member: stub, literals, mailbox ids, timeouts, tail table."""
import re
for m in [41, 42, 50, 51, 52, 53, 54, 55, 56, 57]:
    lines = open(f'/home/hatch/workspace/fosi-dap-neo/work/modules2/dis_{m}.txt').read().splitlines() \
        if m != 54 else open('/home/hatch/workspace/fosi-dap-neo/work/modules2/dis_54.txt').read().splitlines()
    lits = sorted(set(re.findall(r'= (0x030[0-9a-f]{5})', '\n'.join(lines))))
    big = sorted(set(re.findall(r'= (0x0[0-9a-f]{7})', '\n'.join(lines))))
    print(f"== mod {m}")
    print("  0x030xxxxx literals:", ', '.join(lits))
    print("  big const literals :", ', '.join(big))
