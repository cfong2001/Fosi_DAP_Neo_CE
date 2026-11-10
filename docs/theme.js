import {
  STOCK_SHA256, ROLES, GUARD_WORDS, parseFirmware, sha256,
  frequencies, rgbaPixels, rgb565, rgb888, asWord, wordHex,
  validateTheme, exportConfig
} from "./theme-core.mjs";
import {repoFromLocation, rawUrl} from "./repo.mjs";

const $ = id => document.getElementById(id);
const defaults = Object.freeze({
  background: "#141821",
  text: "#F5F7FA",
  highlight: "#38BDF8",
  icons: "#DCECF8",
  progress_bar: "#38BDF8"
});
const roleLabels = {
  background: "Background", text: "Text", highlight: "Selection",
  icons: "Icons", progress_bar: "Progress"
};
const state = {
  palette: {...defaults}, firmware: null, selected: null,
  rules: new Map(), page: 0, filter: ""
};
const perPage = 36;
function status(target, message, kind = "") {
  const node = $(target);
  node.textContent = message;
  node.className = "status" + (kind ? " " + kind : "");
}
function safe(value) { return String(value).replace(/[&<>"']/g, ch => ({
  "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
})[ch]); }
function download(name, content) {
  const url = URL.createObjectURL(new Blob([content], {type:"application/json"}));
  const a = document.createElement("a"); a.href = url; a.download = name;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function populatePalette() {
  const root = $("palette");
  root.replaceChildren();
  for (const role of ROLES) {
    const item = document.createElement("label");
    item.className = "color-field";
    const name = document.createElement("span");
    name.textContent = roleLabels[role];
    const output = document.createElement("output"); output.textContent = state.palette[role];
    const field = document.createElement("input");
    field.type = "color"; field.value = state.palette[role];
    field.setAttribute("aria-label", roleLabels[role] + " hex color");
    field.addEventListener("input", () => {
      state.palette[role] = field.value;
      output.textContent = field.value.toUpperCase();
      applyPalette();
      renderAsset();
    });
    item.append(name, output, field); root.append(item);
  }
  applyPalette();
}
function applyPalette() {
  renderAsset();
}
function pixelsToCanvas(canvas, asset, pixels) {
  canvas.width = asset.width; canvas.height = asset.height;
  const ctx = canvas.getContext("2d", {alpha:false});
  ctx.putImageData(new ImageData(pixels, asset.width, asset.height), 0, 0);
}
function previewReplacements(asset, includePending) {
  const replacements = new Map();
  for (const rule of state.rules.values()) {
    if (rule.id === asset.id) replacements.set(asWord(rule.source), rgb565(state.palette[rule.role]));
  }
  if (includePending) {
    try {
      const source = asWord($("source-word").value.trim());
      const role = $("resource-role").value;
      if (!GUARD_WORDS.has(source) && ROLES.includes(role)) {
        replacements.set(source, rgb565(state.palette[role]));
      }
    } catch { /* Invalid exploratory input changes nothing. */ }
  }
  return replacements;
}
function renderAsset() {
  const selected = state.selected;
  if (!state.firmware || selected === null) return;
  const asset = state.firmware.entries[selected];
  if (!asset) return;
  const source = frequencies(state.firmware, asset);
  $("asset-title").textContent = "Asset #" + asset.id + " · " + asset.label;
  $("asset-metadata").textContent =
    asset.width + "×" + asset.height + " px · x=" + asset.x + " y=" + asset.y +
    " · offset 0x" + asset.data_offset.toString(16).toUpperCase() +
    " · " + source.length + " distinct RGB565 colors";
  pixelsToCanvas($("original-resource"), asset, rgbaPixels(state.firmware, asset));
  pixelsToCanvas($("modified-resource"), asset,
    rgbaPixels(state.firmware, asset, previewReplacements(asset, true)));
  const w = $("source-word").value.trim();
  let count = 0;
  try {
    const target = asWord(w);
    count = source.find(entry => entry.word === target)?.count || 0;
    $("word-count").textContent = count + " pixels have the exact RGB565 word " + wordHex(target) +
      (GUARD_WORDS.has(target) ? ". Reserved candidate: selection blocked." : ".");
  } catch {
    $("word-count").textContent = "Enter an exact 16-bit source color, for example 0xA210.";
  }
  const overlay = $("asset-overlay");
  overlay.replaceChildren();
  if ($("project-asset").checked) {
    const canvas = document.createElement("canvas");
    pixelsToCanvas(canvas, asset, rgbaPixels(state.firmware, asset, previewReplacements(asset, false)));
    canvas.style.left = asset.x + "px";
    canvas.style.top = asset.y + "px";
    overlay.append(canvas);
    overlay.classList.add("active");
  } else overlay.classList.remove("active");
}
function selectAsset(id) {
  if (!state.firmware) return;
  state.selected = id;
  $("asset-detail").hidden = false;
  const asset = state.firmware.entries[id];
  const topColors = frequencies(state.firmware, asset).slice(0, 30);
  const swatches = $("swatch-source"); swatches.replaceChildren();
  for (const entry of topColors) {
    const option = document.createElement("option");
    option.value = entry.hex;
    option.textContent = entry.hex + " · " + entry.count + " px";
    swatches.append(option);
  }
  const safeFirst = topColors.find(item => !GUARD_WORDS.has(item.word)) || topColors[0];
  $("source-word").value = safeFirst ? safeFirst.hex : "0xFFFF";
  const assigned = [...state.rules.values()].find(rule => rule.id === id);
  if (assigned) {
    $("source-word").value = assigned.source;
    $("resource-role").value = assigned.role;
  }
  swatches.value = $("source-word").value;
  renderGallery(); renderAsset();
}
function renderGallery() {
  const root = $("gallery");
  root.replaceChildren();
  if (!state.firmware) {
    const p = document.createElement("p"); p.className = "note";
    p.textContent = "Load a verified V137 image to browse its resources.";
    root.append(p); return;
  }
  const q = state.filter.toLowerCase();
  const items = state.firmware.entries.filter(a =>
    String(a.id).includes(q) || a.label.toLowerCase().includes(q) ||
    (a.width + "x" + a.height).includes(q));
  const totalPages = Math.max(1, Math.ceil(items.length / perPage));
  state.page = Math.min(state.page, totalPages - 1);
  const shown = items.slice(state.page * perPage, (state.page + 1) * perPage);
  for (const asset of shown) {
    const button = document.createElement("button");
    button.type = "button"; button.className = "asset-entry";
    if (asset.id === state.selected) button.classList.add("selected");
    button.setAttribute("aria-label", "Resource " + asset.id + ", " + asset.label);
    const thumb = document.createElement("canvas");
    // Canvas output is downsampled here; never reconstruct the bitmap as CSS.
    thumb.width = 76; thumb.height = 46;
    const img = document.createElement("canvas");
    pixelsToCanvas(img, asset, rgbaPixels(state.firmware, asset));
    const ctx = thumb.getContext("2d", {alpha:false});
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(img, 0, 0, thumb.width, thumb.height);
    thumb.style.maxWidth = "100%"; thumb.style.height = "44px";
    thumb.style.objectFit = "contain";
    const label = document.createElement("small");
    label.textContent = "#" + asset.id + " · " + asset.width + "×" + asset.height;
    button.append(thumb, label);
    button.addEventListener("click", () => selectAsset(asset.id));
    root.append(button);
  }
  const controls = document.createElement("div");
  controls.className = "button-row"; controls.style.gridColumn = "1 / -1";
  const prev = document.createElement("button"), next = document.createElement("button");
  prev.className = "button"; next.className = "button";
  prev.textContent = "‹ Previous"; next.textContent = "Next ›";
  prev.disabled = state.page <= 0; next.disabled = state.page + 1 >= totalPages;
  prev.addEventListener("click", () => {state.page--; renderGallery();});
  next.addEventListener("click", () => {state.page++; renderGallery();});
  const counter = document.createElement("span"); counter.className = "note";
  counter.textContent = "Page " + (state.page + 1) + "/" + totalPages;
  controls.append(prev, counter, next); root.append(controls);
}
function summarizeRules() {
  const root = $("rules"); root.replaceChildren();
  const items = [...state.rules.values()].sort((a,b) => a.id - b.id || asWord(a.source) - asWord(b.source));
  $("rule-count").textContent = items.length;
  if (!items.length) {
    const p = document.createElement("p"); p.className="note";
    p.textContent="No resource edits selected."; root.append(p); return;
  }
  for (const rule of items) {
    const row = document.createElement("div"); row.className = "rule";
    const label = document.createElement("span");
    label.textContent = "#" + rule.id + " · " + rule.source +
      " → " + roleLabels[rule.role] + " (" + rule.expected_count + " px)";
    const remove = document.createElement("button");
    remove.className = "button danger"; remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      state.rules.delete(rule.id + ":" + asWord(rule.source));
      summarizeRules(); renderAsset();
      status("editor-status", "Removed exact resource rule.", "good");
    });
    row.append(label, remove); root.append(row);
  }
}
function addRule() {
  if (!state.firmware || state.selected === null) {
    status("editor-status", "Load your stock firmware and select an asset first.", "bad");
    return;
  }
  try {
    const asset = state.firmware.entries[state.selected];
    const source = asWord($("source-word").value.trim());
    if (GUARD_WORDS.has(source)) throw new Error("This color is a possible transparency key; patching is blocked.");
    const entry = frequencies(state.firmware, asset).find(item => item.word === source);
    if (!entry || !entry.count) throw new Error("The source word is absent from this asset.");
    const role = $("resource-role").value;
    if (!ROLES.includes(role)) throw new Error("Unknown theme role");
    const rule = {id: asset.id, role, source: wordHex(source), expected_count: entry.count};
    state.rules.set(asset.id + ":" + source, rule);
    summarizeRules(); renderAsset();
    status("editor-status", "Rule pinned to " + entry.count + " verified source pixels in asset #" + asset.id + ".", "good");
  } catch (err) { status("editor-status", err.message, "bad"); }
}
function config() { return exportConfig(state.palette, state.rules.values()); }
function exportTheme() {
  try {
    const cfg = config();
    validateTheme(cfg, state.firmware?.entries || Array.from({length:456}));
    download("dap-neo-theme.json", JSON.stringify(cfg, null, 2) + "\n");
    status("editor-status", "Saved JSON locally. " + cfg.resources.length +
      " pinned resource rule(s). Firmware binary was not modified.", "good");
  } catch (err) { status("editor-status", err.message, "bad"); }
}
function applyThemeData(data) {
  try {
    validateTheme(data, state.firmware?.entries || Array.from({length:456}));
    if (data.literal_sites.length)
      throw new Error("Web UI doesn't approve raw module literals. Remove literal_sites or review offline.");
    if (state.firmware) {
      for (const rule of data.resources) {
        const actual = frequencies(state.firmware, state.firmware.entries[rule.id])
          .find(item => item.word === asWord(rule.source))?.count || 0;
        if (actual !== rule.expected_count)
          throw new Error("Asset #" + rule.id + " source count mismatch: expected " +
                          rule.expected_count + ", actual " + actual);
      }
    }
    state.palette = {...defaults, ...data.palette};
    state.rules = new Map(data.resources.map(rule =>
      [rule.id + ":" + asWord(rule.source), {...rule,source:wordHex(asWord(rule.source))}]));
    populatePalette(); summarizeRules(); renderAsset();
    status("editor-status", "Loaded " + state.rules.size + " pinned resource rules. " +
       (state.firmware ? "Pixel counts match your stock firmware." : "Load stock firmware to verify pixel counts."), "good");
    return true;
  } catch (err) { status("editor-status", "Theme rejected: " + err.message, "bad"); return false; }
}
async function importTheme(file) {
  if (!file) return;
  try {
    applyThemeData(JSON.parse(await file.text()));
  } catch (err) { status("editor-status", "Theme rejected: " + err.message, "bad"); }
}
async function openFirmware(file) {
  if (!file) return;
  // Preserve imported theme rules while inspecting firmware. Their source
  // pixel counts must match the new stock image before exposing the catalog.
  const existingRules = [...state.rules.values()];
  state.firmware = null; state.selected = null;
  summarizeRules(); renderGallery();
  $("asset-detail").hidden = true;
  $("asset-count").textContent = "Checking…";
  status("firmware-status", "Reading and verifying SHA-256 locally…");
  // Yield so the browser can paint the status before hashing.
  await new Promise(resolve => setTimeout(resolve, 20));
  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    const digest = await sha256(bytes);
    if (digest !== STOCK_SHA256)
      throw new Error("Unexpected image SHA-256 (" + digest.slice(0,16) +
                      "…). Only unmodified DP3_V137.img is accepted.");
    const parsed = parseFirmware(bytes);
    for (const rule of existingRules) {
      const asset = parsed.entries[rule.id];
      const actual = asset && frequencies(parsed, asset)
        .find(entry => entry.word === asWord(rule.source))?.count || 0;
      if (actual !== rule.expected_count) {
        throw new Error("Imported theme has an incorrect source-pixel count for #" +
                        rule.id + " (" + actual + ", expected " + rule.expected_count + ")");
      }
    }
    state.firmware = parsed;
    $("asset-count").textContent = state.firmware.entries.length + " / 456";
    status("firmware-status", "Verified stock V137 SHA-256. " +
      state.firmware.entries.length + " RGB565 assets mapped locally.", "good");
    state.page = 0; renderGallery(); selectAsset(6);
    window.dispatchEvent(new CustomEvent("stock-firmware"));
    status("editor-status", "Choose a source word and a theme role to define a binary patch.", "good");
  } catch (err) {
    state.firmware = null; $("asset-count").textContent = "0 / 456";
    status("firmware-status", "Firmware rejected: " + err.message, "bad");
  }
}
// The stock image is public in the repository; fetch it instead of
// asking for a local file. openFirmware still checks its SHA-256.
async function fetchStock() {
  const button = $("firmware-fetch");
  button.disabled = true;
  status("firmware-status", "Downloading DP3_V137.img from the repository…");
  try {
    const response = await fetch(rawUrl(repoFromLocation(window.location), "DP3_V137.img"));
    if (!response.ok) throw new Error("GitHub returned " + response.status);
    await openFirmware(new Blob([await response.arrayBuffer()]));
  } catch (err) {
    status("firmware-status", "Could not download the stock image: " + err.message +
      ". Select your own copy instead.", "bad");
  } finally {
    button.disabled = false;
  }
}
function init() {
  populatePalette(); summarizeRules(); renderGallery();
  $("firmware-input").addEventListener("change", ev => openFirmware(ev.target.files[0]));
  $("firmware-fetch").addEventListener("click", fetchStock);
  $("upload-theme").addEventListener("click", () => $("theme-input").click());
  $("theme-input").addEventListener("change", ev => importTheme(ev.target.files[0]));
  $("download-theme").addEventListener("click", exportTheme);
  $("add-rule").addEventListener("click", addRule);
  $("filter-assets").addEventListener("input", ev => {
    state.filter = ev.target.value.trim(); state.page = 0; renderGallery();
  });
  $("swatch-source").addEventListener("change", ev => {
    $("source-word").value = ev.target.value; renderAsset();
  });
  $("source-word").addEventListener("input", renderAsset);
  $("resource-role").addEventListener("change", renderAsset);
  $("project-asset").addEventListener("change", renderAsset);
}
// The CE builder (builder.js) builds from the studio's live state:
// the verified firmware from section 1 and the theme config the
// editor currently holds. Preset schemes load through the same
// checked path as an imported theme.json.
window.dapNeoStudio = {
  applyThemeData,
  config,
  firmware: () => state.firmware,
  rulesCount: () => state.rules.size,
};
init();
