import test from "node:test";
import assert from "node:assert/strict";
import {
  ROLES, STOCK_SHA256, rgb565, rgb888, asWord, wordHex, parseFirmware,
  frequencies, rgbaPixels, validateTheme, exportConfig, sha256
} from "../docs/theme-core.mjs";

const WIDTH = 1, HEIGHT = 1, TOTAL = 456;
const makePalette = () => ({
  background: "#141821", text: "#F5F7FA", highlight: "#38BDF8",
  icons: "#DCECF8", progress_bar: "#38BDF8"
});

function syntheticFirmware() {
  const bytes = new Uint8Array(0xD00004), v = new DataView(bytes.buffer);
  const ascii = (off, str) => {
    for (let i=0; i<str.length; i++) bytes[off+i]=str.charCodeAt(i);
  };
  ascii(0x10, "Rockchip");
  ascii(0x1f8, "RKnanoFW");
  const sectionStart = 0x4000;
  const payloadStart = 0x20 + TOTAL * 16;
  const sectionLength = payloadStart + TOTAL * 2;
  v.setUint32(0x14c, sectionStart, true);
  v.setUint32(0x150, sectionLength, true);
  ascii(sectionStart, "ROCK26IMAGERES  ");
  v.setUint32(sectionStart+16, TOTAL, true);
  for(let i=0;i<TOTAL;i++) {
    const p=sectionStart+0x20+i*16;
    v.setUint16(p,WIDTH,true);
    v.setUint16(p+2,HEIGHT,true);
    v.setUint16(p+4,0,true);
    v.setUint16(p+6,0,true);
    v.setUint32(p+8,2,true);
    v.setUint32(p+12,payloadStart+i*2,true);
    v.setUint16(sectionStart+payloadStart+i*2, i===6 ? 0xA210 : 0x001F,true);
  }
  return bytes;
}

test("RGB888/RGB565 colors convert and validate",()=>{
  assert.equal(rgb565("#FFFFFF"),0xFFFF);
  assert.equal(rgb565("#000000"),0);
  assert.equal(rgb565("#FF0000"),0xF800);
  assert.deepEqual(rgb888(0x001F),[0,0,255]);
  assert.equal(asWord("0xA210"),41488);
  assert.equal(wordHex(41488),"0xA210");
  assert.equal(ROLES.length,5);
  assert.equal(STOCK_SHA256.length,64);
});

test("synthetic Rockchip package maps 456 RGB565 records",()=>{
  const f=parseFirmware(syntheticFirmware());
  assert.equal(f.entries.length,456);
  assert.equal(f.entries[6].width,1);
  assert.equal(f.entries[6].label,"battery graphic 1");
  assert.deepEqual(frequencies(f,f.entries[6]),
    [{word:0xA210,count:1,hex:"0xA210"}]);
});

test("theme recolor changes preview pixels but never input bytes",()=>{
  const f=parseFirmware(syntheticFirmware()), asset=f.entries[6];
  const original=rgbaPixels(f,asset);
  const recolored=rgbaPixels(f,asset,new Map([[0xA210,rgb565("#38BDF8")]]));
  assert.notDeepEqual(original,recolored);
  assert.deepEqual(rgbaPixels(f,asset),original);
  assert.equal(f.view.getUint16(asset.data_offset,true),0xA210);
  // Panel order: stored bytes 10 A2 (named 0xA210) show as RGB565 0x10A2,
  // and a replacement shows as the palette colour itself.
  assert.deepEqual([...original.subarray(0,3)],rgb888(0x10A2));
  assert.deepEqual([...recolored.subarray(0,3)],rgb888(rgb565("#38BDF8")));
});

test("theme schema rejects reserved keys, duplicate selections and extra roles",()=>{
  const f=parseFirmware(syntheticFirmware());
  const cfg={version:1,palette:makePalette(),resources:[{
    id:6,role:"highlight",source:"0xA210",expected_count:1
  }],literal_sites:[]};
  assert.equal(validateTheme(cfg,f.entries),cfg);
  assert.throws(()=>validateTheme({...cfg,resources:[
    {...cfg.resources[0],source:"0x0000"}]},f.entries),/Reserved/);
  assert.throws(()=>validateTheme({...cfg,resources:[...cfg.resources,...cfg.resources]},f.entries),/Duplicate/);
  assert.throws(()=>validateTheme({...cfg,palette:{...cfg.palette,other:"#000000"}},f.entries),/five known roles/);
  assert.throws(()=>validateTheme({...cfg,resources:[{...cfg.resources[0],id:999}]},f.entries),/outside/);
});

test("export keeps stable order and does not include code patches",()=>{
  const c=exportConfig(makePalette(),[
    {id:8,role:"highlight",source:"0xA210",expected_count:1},
    {id:6,role:"highlight",source:"0xA210",expected_count:1}
  ]);
  assert.deepEqual(c.resources.map(x=>x.id),[6,8]);
  assert.deepEqual(c.literal_sites,[]);
});

test("SHA-256 runs locally in secure Node/browser contexts",async()=>{
  const hash=await sha256(new TextEncoder().encode("abc"));
  assert.equal(hash,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
});
