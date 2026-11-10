#!/usr/bin/env python3
"""Offline RGB565 resource catalog, theme editor and fail-closed patch engine.

Stock image assets carry no alpha channel in the package. We do not infer
transparency or runtime uses of raw constants from their numeric values.
"""
import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import struct
import sys

from rknano_image import Image
from extract_images import to_png

STOCK_SHA256 = "fcc1cd3e35b46f1f8dbcb8da39fcc5eb3f1d469cdfade5e9c6ea3bd71ac6deef"
ROLES = ("background", "text", "highlight", "icons", "progress_bar")
RESERVED = {0x0000, 0x00F8}  # conservative guards, NOT proven transparency keys
# Reviewed literal sites only. No stock code/data color site has yet been
# confirmed as UI-only, so this list is intentionally empty. To approve one,
# pin its module/region/address/source here after tracing its UI callers.
APPROVED_LITERAL_SITES = {}
OBSERVED = {
    0: "startup/spinner artwork",
    1: "QR-code artwork",
    6: "battery graphic, level variant 1",
    7: "battery graphic, level variant 2",
    8: "battery graphic, level variant 3",
    9: "battery graphic, level variant 4",
    10: "battery graphic, level variant 5",
}


def word(value):
    """Only explicit RGB565 words are valid as source/preserved-byte guards."""
    if isinstance(value, int) and not isinstance(value, bool):
        n = value
    elif isinstance(value, str) and value.lower().startswith("0x"):
        n = int(value, 16)
    else:
        raise ValueError("expected 16-bit RGB565 word such as 0xFFFF")
    if not 0 <= n <= 0xFFFF:
        raise ValueError("RGB565 word outside 0..65535")
    return n


def rgb565(color):
    if not isinstance(color, str) or len(color) != 7 or color[0] != "#":
        raise ValueError("palette colors must be #RRGGBB")
    try:
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError as exc:
        raise ValueError("invalid #RRGGBB color") from exc
    return ((r * 31 + 127) // 255 << 11 |
            (g * 63 + 127) // 255 << 5 |
            (b * 31 + 127) // 255)


def catalog(raw):
    im = Image(raw)
    assets = list(im.images())
    entries = []
    for a in assets:
        if not a["rgb565_bytes"] or a["size"] != 2 * a["width"] * a["height"]:
            raise ValueError("resource %d is not uncompressed RGB565" % a["id"])
        buf = memoryview(raw)[a["data_offset"]:a["data_offset"] + a["size"]]
        counts = Counter(x[0] for x in struct.iter_unpack("<H", buf))
        entries.append({
            **a,
            "observed_label": OBSERVED.get(a["id"], "unclassified"),
            "color_count": len(counts),
            "swatches": [{"rgb565": "0x%04X" % k, "count": n}
                         for k, n in counts.most_common(12)],
        })
    return entries


def parse_config(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("theme config must have version: 1")
    palette = data.get("palette")
    if not isinstance(palette, dict):
        raise ValueError("palette object missing")
    if set(palette) != set(ROLES):
        raise ValueError("palette must define exactly: " + ", ".join(ROLES))
    converted = {role: rgb565(palette[role]) for role in ROLES}
    resources = data.get("resources", [])
    literals = data.get("literal_sites", [])
    if not isinstance(resources, list) or not isinstance(literals, list):
        raise ValueError("resources and literal_sites must be arrays")
    return converted, resources, literals


def apply_theme(raw, config, protected_ranges=()):
    """Change only explicitly named pixels/verified literal sites.

    No raw-image-wide RGB565 replace. Every resource change has a pinned
    source word and source count; every literal has a pinned address and
    original bytes. All changes are attributed to an allowed region.
    """
    palette, rules, literals = parse_config(config)
    im = Image(raw)
    assets = list(im.images())
    output = bytearray(raw)
    claims = []
    changes = []
    used = set()
    claimed_assets = set()

    def claim(off, length, label):
        end = off + length
        if off < 0 or end > len(raw):
            raise ValueError("%s lies outside image" % label)
        for a, b in protected_ranges:
            if off < b and a < end:
                raise ValueError("%s overlaps an existing firmware patch" % label)
        for a, b, other in claims:
            if off < b and a < end:
                raise ValueError("%s overlaps %s" % (label, other))
        claims.append((off, end, label))

    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("resource rule must be object")
        idx = rule.get("id")
        role = rule.get("role")
        if type(idx) is not int or not 0 <= idx < len(assets):
            raise ValueError("resource id out of range")
        if role not in palette:
            raise ValueError("unknown resource role")
        source = word(rule.get("source"))
        expected = rule.get("expected_count")
        if type(expected) is not int or expected <= 0:
            raise ValueError("resource %d requires positive expected_count" % idx)
        explicit_preserve = {word(v) for v in rule.get("preserve", [])}
        if source in explicit_preserve:
            raise ValueError("resource %d: source is explicitly preserved" % idx)
        preserved = explicit_preserve | RESERVED
        if source in RESERVED:
            if not (rule.get("allow_reserved") is True and
                    len(str(rule.get("evidence", "")).strip()) >= 15):
                raise ValueError("resource %d: reserved/background-key candidate %04X; "
                                 "requires allow_reserved and documented evidence" %
                                 (idx, source))
            preserved.discard(source)
        key = (idx, source)
        if key in used:
            raise ValueError("duplicate resource id/source")
        used.add(key)
        a = assets[idx]
        if not a["rgb565_bytes"]:
            raise ValueError("resource %d is not RGB565" % idx)
        start, end = a["data_offset"], a["data_offset"] + a["size"]
        if idx not in claimed_assets:
            claim(start, a["size"], "resource %d" % idx)
            claimed_assets.add(idx)
        buf = raw[start:end]
        count = 0
        target = palette[role]
        for pos in range(0, len(buf), 2):
            current = struct.unpack_from("<H", buf, pos)[0]
            if current != source:
                continue
            if current in preserved:
                raise AssertionError("preserved pixel selected")
            count += 1
            struct.pack_into("<H", output, start + pos, target)
        if count != expected:
            raise ValueError("resource %d: expected %d source pixels, found %d" %
                             (idx, expected, count))
        changes.append({"kind": "resource", "id": idx, "role": role,
                        "file_offset": hex(start), "bytes": a["size"],
                        "source": "0x%04X" % source,
                        "target": "0x%04X" % target, "pixels": count})

    for rule in literals:
        if not isinstance(rule, dict):
            raise ValueError("literal site must be object")
        role = rule.get("role")
        if role not in palette:
            raise ValueError("unknown literal-site role")
        evidence = rule.get("evidence")
        if not isinstance(evidence, str) or len(evidence.strip()) < 15:
            raise ValueError("literal requires source-level/disassembly evidence")
        mid = rule.get("module")
        region = rule.get("region")
        if type(mid) is not int or not 0 <= mid < len(im.modules):
            raise ValueError("literal module invalid")
        if region not in ("code", "data"):
            raise ValueError("literal region must be code or data")
        address = rule.get("address")
        if not isinstance(address, str) or not address.startswith("0x"):
            raise ValueError("literal requires hex CPU address")
        address = int(address, 16)
        rel = address - im.modules[mid][region + "_exec"]
        if rel < 0 or rel + 2 > im.modules[mid][region + "_len"] or address % 2:
            raise ValueError("literal outside its module region or unaligned")
        start, _ = im.module_region(mid, region)
        off = start + rel
        expected = word(rule.get("source"))
        site_key = (mid, region, address, expected)
        if site_key not in APPROVED_LITERAL_SITES:
            raise ValueError("literal %08X is not in reviewed UI-only registry" %
                             address)
        if struct.unpack_from("<H", raw, off)[0] != expected:
            raise ValueError("literal at %08X: original word does not match" % address)
        if expected in RESERVED and not rule.get("allow_reserved"):
            raise ValueError("reserved literal requires explicit opt-in")
        claim(off, 2, "literal %08X" % address)
        struct.pack_into("<H", output, off, palette[role])
        changes.append({"kind": "literal", "module": mid, "region": region,
                        "cpu_address": hex(address), "role": role,
                        "file_offset": hex(off), "bytes": 2,
                        "source": "0x%04X" % expected,
                        "target": "0x%04X" % palette[role],
                        "evidence": evidence})

    if len(output) != len(raw):
        raise AssertionError("image length changed")
    # Full-byte diff attribution; catches stray writes, including outside assets.
    allowed = sorted((a, b) for a, b, _ in claims)
    changed = [i for i, (a, b) in enumerate(zip(raw, output)) if a != b]
    j = 0
    for offset in changed:
        while j < len(allowed) and allowed[j][1] <= offset:
            j += 1
        if j == len(allowed) or offset < allowed[j][0]:
            raise AssertionError("unattributed theme diff at %x" % offset)
    return bytes(output), {"changes": changes, "changed_bytes": len(changed),
                           "claims": [{"start": hex(a), "end_exclusive": hex(b),
                                      "target": name} for a, b, name in claims]}


def scan_literals(raw, colors):
    """Discovery only. An exact 16-bit match is not proof of UI color usage."""
    im = Image(raw)
    results = []
    for m in im.modules:
        for region in ("code", "data"):
            start, size = im.module_region(m["index"], region)
            if not size:
                continue
            for delta in range(0, size - 1, 2):
                v = struct.unpack_from("<H", raw, start + delta)[0]
                if v in colors:
                    results.append({"module": m["index"], "region": region,
                                    "address": hex(m[region + "_exec"] + delta),
                                    "file_offset": hex(start + delta),
                                    "rgb565": "0x%04X" % v,
                                    "status": "UNVERIFIED_CANDIDATE"})
    return results


EDITOR_JS = r"""
const assets = JSON.parse(document.getElementById('catalog-data').textContent);
const roles = ['background', 'text', 'highlight', 'icons', 'progress_bar'];
const palette = {background:'#161923',text:'#FFFFFF',highlight:'#27A5F8',
                 icons:'#E4ECF7',progress_bar:'#40BFFF'};
const rules = new Map();
let selected = 0;
const byId = id => document.getElementById(id);
const grid = byId('grid'), canvas = byId('preview');
function rgb565(r,g,b) {
  return ((Math.round(r*31/255)<<11)|(Math.round(g*63/255)<<5)|Math.round(b*31/255));
}
function rgb8(v) { return [Math.floor(((v>>11)&31)*255/31),
                            Math.floor(((v>>5)&63)*255/63),
                            Math.floor((v&31)*255/31)]; }
function currentAsset() { return assets[selected]; }
function show() {
  const a=currentAsset(), rule=rules.get(selected);
  byId('info').textContent='Asset '+selected+'  '+a.width+'x'+a.height+
    '  file '+a.data_offset.toString(16)+'  '+a.observed_label;
  byId('asset').src='assets/asset_'+String(selected).padStart(3,'0')+'.png';
  byId('role').value=rule?.role||'highlight';
  byId('source').innerHTML='';
  for (const s of a.swatches) {
    const opt=document.createElement('option'); opt.value=s.rgb565;
    opt.textContent=s.rgb565+'  ('+s.count+' pixels)';
    byId('source').appendChild(opt);
  }
  if (rule) byId('source').value=rule.source;
  byId('chosen').textContent=rules.size+' resource rules selected';
  byId('asset').onload=render;
}
function render() {
  const a=currentAsset(); const img=byId('asset');
  canvas.width=a.width;canvas.height=a.height;
  const ctx=canvas.getContext('2d', {willReadFrequently:true});
  ctx.drawImage(img,0,0);
  const data=ctx.getImageData(0,0,a.width,a.height);
  const source=parseInt(byId('source').value), target=parseInt(
    palette[byId('role').value].substring(1),16);
  const out=rgb565((target>>16)&255,(target>>8)&255,target&255);
  if (!Number.isNaN(source)) {
    const converted=rgb8(out);
    for(let i=0;i<data.data.length;i+=4) {
      if(rgb565(data.data[i],data.data[i+1],data.data[i+2])===source) {
        data.data[i]=converted[0];data.data[i+1]=converted[1];
        data.data[i+2]=converted[2];
      }
    }
  }
  ctx.putImageData(data,0,0);
}
function setRule() {
  const source=parseInt(byId('source').value);
  if(source===0 || source===0x00f8) {
    alert('Reserved key candidate. Review transparency and edit JSON manually with evidence.');
    return;
  }
  const sw=currentAsset().swatches.find(s=>parseInt(s.rgb565)===source);
  if(!sw) {alert('Select a cataloged source color');return;}
  rules.set(selected,{id:selected,role:byId('role').value,
                      source:sw.rgb565,expected_count:sw.count});
  show();
}
function download() {
  const cfg={version:1,palette,resources:[...rules.values()],literal_sites:[]};
  const url=URL.createObjectURL(new Blob([JSON.stringify(cfg,null,2)+'\n'],
                                           {type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='theme.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
roles.forEach(role=>{
  const item=document.createElement('label');item.textContent=role+' ';
  const input=document.createElement('input');input.type='color';input.value=palette[role];
  input.addEventListener('input',()=>{palette[role]=input.value;render();});
  item.append(input);byId('colors').append(item);
});
assets.forEach(a=>{
  const node=document.createElement('button');
  node.innerHTML='<img loading="lazy" src="assets/asset_'+String(a.id).padStart(3,'0')+
                 '.png"><span>#'+a.id+'</span>';
  node.title=a.observed_label+' ('+a.width+'x'+a.height+')';
  node.onclick=()=>{selected=a.id;show();};grid.append(node);
});
byId('role').addEventListener('change',render);
byId('source').addEventListener('change',render);
byId('add').onclick=setRule;
byId('remove').onclick=()=>{rules.delete(selected);show();};
byId('export').onclick=download;
show();
"""


def write_catalog(raw, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    entries = catalog(raw)
    (output / "catalog.json").write_text(json.dumps({
        "stock_sha256": hashlib.sha256(raw).hexdigest(),
        "format": "RGB565_LE", "resource_count": len(entries),
        "notes": "Roles other than observed labels require visual review. "
                 "No alpha/transparency key is established by RGB565 bytes.",
        "resources": entries}, indent=2) + "\n")
    for a in entries:
        off, size = a["data_offset"], a["size"]
        png = to_png(raw[off:off + size], a["width"], a["height"])
        (output / "assets" / ("asset_%03d.png" % a["id"])).write_bytes(png)
    page = """<!doctype html><html><head><meta charset="utf-8">
<title>DAP Neo offline theme editor</title><style>
body{font:15px system-ui;margin:20px;background:#151821;color:#f2f5fa}
header{position:sticky;top:0;background:#151821;padding:10px;z-index:1}
label{display:inline-block;margin:7px}button{cursor:pointer}
#grid{display:grid;grid-template-columns:repeat(auto-fill, minmax(84px,1fr));gap:7px}
#grid button{background:#293141;color:white;border:1px solid #465068;min-height:82px}
#grid img{display:block;width:70px;height:65px;object-fit:contain;margin:auto;image-rendering:pixelated}
#grid span{display:block}#asset{display:none}#preview{max-width:100%;max-height:320px;image-rendering:pixelated;background:#242a36}
#controls{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
select,button{padding:7px}#notice{max-width:900px;color:#c8d0df}
</style></head><body><header><h2>DAP Neo offline theme editor</h2>
<p id="notice">Every edit is opt-in. Only exact RGB565 source pixels you select will change.
Black (0x0000) and 0x00F8 are blocked as possible keys. Other transparency
semantics are unverified. Export JSON, then run the firmware builder offline.</p>
<div id="colors"></div><div id="info"></div><div id="controls">
<label>Role <select id="role"><option>background</option><option>text</option>
<option>highlight</option><option>icons</option><option>progress_bar</option></select></label>
<label>Original color <select id="source"></select></label>
<button id="add">Add selected color</button><button id="remove">Remove asset rule</button>
<button id="export">Export theme.json</button><span id="chosen"></span></div>
<canvas id="preview"></canvas><img id="asset" alt=""></header>
<h3>All stock RGB565 resources (click an asset)</h3><div id="grid"></div>
<script id="catalog-data" type="application/json">__CATALOG__</script>
<script>__JS__</script></body></html>"""
    page = page.replace("__CATALOG__", json.dumps(entries).replace("</", "<\\/"))
    page = page.replace("__JS__", EDITOR_JS)
    (output / "index.html").write_text(page, encoding="utf-8")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path, help="unmodified DP3_V137.img")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("catalog", help="456-asset offline editor + JSON map")
    p.add_argument("directory", type=Path)
    p = commands.add_parser("preview", help="render theme-changed PNGs without touching firmware")
    p.add_argument("config", type=Path)
    p.add_argument("directory", type=Path)
    p = commands.add_parser("scan-literals", help="list UNVERIFIED RGB565 module matches")
    p.add_argument("colors", nargs="+", help="16-bit RGB565 words, e.g. 0xFFFF")
    p.add_argument("--output", type=Path)
    a = parser.parse_args()
    raw = a.stock.read_bytes()
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA256:
        parser.error("stock image SHA-256 mismatch")
    if a.command == "catalog":
        entries = write_catalog(raw, a.directory)
        print("wrote %d RGB565 resources and offline editor to %s" %
              (len(entries), a.directory / "index.html"))
    elif a.command == "preview":
        config = json.loads(a.config.read_text())
        changed, report = apply_theme(raw, config)
        a.directory.mkdir(parents=True, exist_ok=True)
        entries = list(Image(raw).images())
        for c in report["changes"]:
            if c["kind"] == "resource":
                e = entries[c["id"]]
                off, size = e["data_offset"], e["size"]
                (a.directory / ("asset_%03d_before.png" % c["id"])).write_bytes(
                    to_png(raw[off:off + size], e["width"], e["height"]))
                (a.directory / ("asset_%03d_after.png" % c["id"])).write_bytes(
                    to_png(changed[off:off + size], e["width"], e["height"]))
        (a.directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print("preview: %d rule(s), %d differing bytes" %
              (len(report["changes"]), report["changed_bytes"]))
    else:
        results = scan_literals(raw, set(map(word, a.colors)))
        result = json.dumps(results, indent=2) + "\n"
        if a.output:
            a.output.write_text(result)
        else:
            print(result)
        print("%d unverified candidates (NOT an approved UI color map)" %
              len(results), file=sys.stderr)


if __name__ == "__main__":
    main()
