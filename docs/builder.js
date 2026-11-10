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
import {BT_PATCH, LOCK_PATCH, PLAYLIST_PATCHES, TITLE_PATCHES, bluetoothTail, lockscreenPayload, playlistPayloads, combineTails, theaterTail, combineWithTheater} from "./builder-experimental.mjs";
import {FULL_EXTRA_PATCHES, FULL_TAIL, FULL_GROWTHS, FULL_THEME_RUNS, FULL_IMAGE_SHA256} from "./builder-full.mjs";
import {sha256} from "./theme-core.mjs";
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

function renderToggles() {
  const root = $("feature-toggles");
  // Put playback first and keep the framework's mandatory no-op fixture
  // out of the user-facing settings. The engine always applies it.
  const groups = PATCH_GROUPS.filter(group => group.id !== "fixture");
  groups.sort((a, b) => (a.id === "gapless" ? -1 : 0) -
                        (b.id === "gapless" ? -1 : 0));
  for (const group of groups) {
    const label = document.createElement("label");
    label.className = "checkbox";
    const box = document.createElement("input");
    box.type = "checkbox";
    box.dataset.group = group.id;
    box.checked = true;
    const text = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = group.id === "gapless" ? "Gapless playback (fast path)" : group.label;
    const blurb = document.createElement("span");
    blurb.className = "note";
    blurb.textContent = group.id === "gapless"
      ? "Enabled by default. Shortens same-codec transitions; uninterrupted playback is not guaranteed. The system-side transition still needs hardware validation."
      : group.blurb;
    text.append(title, document.createElement("br"), blurb);
    label.append(box, text);
    root.append(label);
  }
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

async function build() {
  const studio = window.dapNeoStudio;
  const firmware = studio?.firmware();
  if (!firmware) {
    setStatus("Load your stock DP3_V137.img in section 1 first; " +
      "the build refuses any other image.", "bad");
    return;
  }
  const groups = new Set();
  document.querySelectorAll("#feature-toggles input[data-group]")
    .forEach(box => { if (box.checked) groups.add(box.dataset.group); });
  const themeConfig = $("opt-theme").checked ? studio.config() : null;
  const ceMarkRuns = $("opt-ce-mark").checked ? CE_MARK_RUNS : null;
  const vorbis = $("opt-vorbis").checked ? VORBIS75 : null;
  const opusFile = $("opt-opus-data").files[0];
  const btFile = $("opt-bt-data").files[0];
  const overlayFile = $("opt-playlist-overlay").files[0];
  const resolverFile = $("opt-playlist-resolver").files[0];
  const lockFile = $("opt-lock-data").files[0];
  let eq;
  try {
    eq = eqSelection(firmware.bytes);
  } catch (err) {
    setStatus("Build refused: EQ preset: " + err.message, "bad");
    return;
  }
  const filterId = $("opt-dac-filter").value;
  const autoOffId = $("opt-bt-auto-off").value;
  // The build options that only add byte patches: DAC filter, Bluetooth
  // auto-off and EQ presets. They apply to the everything build too.
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
    const opus = opusFile ? JSON.parse(await opusFile.text()) : null;
    if (opusFile && (!opus || !Array.isArray(opus.ranges)))
      throw new Error("Opus data must contain a ranges array");
    if ($("opt-everything").checked) {
      if (!opus)
        throw new Error("the everything build includes Opus playback; " +
          "select the locally generated Opus data file above first");
      const result = await buildFirmware(firmware.bytes,
        {groups: new Set(PATCH_GROUPS.map(g => g.id)),
         patchGroups: PATCH_GROUPS, vorbis: VORBIS75, opus,
         opusPatches: OPUS_PATCHES,
         themeConfig: {version: 1, runs: FULL_THEME_RUNS},
         tailPayload: await fullTailPayload(),
         extraPatches: [...FULL_EXTRA_PATCHES, ...filterPatches],
         growths: await fullGrowthPayloads()},
        sha256);
      download("DP3_V137_CE_full.img", result.bytes);
      setStatus("Built DP3_V137_CE_full.img (the everything build). " +
        "SHA-256 " + result.sha256 + (filterPatches.length
          ? " (the pinned " + FULL_IMAGE_SHA256.slice(0, 12) + "… plus" + filterNote.slice(1) + "). "
          : " (pinned: " + FULL_IMAGE_SHA256 + "). ") +
        result.patchesApplied + " byte patches, both decoder transplants, " +
        "the merged tail, two module extensions and the merged theme " +
        "runs. The image is 6,962 bytes longer than stock because the " +
        "ebook reader is kept; whether the update slots accept the " +
        "longer image is unverified. Nothing was flashed; install " +
        "through the usual update flow at your own risk.", "good");
      return;
    }
    if (!!overlayFile !== !!resolverFile)
      throw new Error("Select both playlist payload files");
    if (lockFile && overlayFile) throw new Error("Select only one module 31 extension");
    const playlist = overlayFile ? await playlistPayloads(
      new Uint8Array(await overlayFile.arrayBuffer()),
      new Uint8Array(await resolverFile.arrayBuffer()), sha256) : null;
    const btTail = btFile ? await bluetoothTail(new Uint8Array(await btFile.arrayBuffer()), sha256) : null;
    const lock = lockFile ? await lockscreenPayload(new Uint8Array(await lockFile.arrayBuffer()), sha256) : null;
    const theater = $("opt-theater").checked
      ? await theaterTail(hexToBytes(THEATER_TAIL.hex), sha256) : null;
    const tailPayload = combineWithTheater(
      theater, combineTails(playlist?.resolver, btTail), !!lock);
    const titleFix = $("opt-title-fix").checked;
    const extraPatches = [...(btFile ? [BT_PATCH] : []), ...(playlist ? PLAYLIST_PATCHES : []),
                          ...(lock ? [LOCK_PATCH] : []), ...(titleFix ? TITLE_PATCHES : []),
                          ...(theater ? THEATER_PATCHES : []), ...filterPatches];
    const result = await buildFirmware(firmware.bytes,
      {groups, patchGroups: PATCH_GROUPS, vorbis, opus, opusPatches: OPUS_PATCHES,
       themeConfig, ceMarkRuns, tailPayload, extraPatches, module31Payload: playlist?.overlay ?? lock},
      sha256);
    download("DP3_V137_CE_builder.img", result.bytes);
    setStatus("Built DP3_V137_CE_builder.img. SHA-256 " + result.sha256 +
      ". " + result.patchesApplied + " byte patches" +
      (result.vorbis ? ", vorbis75 transplant" : "") +
      (opus ? ", Opus replaces WMA" : "") +
      (btFile ? ", Bluetooth shortcut" : "") +
      (playlist ? ", M3U playlists and lock-screen information" : "") +
      (lock ? ", lock-screen information" : "") +
      (titleFix ? ", safer track titles" : "") +
      (theater ? ", Theater mode" : "") + filterNote +
      (result.theme ? ", theme (" + result.theme.bytes_changed +
        " bytes)" : "") +
      (result.bytesChanged === null ? ". Image contains a module extension. " :
        ". " + result.bytesChanged + " bytes differ from stock. ") +
      "Nothing was flashed; install through the usual update flow " +
      "at your own risk.", "good");
  } catch (err) {
    setStatus("Build refused: " + err.message, "bad");
  } finally {
    button.disabled = false;
  }
}

renderToggles();
renderEqSlots();
renderChoices("opt-dac-filter", DAC_FILTERS);
renderChoices("opt-bt-auto-off", BT_AUTO_OFF);
renderPresets();
$("build-button").addEventListener("click", build);
