"""Real artwork extraction and JPEG/theater execution; filesystem and LCD leaves modeled."""
import sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from rknano_image import Image
from unicorn import *
from unicorn.arm_const import *

def extract(raw,data,decode=False):
 im=Image(raw);u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x03000000,0x100000)
 for m in (0,18,19):
  for kind in ('code','data'):
   o,n=im.module_region(m,kind);u.mem_write(im.modules[m][kind+'_exec'],raw[o:o+n])
 u.mem_write(0x300443c,struct.pack('<II',0x3058fa9,0x30594a1))
 blits=[]
 files={7:bytes(data),2:b''};positions={7:0,2:0};calls=[]
 def hook(u,a,size,_):
  if a not in (0x3058fa8,0x30594a0,0x30545d4,0x3058e8e,0x305c86a,0x305c822,0x305ca1c,0x306d8f0,0x30611e0,0x3058cc6,0x3067870,0x306333e):return
  args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)];v=0
  if a==0x3058cc6:positions[2]=0;v=2
  elif a==0x3067870:v=0
  elif a==0x306333e:
   mode,ptr=struct.unpack('<II',u.mem_read(u.reg_read(UC_ARM_REG_SP),8));assert mode==16
   blits.append(struct.unpack('<%dH'%args[2],u.mem_read(ptr,args[2]*2)));v=0
  elif a==0x3058fa8:
   dst,n,h=args[:3];assert h in files,(hex(a),args);p=positions[h];block=files[h][p:p+n];positions[h]+=len(block);u.mem_write(dst,block);v=len(block)
  elif a==0x30594a0:
   off,whence,h=args[:3];assert h in files,(hex(a),args);off=off if off<0x80000000 else off-0x100000000;positions[h]=off+(positions[h] if whence else 0);v=positions[h]
  elif a==0x30545d4:v=len(files[args[0]])
  elif a==0x305c822:files[2]=b'';positions[2]=0;v=2
  elif a==0x305ca1c:
   ptr,off,n,h=args;assert h==2,(hex(a),args);block=bytes(u.mem_read(ptr,n));files[h]=files[h][:off]+block+files[h][off+n:];v=n
  elif a==0x3058e8e:v=0
  elif a==0x306d8f0:pass
  calls.append(a);u.reg_write(UC_ARM_REG_R0,v&0xffffffff);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 for a in (0x3058fa8,0x30594a0,0x30545d4,0x3058e8e,0x305c86a,0x305c822,0x305ca1c,0x306d8f0,0x30611e0,0x3058cc6,0x3067870,0x306333e):u.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 kept=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
 for reg in kept:u.reg_write(reg,0x12345678)
 u.mem_write(0x30d0000,b'Z'*8+b'\xff'*4+b'Z'*8)
 for reg,v in ((UC_ARM_REG_R0,7),(UC_ARM_REG_R1,0x30d0008),(UC_ARM_REG_SP,0x30f0000),(UC_ARM_REG_LR,0x30ef001)):u.reg_write(reg,v)
 try:u.emu_start(0x3083277,0x30ef000,count=100000000)
 except Exception as e:raise AssertionError((hex(u.reg_read(UC_ARM_REG_PC)),hex(u.reg_read(UC_ARM_REG_LR)))) from e
 assert u.reg_read(UC_ARM_REG_PC)==0x30ef000,hex(u.reg_read(UC_ARM_REG_PC))
 assert u.reg_read(UC_ARM_REG_SP)==0x30f0000
 assert bytes(u.mem_read(0x30d0000,8))==b'Z'*8 and bytes(u.mem_read(0x30d000c,8))==b'Z'*8
 assert all(u.reg_read(reg)==0x12345678 for reg in kept)
 if decode:
  for a,v in ((0x302598c,30),(0x3025990,18),(0x3025994,23),(0x3025998,36),(0x30259dc,1)):
   u.mem_write(a,struct.pack('<I',v))
  def call(a,r0=0,r1=0):
   for reg,v in ((UC_ARM_REG_R0,r0),(UC_ARM_REG_R1,r1),(UC_ARM_REG_R2,0),(UC_ARM_REG_R3,0),(UC_ARM_REG_SP,0x30f0000),(UC_ARM_REG_LR,0x30ef001)):u.reg_write(reg,v)
   u.emu_start(a|1,0x30ef000,count=10000000);assert u.reg_read(UC_ARM_REG_PC)==0x30ef000,hex(u.reg_read(UC_ARM_REG_PC))
   return u.reg_read(UC_ARM_REG_R0)
  assert call(0x308389e,7,0)==1,'native JPEG setup failed'
  for _ in range(18):call(0x3083b36)
  ground=struct.unpack('<H',u.mem_read(0x3004400,2))[0]
  return blits,ground
 return u.reg_read(UC_ARM_REG_R0),struct.unpack('<I',u.mem_read(0x30d0008,4))[0],files[2],calls
