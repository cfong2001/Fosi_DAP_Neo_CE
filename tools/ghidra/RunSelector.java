// Run on the raw image mapped at file offset zero. See README.md.
//@category Firmware
import ghidra.app.script.GhidraScript;
import ghidra.app.emulator.EmulatorHelper;
import java.math.BigInteger;
public class RunSelector extends GhidraScript {
 public void run() throws Exception {
  byte[] expected={(byte)0x01,(byte)0x46,(byte)0x00,(byte)0x20,(byte)0x09,(byte)0x29,(byte)0x28,(byte)0xbf,(byte)0x70,(byte)0x47,(byte)0xdf,(byte)0xe8,(byte)0x01,(byte)0xf0};
  byte[] actual=new byte[expected.length]; currentProgram.getMemory().getBytes(toAddr(0x846ba),actual);
  if(!java.util.Arrays.equals(expected,actual)) throw new IllegalStateException("unexpected image or base address");
  currentProgram.getProgramContext().setValue(currentProgram.getRegister("TMode"),toAddr(0x846ba),toAddr(0x846ed),BigInteger.ONE);
  disassemble(toAddr(0x846ba));
  for(int a : new int[]{0x846d2,0x846d4,0x846d6,0x846da,0x846de,0x846e2,0x846e6,0x846ea}) disassemble(toAddr(a));
  int[] results={0,1,1,2,3,0,5,6,7,0,0,0,0};
  for(int input=0;input<results.length;input++) {
   EmulatorHelper e=new EmulatorHelper(currentProgram);
   e.writeRegister("r0",input); e.writeRegister("lr",0x90001); e.writeRegister("pc",0x846ba);
   int steps=0;
   while(e.getExecutionAddress().getOffset()!=0x90000 && steps++<20) if(!e.step(monitor)) throw new IllegalStateException("input="+input+" pc="+e.getExecutionAddress()+" "+e.getLastError());
   int result=e.readRegister("r0").intValue();
   println("input="+input+" result="+result+" steps="+steps+" pc="+e.getExecutionAddress());
   if(e.getExecutionAddress().getOffset()!=0x90000 || result!=results[input]) throw new IllegalStateException("unexpected result");
   e.dispose();
  }
 }
}
