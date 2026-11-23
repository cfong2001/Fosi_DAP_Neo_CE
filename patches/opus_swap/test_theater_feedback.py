"""Close the native artwork-completion -> player repaint -> artwork-request loop."""
from pathlib import Path
import sys,struct
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(Path(__file__).resolve().parent),str(ROOT/'tools'),str(ROOT/'patches/full/build')]
from artwork_harness import extract
from test_artwork_route import fixture_jpeg,picture,stream
import base64
from rknano_image import Image
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
def feedback(raw):
 def observer(u,call,blits,files):
  im=Image(raw)
  for kind in ('code','data'):
   o,n=im.module_region(27,kind);u.mem_write(im.modules[27][kind+'_exec'],raw[o:o+n])
  def skip(u,a,n,_):u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
  # 0x3063a08: keyed helper, the player's speaker draw (status bar patch 0284)
  for a in (0x306354a,0x3063a08,0x3063700,0x3063642):u.hook_add(UC_HOOK_CODE,skip,begin=a,end=a)
  grounds=[];repaints=0
  for _ in range(3):
   events=struct.unpack('<I',u.mem_read(0x3023cfc,4))[0]
   if not events & (1<<25):break
   u.reg_write(UC_ARM_REG_SP,0x30f0000);u.emu_start(0x307ef7b,0x307f084,count=1000000);assert u.reg_read(UC_ARM_REG_PC)==0x307f084
   events=struct.unpack('<I',u.mem_read(0x3023cfc,4))[0];assert events & (1<<27),'repaint did not request art'
   u.mem_write(0x3023cfc,struct.pack('<I',events & ~(1<<27)));repaints+=1
   assert call(0x308389e,7,0)==1
   grounds.append(struct.unpack('<H',u.mem_read(0x3004400,2))[0])
   for _ in range(18):call(0x3083b36)
  pending=bool(struct.unpack('<I',u.mem_read(0x3023cfc,4))[0] & (1<<25))
  changed=None
  if not pending:
   import io
   from PIL import Image as PillowImage
   out=io.BytesIO();PillowImage.new('RGB',(30,18),'white').save(out,'JPEG')
   files[2]=picture(out.getvalue())
   assert call(0x308389e,7,0)==1
   assert struct.unpack('<H',u.mem_read(0x3004400,2))[0]==0x7000
   for _ in range(18):call(0x3083b36)
   assert struct.unpack('<H',u.mem_read(0x3004400,2))[0]==0x738e
   changed=bool(struct.unpack('<I',u.mem_read(0x3023cfc,4))[0] & (1<<25))
   assert changed, 'changed artwork failed to request a repaint'
  return {'repaints':repaints,'setup_grounds':grounds,'pending_repaint':pending,
          'changed_art_requests_repaint':changed}
 return extract(raw,stream(base64.b64encode(picture(fixture_jpeg()))),decode=True,observe=observer)


def check(raw):
 import hashlib,runpy
 from build_tail import branch
 source=runpy.run_path(str(ROOT/'patches/full/build/theater/build_theater.py'))
 reset=list(source['RESET_ASM']);at=reset.index('pop {r2, r3}')
 previous=[*source['load']('r3',0x030232A0),'ldrb r2, [r3, #0x2d8]',
           'cmp r2, #0','bne rst_light','movw r2, #0x10a2','b rst_store',
           'rst_light:',*source['load']('r3',0x030235B4),'ldrh r2, [r3, #0]',
           'rst_store:',*source['load']('r3',0x03004400),'strh r2, [r3, #0]']
 reset[at:at]=previous
 tail=[line for line in source['TRAMP_TAIL_ASM'] if line not in
       ('ldrh r1, [r0]','cmp r1, r5','beq color_unchanged','color_unchanged:')]
 base=0x0307C350
 body,_=source['assemble'](reset,base);body+=branch(base+len(body),0x030838A2)
 entry=base+len(body);head,_=source['assemble'](source['TRAMP_HEAD_ASM'],entry)
 site=entry+len(head);last,_=source['assemble'](tail,site+4)
 old=body+head+branch(site,source['BITMAP'],True)+last
 assert hashlib.sha256(old).hexdigest()=='53dce973e3bf970ce66fd53501c0ccf23f929c5d80a4e61870bca4370447d1df'
 image=Image(raw);legacy=bytearray(raw)
 off,_=image.module_region(0,'code');pos=off+base-image.modules[0]['code_exec'];legacy[pos:pos+680]=old
 for site in source['BLIT_SITES']:
  off,_=image.module_region(18,'code');pos=off+site-image.modules[18]['code_exec'];legacy[pos:pos+4]=branch(site,entry,True)
 before=feedback(bytes(legacy));after=feedback(raw)
 assert before['repaints']==3 and before['pending_repaint']
 assert before['setup_grounds']==[0x10A2]*3
 assert after['repaints']==1 and not after['pending_repaint']
 assert after['setup_grounds']==[0x7000], 'resampling changed displayed ground'
 return {'legacy':before,'repaired':after,'same_cover_loop_settled':True,
         'displayed_color_preserved_during_resampling':True}

if __name__=='__main__':
 import json
 print(json.dumps(check(Path(sys.argv[1]).read_bytes()),indent=2))
