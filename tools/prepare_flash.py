#!/usr/bin/env python3
"""Offline package review and matched-date recovery preparation; no device I/O."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from rknano_image import Image,rk_crc32
from firmware_patch import bcd_date
ROOT=Path(__file__).resolve().parents[1]
BOOT_PATCH_DIR = ROOT / 'patches' / 'boot_recovery'
OFFICIAL={
 'fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef':'V137',
 '4713a2eb4b523d49ad003ac2df159c1c596339aef1a9a060e6ea6bbbf18e1332':'V155',
}

POWER_RESTART_POLL = 0x03067CF4
POWER_RESTART_STOCK = bytes.fromhex(
    '0a20 fcf725fe f9f799fc 0028 f8d1 0024 f9f794fc 0028 fad0 641c 0a2c f8d9'
)
POWER_RESTART_DEBOUNCED = bytes.fromhex(
    '0024 '      # movs r4, #0          Keep waiting for the first release.
    '0a20 '      # poll: movs r0, #10
    'fcf724fe '  # bl 0x03064944        Stock 10 ms delay.
    'f9f798fc '  # bl 0x03061630        Read the active-high Power button.
    '20b1 '      # cbz r0, released
    '002c '      # cmp r4, #0
    'f7d0 '      # beq poll
    '013c '      # subs r4, #1
    'f5d1 '      # bne poll
    '02e0 '      # b 0x03067D12          Stock reset with arguments (0, 0).
    '0b24 '      # released: movs r4, #11
    'f2e7 '      # b poll
    '00bf'       # nop
)

def digest(raw):return hashlib.sha256(raw).hexdigest()
def image_date(raw):
    year,day=struct.unpack_from('<HH',raw)
    s=f'{year:04x}{day:04x}'
    if not s.isdigit():raise ValueError('header date has non-BCD digits')
    return dt.datetime.strptime(s,'%Y%m%d').date()
def audit(raw):
    im=Image(raw);mirror=im.u32(0x1f4)
    if len(im.modules)!=82:raise ValueError('module count must be 82')
    if mirror%512 or mirror+512>len(raw)-4:raise ValueError('invalid aligned header mirror')
    if raw[:512]!=raw[mirror:mirror+512]:raise ValueError('header mirror mismatch')
    if im.u32(len(raw)-4)!=rk_crc32(raw[:-4]):raise ValueError('trailer CRC mismatch')
    transfer=(mirror+0x104000)&~0xfffff
    if transfer!=0xd00000:raise ValueError('rounded updater transfer differs from stock 13 MiB')
    ranges=[]
    for m in im.modules:
        for kind in ('code','data'):
            off,n=im.module_region(m['index'],kind)
            if n and (off<0x400 or off+n>mirror):raise ValueError(f'module {m["index"]} {kind} outside payload')
            if n:ranges.append((off,off+n,m['index'],kind))
    # Overlay execution spans deliberately overlap; stored payload ranges must not.
    for a,b in zip(sorted(ranges),sorted(ranges)[1:]):
        if a[1]>b[0]:raise ValueError(f'stored module segments overlap: {a[2:]} / {b[2:]}')
    for name,s in im.sections.items():
        if s['offset']<0x400 or s['offset']+s['length']>mirror:raise ValueError(f'{name} outside payload')
    if mirror+512>transfer:raise ValueError('mirror lies outside updater transfer')
    if any(raw[transfer:-4]):raise ValueError('nonzero payload would be omitted by the updater transfer')
    return {'sha256':digest(raw),'bytes':len(raw),'header_date':image_date(raw).isoformat(),
            'mirror_offset':hex(mirror),'updater_transfer_bytes':transfer,
            'nonzero_payload_after_transfer':False,'stored_segments':len(ranges),
            'package_checks':'passed','hardware_boot_verified':False,
            'physical_slot_geometry_verified':False,'recovery_on_device_verified':False}
def redated(raw,date):
    audit(raw)
    date_string=date.strftime('%Y%m%d')
    out=bytearray(raw);mirror=struct.unpack_from('<I',raw,0x1f4)[0]
    out[:4]=bcd_date(date_string);out[mirror:mirror+512]=out[:512]
    struct.pack_into('<I',out,len(out)-4,rk_crc32(out[:-4]))
    result=bytes(out);audit(result)
    # Only the two date fields and outer CRC may differ.
    spans=((0,4),(mirror,mirror+4),(len(out)-4,len(out)))
    if any(a!=b and not any(lo<=i<hi for lo,hi in spans) for i,(a,b) in enumerate(zip(raw,result))):
        raise ValueError('redating changed bytes outside the date fields and CRC')
    return result

def release_pins():
    pins={}
    for line in (ROOT/'release/SHA256SUMS').read_text().splitlines():
        h,name=line.split();pins[h]=name.lstrip('*')
    return pins

def debounce_power_restart(raw):
    image = Image(raw)
    code_offset, code_size = image.module_region(0, 'code')
    relative = POWER_RESTART_POLL - image.modules[0]['code_exec']
    offset = code_offset + relative
    end = offset + len(POWER_RESTART_STOCK)
    if (not 0 <= relative <= code_size - len(POWER_RESTART_STOCK)
            or raw[offset:end] != POWER_RESTART_STOCK):
        raise ValueError('unexpected shutdown power-button polling code')
    output = bytearray(raw)
    output[offset:end] = POWER_RESTART_DEBOUNCED
    struct.pack_into('<I', output, len(output) - 4, rk_crc32(output[:-4]))
    return bytes(output)


def apply_boot_patches(raw, names):
    manifests = {p.parent.name: p for p in BOOT_PATCH_DIR.glob('*/manifest.txt')}
    if unknown := set(names) - manifests.keys():
        raise ValueError('unknown boot patch: ' + ', '.join(sorted(unknown)))
    spec = importlib.util.spec_from_file_location(
        'firmware_build', ROOT / 'patches' / 'framework' / 'build.py')
    framework = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(framework)

    patches = [patch for name in dict.fromkeys(names)
               for patch in framework.load_manifest(manifests[name])]
    patched, edits = framework.apply_patches(raw, patches)
    output = bytearray(patched)
    struct.pack_into('<I', output, len(output) - 4, rk_crc32(output[:-4]))
    return bytes(output), edits


def prepare(candidate,official,date=None,*,debounce_power_on=False,boot_patches=()):
    if digest(candidate) not in release_pins():raise ValueError('candidate is not one of the pinned CE release images')
    if digest(official) not in OFFICIAL:raise ValueError('official recovery source is not a verified DP3 V137/V155 image')
    c=audit(candidate);o=audit(official)
    latest=max(image_date(candidate),image_date(official))
    build=date or latest+dt.timedelta(days=1)
    if build<=latest:raise ValueError('candidate date must be newer than both input images')
    recovery_date=build+dt.timedelta(days=1)
    ce=redated(candidate,build);recovery=redated(official,recovery_date)
    if debounce_power_on:
        ce = debounce_power_restart(ce)
    if boot_patches:
        ce, boot_patch_edits = apply_boot_patches(ce, boot_patches)
    report={'status':'OFFLINE CHECKS PASSED; DEVICE QUALIFICATION REQUIRED',
            'source_candidate':c,'source_official':{**o,'version':OFFICIAL[digest(official)]},
            'prepared_candidate':audit(ce),'prepared_recovery':audit(recovery),
            'source_candidate_not_newer_than_official':image_date(candidate)<=image_date(official),
            'modified_code_or_resources':debounce_power_on or bool(boot_patches),
            'official_source_matches_device_verified':False,
            'full_device_backup_verified':False,
            'release_gate':'Do not flash until a full device backup, readback-verified slot map, recovery entry and restore procedure are established on this unit.',
            'recovery_note':'Recovery is the supplied official firmware with a newer header date; no CE code is present. Date ordering is a traced validator rule, not proof of early-boot acceptance.'}
    if debounce_power_on:
        report['candidate_patch'] = {
            'module': 0,
            'address': hex(POWER_RESTART_POLL),
            'bytes': len(POWER_RESTART_DEBOUNCED),
            'behavior': 'After release, require eleven consecutive Power samples 10 ms apart.',
        }
    if boot_patches:
        report['boot_patches'] = boot_patch_edits
    return ce,recovery,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,default=ROOT/'release/DP3_V137_CE.img')
    p.add_argument('--official',type=Path,required=True,help='verified official image matching the firmware/model currently on the device')
    p.add_argument('--date',help='YYYYMMDD, strictly newer than both inputs; otherwise next day after the newer input')
    p.add_argument('--debounce-power-on', action='store_true',
                   help='apply the post-shutdown Power button fix to the CE candidate')
    p.add_argument('--boot-patch', action='append', default=[],
                   choices=sorted(p.parent.name for p in BOOT_PATCH_DIR.glob('*/manifest.txt')),
                   help='apply an opt-in boot repair to the CE candidate (repeatable)')
    p.add_argument('--output',type=Path,required=True,help='new directory; existing paths are refused')
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():p.error('output already exists')
    date=dt.datetime.strptime(a.date,'%Y%m%d').date() if a.date else None
    ce,recovery,report=prepare(a.candidate.read_bytes(),a.official.read_bytes(),date,
                               debounce_power_on=a.debounce_power_on,boot_patches=a.boot_patch)
    a.output.mkdir(parents=True,exist_ok=False)
    for name,raw in (('DP3_CE_candidate.img',ce),('DP3_official_recovery.img',recovery)):
        with (a.output/name).open('xb') as f:f.write(raw)
    with (a.output/'REVIEW.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    with (a.output/'SHA256SUMS').open('x') as f:
        f.write(f'{digest(ce)}  DP3_CE_candidate.img\n{digest(recovery)}  DP3_official_recovery.img\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
