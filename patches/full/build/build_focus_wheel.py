"""Poll wheel activity at every player service entry, independently of progress.

The original focus tick skips wheel changes while hidden and runs only after
the stock >40-tick progress interval. Both behaviors are inappropriate for
interactive wake. The service wrapper preserves all volatile input registers
and replays the exact stock prologue before continuing.
"""
import hashlib
import sys
from pathlib import Path
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from rknano_image import Image
from build_tail import branch
POLL=0x0305048C
WRAP=0x030511EC
SERVICE=0x0307DFDA
STATE=0x03023484

def assemble():
    ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
    poll=bytes(ks.asm('''
        push {r4,lr}
        ldr r4, =0x03023484
        ldr r0, =0x0302317C
        ldr r0, [r0]
        ldr r1, [r4,#4]
        cmp r0,r1
        beq done
        str r0,[r4,#4]
        bl 0x0306672E
        str r0,[r4]
        ldrb r0,[r4,#8]
        cbz r0,done
        movs r0,#0
        strb r0,[r4,#8]
        movs r0,#0x39
        bl 0x0306723C
        movs r0,#0x3b
        bl 0x0306723C
    done:
        pop {r4,pc}
        .ltorg
    ''',POLL)[0])
    stock=(ROOT/'DP3_V137.img').read_bytes();im=Image(stock)
    offset,_=im.module_region(27,'code');p=offset+SERVICE-im.modules[27]['code_exec']
    prologue=stock[p:p+4]
    assert prologue.hex()=='2de9f043',prologue.hex()
    wrapper=bytes(ks.asm(f'push.w {{r0-r3,r12,lr}}; bl {POLL:#x}; pop.w {{r0-r3,r12,lr}}',WRAP)[0])
    assert len(wrapper)==12
    wrapper+=prologue+branch(WRAP+16,SERVICE+4)
    assert len(poll)<=82 and len(wrapper)<=46
    return poll,wrapper

def main():
    poll,wrapper=assemble();raw=(ROOT/'DP3_V137.img').read_bytes();im=Image(raw)
    for number,label,module,address,data in (
            (260,'poll',0,POLL,poll),(261,'service-wrapper',0,WRAP,wrapper),
            (262,'service-hook',27,SERVICE,branch(SERVICE,WRAP))):
        off,_=im.module_region(module,'code');p=off+address-im.modules[module]['code_exec']
        name=f'{number:04d}-focus-wheel-{label}'
        (HERE.parent/'patches'/f'{name}.patch').write_text(
            f'# Player wheel responsiveness: {label}.\nname: {name}\nkind: module\nmodule: {module}\nregion: code\naddress: {address:#x}\nexpect: {raw[p:p+len(data)].hex()}\nreplace: {data.hex()}\ngate: stock bytes; service-entry wheel wake and ABI regression\nrationale: Detect wheel changes on every player service pass. Wake hidden controls immediately without waiting for the progress repaint cadence; preserve stock progress timing and original service prologue.\n')
    print(f'Wheel poll: {len(poll)} bytes; service wrapper: {len(wrapper)} bytes')
if __name__=='__main__':main()
