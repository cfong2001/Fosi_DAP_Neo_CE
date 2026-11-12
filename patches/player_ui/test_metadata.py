"""Execute generated player hooks with synthetic playback metadata."""
import struct
import unittest
from test_typography import Typography, REPO, HERE, END
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from build import parse_patch

class Metadata(Typography):
    # Inherit the typography machine factory, not its tests.
    def machine(self):
        u=super().machine()
        for p in HERE.glob('016*.patch'):
            row=parse_patch(p);u.mem_write(row['address'],row['replace'])
        return u
    def text(self,u,address,value):u.mem_write(address,(value+'\0').encode('utf-16le'))
    def read_text(self,u,address,units=128):return bytes(u.mem_read(address,units*2)).decode('utf-16le').split('\0')[0]
    def test_player_title_hook(self):
        for title,name,want in [('Tagged.wav','01 - disk.flac','Tagged.wav'),('','01 - disk.flac','01 - disk.flac'),('X'*128,'fallback','X'*127),('','','')]:
            u=self.machine();self.text(u,0x0304AF84,title);self.text(u,0x0304ADF4,name)
            u.mem_write(0x03024802,b'\x5a'*260);writes=[]
            def hook(uc,access,addr,size,value,data):
                if 0x03024802<=addr<0x03024906:writes.append((addr,size))
            u.hook_add(UC_HOOK_MEM_WRITE,hook)
            u.reg_write(UC_ARM_REG_R0,1)
            u.emu_start(0x0307F9CD,0x0307F9EE,count=10000)
            self.assertEqual(self.read_text(u,0x03024804),want)
            self.assertTrue(all(0x03024804<=a and a+n<=0x03024904 for a,n in writes))
            self.assertEqual(u.mem_read(0x03024802,2),b'ZZ')
            self.assertEqual(u.mem_read(0x03024904,2),b'ZZ')
    def paint(self,title='Title tag',artist='Artist tag',album='Album tag',codec_id=6,bits=24,rate=96000,bitrate=2915000,size=98600000,have_codec=True):
        u=self.machine();self.text(u,0x0304AF84,title);self.text(u,0x0304B082,artist);self.text(u,0x0304B180,album)
        self.text(u,0x0304ADF4,'fallback.flac')
        u.mem_write(0x0304B4D4,struct.pack('<I',codec_id));u.mem_write(0x0304AD78,struct.pack('<I',0x030D0000 if have_codec else 0))
        for off,val in ((8,rate),(12,bitrate),(0x9c,bits)):u.mem_write(0x030D0000+off,struct.pack('<I',val))
        u.mem_write(0x0302385C,struct.pack('<H',0x1234));u.mem_write(0x030235B6,struct.pack('<H',0xABCD));u.mem_write(0x03004400,b'\x22\x11')
        rows=[];fills=[]
        def hook(uc,addr,n,data):
            if addr==0x030545D4:uc.reg_write(UC_ARM_REG_R0,size)
            elif addr==0x03062CEE:
                rows.append((struct.unpack('<4h',uc.mem_read(uc.reg_read(UC_ARM_REG_R0),8)),self.read_text(uc,uc.reg_read(UC_ARM_REG_R2))))
            elif addr==0x030632FA:fills.append(tuple(uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)))
            else:return
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE,hook)
        for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11):u.reg_write(reg,0x12345678)
        u.emu_start(0x0307E987,END,count=100000)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC),END)
        self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x030ED000)
        self.assertEqual(u.mem_read(0x0302385C,2),b'\x34\x12')
        self.assertEqual(len(rows),14);self.assertEqual(fills,[(0,32,239,191)])
        for i,(r,t) in enumerate(rows):self.assertTrue(0<=r[0]<r[2]<240 and 32<=r[1]<=r[3]<192)
        for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11):self.assertEqual(u.reg_read(reg),0x12345678)
        return [t for r,t in rows]
    def test_seven_labeled_rows_and_units(self):
        self.assertEqual(self.paint(),['Title','Title tag','Artist','Artist tag','Album','Album tag','Format','FLAC','Resolution','24-bit / 96 kHz','Bitrate','2915 kbps','Size','98.6 MB'])
    def test_fallbacks_and_sample_rate_precision(self):
        values=self.paint(title='',artist='',album='',codec_id=255,have_codec=False,size=0)
        self.assertEqual(values[1],'fallback.flac');self.assertEqual(values[3:12:2],['Unknown']*5);self.assertEqual(values[-1],'0.0 MB')
        for rate,text in ((44100,'44.1'),(11025,'11.025'),(352800,'352.8')):
            self.assertEqual(self.paint(rate=rate)[9],'24-bit / '+text+' kHz')
        self.assertEqual(self.paint(size=0xffffffff)[-1],'4295.0 MB')

if __name__=='__main__':unittest.main()
