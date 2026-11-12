// CE builder panel wiring (section 4 of docs/index.html).
//
// The build itself lives in builder-core.mjs and mirrors
// patches/framework/build.py; the data comes from the generated
// modules beside this file (see generate_builder_data.py). The
// studio half (theme.js) exposes its verified firmware and current
// theme config through window.dapNeoStudio.
import {buildFirmware, hexToBytes} from "./builder-core.mjs";
import {PATCH_GROUPS} from "./builder-data.mjs";
import {VORBIS75} from "./builder-vorbis.mjs";
import {OPUS_PATCHES} from "./builder-opus.mjs";
import {CE_MARK_RUNS} from "./builder-cemark.mjs";
import {PRESETS} from "./builder-presets.mjs";
import {THEATER_PATCHES, THEATER_TAIL} from "./builder-theater.mjs";
import {BT_PATCH, LOCK_PATCH, TITLE_PATCHES, bluetoothTail, lockscreenPayload, combineTails, theaterTail, combineWithTheater} from "./builder-experimental.mjs";
import {BT_PAYLOAD, LOCK_PAYLOAD} from "./builder-payloads.mjs";
import {FULL_EXTRA_PATCHES, FULL_TAIL, FULL_GROWTHS, FULL_THEME_RUNS, FULL_IMAGE_SHA256} from "./builder-full.mjs";
import {sha256} from "./theme-core.mjs";
import {githubUrl, repoFromLocation} from "./repo.mjs";
import {SLOTS, bandTable, parseCurve, fit, slotPatches} from "./eq-core.mjs";
import {DAC_FILTERS, dacFilterPatches} from "./builder-dacfilter.mjs";
import {BT_AUTO_OFF, btAutoOffPatches} from "./builder-btautooff.mjs";

// The everything build's payloads are embedded in builder-full.mjs
// (generated from patches/full/) and are checked against their
// pinned SHA-256 values before use, like the local-file payloads.
async function fullTailPayload() {
  const bytes = hexToBytes(FULL_TAIL.hex);
  if (bytes.length !== FULL_TAIL.length || await sha256(bytes) !== FULL_TAIL.sha256)
    throw new Error("merged tail payload does not match its pinned SHA-256");
  return bytes;
}

async function fullGrowthPayloads() {
  const out = [];
  for (const g of FULL_GROWTHS) {
    const payload = hexToBytes(g.hex);
    if (payload.length !== g.length || await sha256(payload) !== g.sha256)
      throw new Error("module " + g.module + " growth payload does not " +
        "match its pinned SHA-256");
    out.push({module: g.module, payload});
  }
  return out;
}

const $ = id => document.getElementById(id);

function setStatus(message, kind = "") {
  const el = $("build-status");
  el.textContent = message;
  el.className = "status" + (kind ? " " + kind : "");
}

function download(name, bytes) {
  const url = URL.createObjectURL(
    new Blob([bytes], {type: "application/octet-stream"}));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// Offer the build to the install flow at the top of the page
// (install.mjs), which can copy it to the player as RKNANOFWIMG.
function offerToInstaller(name, result) {
  window.dispatchEvent(new CustomEvent("ce-build",
    {detail: {name, bytes: result.bytes, sha256: result.sha256}}));
}

// The feature checklist for picked builds. Framework groups (id "g:...")
// come from builder-data.mjs; the rest are this page's options.
const FEATURES = [
  {heading: "Sound", items: [
    {id: "vorbis", patch: "patches/vorbis_swap/", title: "Full-precision Vorbis", on: true,
     note: "Decodes Ogg Vorbis at full precision instead of stock's low-accuracy decoder (about 40 dB better in emulation)."},
    {id: "g:gapless", patch: "patches/gapless/", title: "Faster track changes", on: true,
     note: "At the end of a FLAC track the decoder stays loaded for the next FLAC file: about 11.4 ms of system work instead of 20.5 ms in emulation. Other formats reload as stock does. Not sample-exact gapless."},
    {id: "opus", patch: "patches/opus_swap/", title: "Opus playback", tag: "replaces WMA",
     note: "Plays .opus files; WMA files stop playing. No Opus tags or cover art. Adds 277 KB of decoder data to the download when built."},
    {id: "g:clock", patch: "patches/clock_v1/", title: "Lower decoder clocks", on: true,
     note: "MP3, WMA, AAC, WAV, FLAC and lower-tier Vorbis run at lower clocks. APE, ALAC, DSD and top-tier Vorbis keep stock clocks, at or above Rockchip's own figures."},
    {id: "g:dac", patch: "patches/dac_fix/", title: "DAC error-counter fix", on: true,
     note: "Two passing I2C glitches no longer freeze volume and DAC control for the session."},
  ]},
  {heading: "Library", items: [
    {id: "g:sort", patch: "patches/sort_keys/", title: "Natural sort", on: true,
     note: "Ignores case, accents and a leading \u201cThe\u201d, and puts 2 before 10."},
  ]},
  {heading: "Screen", items: [
    {id: "theater", patch: "patches/theater/", title: "Theater mode", tag: "experimental", excludes: ["bt", "lock"],
     note: "The player background takes its colour from the album art (see section 2)."},
    {id: "lock", patch: "patches/ui_features/lockscreen_build/lockscreen_build.md", title: "Lock-screen track info", tag: "experimental", excludes: ["theater"],
     note: "Shows the title and elapsed / total time while locked."},
    {id: "title", patch: "patches/theater/text/", title: "Safer track titles", tag: "experimental",
     note: "Bounds the player's title copy so very long or very short titles cannot overrun."},
    {id: "cemark", patch: "patches/theme_editor/", title: "CE splash mark",
     note: "A small CE mark on both boot screens."},
    {id: "playlists", patch: "patches/m3u/", title: "M3U playlists", only: "all",
     note: "Select an .m3u file in the browser to play it. Only in All CE features, which composes it with the lock screen."},
  ]},
  {heading: "Controls and power", items: [
    {id: "bt", patch: "patches/ui_features/", title: "Bluetooth shortcut", tag: "experimental", excludes: ["theater"],
     note: "Long-press Power to turn Bluetooth on or off. May pause up to 5 s if Bluetooth does not answer."},
    {id: "g:wheel", patch: "patches/power/", title: "Fewer wheel wake-ups", on: true,
     note: "The wheel timer runs every 1,000 µs instead of 400 µs."},
  ]},
];

function renderFeatures() {
  const root = $("feature-list");
  const known = new Set(PATCH_GROUPS.map(g => "g:" + g.id));
  for (const group of FEATURES) {
    const set = document.createElement("fieldset");
    set.className = "feature-group";
    const legend = document.createElement("legend");
    legend.textContent = group.heading;
    set.append(legend);
    for (const item of group.items) {
      if (item.id.startsWith("g:") && !known.has(item.id))
        throw new Error("unknown framework group " + item.id);
      const label = document.createElement("label");
      label.className = "feature";
      const box = document.createElement("input");
      box.type = "checkbox";
      box.dataset.feature = item.id;
      box.checked = !!item.on;
      if (item.only) { box.disabled = true; label.classList.add("only-all"); }
      const text = document.createElement("span");
      const head = document.createElement("span");
      head.className = "feature-head";
      const title = document.createElement("strong");
      title.textContent = item.title;
      head.append(title);
      if (item.tag) {
        const tag = document.createElement("span");
        tag.className = "badge";
        tag.textContent = item.tag;
        head.append(tag);
      }
      text.append(head);
      const note = document.createElement("span");
      note.className = "note";
      note.textContent = item.note;
      if (item.patch) {
        // The feature's source, in this site's repository (repo.mjs)
        const source = document.createElement("a");
        source.className = "feature-source";
        source.href = githubUrl(repoFromLocation(window.location), item.patch);
        source.dataset.repoPath = item.patch;
        source.textContent = "Source";
        head.append(source);
      }
      const why = document.createElement("span");
      why.className = "note why";
      why.hidden = true;
      text.append(note, why);
      label.append(box, text);
      set.append(label);
      box.addEventListener("change", applyExclusions);
    }
    root.append(set);
  }
  document.querySelectorAll("input[name=build-base]").forEach(radio =>
    radio.addEventListener("change", applyMode));
  applyMode();
}

const featureBox = id => document.querySelector(`#feature-list input[data-feature="${id}"]`);
const isOn = id => featureBox(id)?.checked && !featureBox(id).disabled;
const mode = () => document.querySelector("input[name=build-base]:checked").value;

// A picked build has one gap tail: theater excludes the Bluetooth
// shortcut and the lock screen (combineWithTheater). Disable what the
// current ticks exclude and say why.
function applyExclusions() {
  const items = FEATURES.flatMap(g => g.items);
  for (const item of items) {
    if (item.only) continue;
    const box = featureBox(item.id);
    const blockers = items.filter(other => other.excludes?.includes(item.id) &&
                                           featureBox(other.id).checked);
    const why = box.closest("label").querySelector(".why");
    box.disabled = blockers.length > 0;
    if (box.disabled) box.checked = false;
    why.hidden = !box.disabled;
    why.textContent = box.disabled ? "Not with " + blockers.map(b => b.title).join(" or ") +
      " in a picked build; All CE features has both." : "";
  }
}

function applyMode() {
  const custom = mode() === "custom";
  $("feature-list").hidden = !custom;
  $("look-options").hidden = !custom;
  if (custom) applyExclusions();
}

function renderEqSlots() {
  const root = $("eq-slots");
  for (const [n, name] of Object.entries(SLOTS)) {
    const label = document.createElement("label");
    label.htmlFor = "eq-slot-" + n;
    label.textContent = n + ". " + name;
    const text = document.createElement("textarea");
    text.id = "eq-slot-" + n;
    text.rows = 2;
    text.placeholder = "Empty: stock curve. Paste GraphicEQ: 20 -0.2; 21 -0.2; ... or 31 dB values";
    const file = document.createElement("input");
    file.type = "file";
    file.accept = ".txt,text/plain";
    file.setAttribute("aria-label", "Load an AutoEQ file for " + name);
    file.addEventListener("change", async () => {
      if (file.files[0]) text.value = await file.files[0].text();
    });
    root.append(label, text, file);
  }
}

// Fitted EQ patches for every filled slot, plus a summary for the status.
function eqSelection(bytes) {
  const slots = {}, notes = [];
  let R = null;
  for (const [n, name] of Object.entries(SLOTS)) {
    const text = $("eq-slot-" + n).value.trim();
    if (!text) continue;
    R = R || bandTable(bytes);
    const result = fit(parseCurve(text), R);
    slots[n] = result.gains;
    notes.push(name + " (fit " + result.rms.toFixed(1) + " dB rms, peak " +
      (result.peak > 0 ? "+" : "") + result.peak.toFixed(1) + " dB)");
  }
  if (!notes.length) return {patches: [], note: ""};
  return {patches: slotPatches(bytes, slots), note: ", EQ presets " + notes.join(", ")};
}

function renderChoices(id, choices) {
  const select = $(id);
  for (const choice of choices) {
    const option = document.createElement("option");
    option.value = choice.id;
    option.textContent = choice.label;
    select.append(option);
  }
}

function renderPresets() {
  const root = $("preset-buttons");
  for (const preset of PRESETS) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "button ghost";
    button.textContent = preset.name;
    button.addEventListener("click", () => {
      if (window.dapNeoStudio.applyThemeData(
            JSON.parse(JSON.stringify(preset.config)))) {
        $("opt-theme").checked = true;
        setStatus("Preset " + preset.name + " loaded into the editor. " +
          "Build when ready.", "good");
      } else {
        setStatus("Preset " + preset.name +
          " was rejected by the editor checks; see the editor status.", "bad");
      }
    });
    root.append(button);
  }
}

// The Opus decoder data (277 KB) loads only when a build needs it.
async function opusData() {
  const {OPUS_DATA} = await import("./builder-opus-data.mjs");
  return OPUS_DATA;
}

async function build() {
  const studio = window.dapNeoStudio;
  const firmware = studio?.firmware();
  if (!firmware) {
    setStatus("Load the stock DP3_V137.img in section 1 first (from the repository " +
      "or your own copy); the build refuses any other image.", "bad");
    return;
  }
  let eq;
  try {
    eq = eqSelection(firmware.bytes);
  } catch (err) {
    setStatus("Build refused: EQ preset: " + err.message, "bad");
    return;
  }
  const filterId = $("opt-dac-filter").value;
  const autoOffId = $("opt-bt-auto-off").value;
  // Byte-patch settings that apply to either kind of build.
  const filterPatches = [...dacFilterPatches(filterId), ...btAutoOffPatches(autoOffId), ...eq.patches];
  const filterNote =
    (filterId !== "stock" ? ", DAC filter " + DAC_FILTERS.find(f => f.id === filterId).label : "") +
    (autoOffId !== "stock" ? ", Bluetooth auto-off " + autoOffId : "") + eq.note;
  const button = $("build-button");
  button.disabled = true;
  setStatus("Building locally. Checking every expected byte, " +
    "then stamping the date and recomputing the CRC.");
  // Yield so the browser can paint the status before the CRC pass.
  await new Promise(resolve => setTimeout(resolve, 20));
  try {
    if (mode() === "all") {
      const result = await buildFirmware(firmware.bytes,
        {groups: new Set(PATCH_GROUPS.map(g => g.id)),
         patchGroups: PATCH_GROUPS, vorbis: VORBIS75, opus: await opusData(),
         opusPatches: OPUS_PATCHES,
         themeConfig: {version: 1, runs: FULL_THEME_RUNS},
         tailPayload: await fullTailPayload(),
         extraPatches: [...FULL_EXTRA_PATCHES, ...filterPatches],
         growths: await fullGrowthPayloads()},
        sha256);
      download("DP3_V137_CE_full.img", result.bytes);
      offerToInstaller("DP3_V137_CE_full.img", result);
      setStatus("Built DP3_V137_CE_full.img with all CE features. SHA-256 " + result.sha256 +
        (filterPatches.length
          ? " (the Standard image " + FULL_IMAGE_SHA256.slice(0, 12) + "… plus" + filterNote.slice(1) + "). "
          : ", identical to the Standard image. ") +
        "It is 7,168 bytes longer than stock; no longer-than-stock image has been " +
        "installed yet. It is now selected in Install CE at the top of the page; " +
        "installing it is at your own risk.", "good");
      return;
    }
    const groups = new Set(PATCH_GROUPS.filter(g => isOn("g:" + g.id) || g.id === "fixture").map(g => g.id));
    const opus = isOn("opus") ? await opusData() : null;
    const btTail = isOn("bt") ? await bluetoothTail(hexToBytes(BT_PAYLOAD.hex), sha256) : null;
    const lock = isOn("lock") ? await lockscreenPayload(hexToBytes(LOCK_PAYLOAD.hex), sha256) : null;
    const theater = isOn("theater") ? await theaterTail(hexToBytes(THEATER_TAIL.hex), sha256) : null;
    const tailPayload = combineWithTheater(theater, combineTails(null, btTail), !!lock);
    const titleFix = isOn("title");
    const extraPatches = [...(btTail ? [BT_PATCH] : []), ...(lock ? [LOCK_PATCH] : []),
                          ...(titleFix ? TITLE_PATCHES : []),
                          ...(theater ? THEATER_PATCHES : []), ...filterPatches];
    const result = await buildFirmware(firmware.bytes,
      {groups, patchGroups: PATCH_GROUPS, vorbis: isOn("vorbis") ? VORBIS75 : null,
       opus, opusPatches: OPUS_PATCHES,
       themeConfig: $("opt-theme").checked ? studio.config() : null,
       ceMarkRuns: isOn("cemark") ? CE_MARK_RUNS : null,
       tailPayload, extraPatches, module31Payload: lock},
      sha256);
    download("DP3_V137_CE_builder.img", result.bytes);
    offerToInstaller("DP3_V137_CE_builder.img", result);
    const picked = FEATURES.flatMap(g => g.items).filter(i => !i.only && isOn(i.id)).map(i => i.title);
    setStatus("Built DP3_V137_CE_builder.img. SHA-256 " + result.sha256 + ". " +
      (picked.length ? picked.join(", ") : "No optional features") + filterNote +
      (result.theme ? ", theme (" + result.theme.bytes_changed + " bytes)" : "") +
      (result.bytesChanged === null ? ". The image contains a module extension. " :
        ". " + result.bytesChanged + " bytes differ from stock. ") +
      "It is now selected in Install CE at the top of the page; installing it is at your own risk.", "good");
  } catch (err) {
    setStatus("Build refused: " + err.message, "bad");
  } finally {
    button.disabled = false;
  }
}

renderFeatures();
renderEqSlots();
renderChoices("opt-dac-filter", DAC_FILTERS);
renderChoices("opt-bt-auto-off", BT_AUTO_OFF);
renderPresets();
$("build-button").addEventListener("click", build);
