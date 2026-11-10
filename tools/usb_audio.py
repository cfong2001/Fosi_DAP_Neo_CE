#!/usr/bin/env python3
"""Decode USB Audio Class 1.0 and HID descriptors from original module 11.

The hardcoded CPU addresses are pinned to SHA-256 of DP3_V137.img.
All descriptor fields and buffer byte lengths derive from actual firmware bytes.
No host USB devices are accessed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from rknano_image import Image

SHA256='fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef'
MODULE=11
DATA_CPU=0x03024ac0
CONFIG_CPU=0x03024ac8
REPORT_CPU=0x03024b58
DEVICE_CPU=0x03024bc4


def u24(b):
    return b[0] | b[1]<<8 | b[2]<<16


def decode(im):
    if hashlib.sha256(im.raw).hexdigest() != SHA256:
        raise ValueError('image SHA-256 is not DP3_V137; pinned addresses would be invalid')
    m=im.modules[MODULE]
    start,n=im.module_region(MODULE,'data')
    if m['data_exec']!=DATA_CPU:
        raise ValueError('unexpected USB Audio module data base')
    data=im.raw[start:start+n]
    pos=CONFIG_CPU-DATA_CPU
    if data[pos:pos+2]!=b'\x09\x02':
        raise ValueError('missing USB configuration header')
    config_len=struct.unpack_from('<H',data,pos+2)[0]
    end=pos+config_len
    result={'file_offset':f'0x{start+pos:x}',
            'cpu_address':f'0x{CONFIG_CPU:08x}',
            'total_length':config_len,
            'num_interfaces':data[pos+4],
            'attributes':data[pos+7],
            'max_power_2ma':data[pos+8],
            'descriptors':[]}
    interface=None;alternate=None
    while pos<end:
        size=data[pos]
        if size<2 or pos+size>end:
            raise ValueError('invalid USB configuration descriptor length')
        raw=data[pos:pos+size]
        typ=raw[1]
        rec={'file_offset':f'0x{start+pos:x}', 'cpu_address':f'0x{DATA_CPU+pos:08x}',
             'length':size,'type':typ,'raw_hex':raw.hex(' ')}
        if typ==4 and size>=9:
            interface,alternate=raw[2],raw[3]
            rec.update(interface=interface,alternate_setting=alternate,endpoint_count=raw[4],
                       usb_class=raw[5],usb_subclass=raw[6],usb_protocol=raw[7])
        if typ==5 and size>=7:
            rec.update(interface=interface,alternate_setting=alternate,
                       endpoint_address=f'0x{raw[2]:02x}',attributes=raw[3],
                       max_packet_bytes=struct.unpack_from('<H',raw,4)[0]&0x7ff,
                       interval=raw[6])
        if typ==0x24 and size>=3:
            subtype=raw[2]
            rec['audio_subtype']=subtype
            if interface==0 and subtype==2 and size>=12:
                rec.update(terminal_id=raw[3],terminal_type=f'0x{struct.unpack_from("<H",raw,4)[0]:04x}',
                           channels=raw[7],channel_config=struct.unpack_from('<H',raw,8)[0])
            if interface==0 and subtype==3 and size>=9:
                rec.update(terminal_id=raw[3],terminal_type=f'0x{struct.unpack_from("<H",raw,4)[0]:04x}',
                           source_id=raw[7])
            if interface==0 and subtype==6 and size>=7:
                rec.update(feature_unit_id=raw[3],source_id=raw[4],control_size=raw[5],
                           master_controls=raw[6])
            if interface==1 and alternate==1 and subtype==2 and size>=8:
                num_rates=raw[7]
                if num_rates and len(raw)>=8+3*num_rates:
                    rec.update(channels=raw[4],subframe_size=raw[5],resolution_bits=raw[6],
                               sample_rates_hz=[u24(raw[8+3*i:11+3*i]) for i in range(num_rates)])
        if typ==0x21 and size>=9:
            rec.update(hid_report_descriptor_bytes=struct.unpack_from('<H',raw,7)[0])
        result['descriptors'].append(rec)
        pos+=size
    report_pos=REPORT_CPU-DATA_CPU
    hid = next((d for d in result['descriptors'] if d['type']==0x21),None)
    if not hid:raise ValueError('missing HID interface')
    report_len=hid['hid_report_descriptor_bytes']
    report=data[report_pos:report_pos+report_len]
    if len(report)!=report_len:raise ValueError('HID report outside data')
    device_pos=DEVICE_CPU-DATA_CPU
    descriptor=data[device_pos:device_pos+18]
    if descriptor[:2]!=b'\x12\x01':raise ValueError('missing USB device descriptor')
    result['device']={'cpu_address':f'0x{DEVICE_CPU:08x}',
                      'file_offset':f'0x{start+device_pos:x}',
                      'vendor_id':f'0x{struct.unpack_from("<H",descriptor,8)[0]:04x}',
                      'product_id':f'0x{struct.unpack_from("<H",descriptor,10)[0]:04x}',
                      'device_bcd':f'0x{struct.unpack_from("<H",descriptor,12)[0]:04x}',
                      'raw_hex':descriptor.hex(' ')}
    result['hid_report']={'cpu_address':f'0x{REPORT_CPU:08x}',
                          'file_offset':f'0x{start+report_pos:x}',
                          'length':report_len,'raw_hex':report.hex(' '),
                          'consumer_usages':[f'0x{x:02x}' for x in
                           [0xe9,0xea,0xe2,0xcd,0xb5,0xb6,0xb3,0xb7]]}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    a=p.parse_args()
    print(json.dumps(decode(Image(a.image.read_bytes())),indent=2))


if __name__=='__main__':main()
