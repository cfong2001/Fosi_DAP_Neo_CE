// Section 2 of index.html: stock and CE screens side by side, from real
// firmware pixels (see sim-core.mjs for what is exact and what is drawn).
//
// Each image's resource section (about 4 MB) is fetched from the
// repository with an HTTP range request and refused unless its SHA-256
// matches SECTIONS in sim-data.mjs. If the stock image is already loaded
// in section 1, its section is taken from there instead.
import {SECTIONS} from "./sim-data.mjs";
import {
  WIDTH, HEIGHT, ART, BADGE, parseResourceSection, resourceSectionOf, fill, draw, blit,
  blitCover, paintPlaceholder, paintBadge, paintPlayer, paintProgress, groundFor, theaterGround,
  rgbaToWords, toRGBA, sampleCover, rgb888
} from "./sim-core.mjs";
import {sha256} from "./theme-core.mjs";
import {repoFromLocation, rawUrl} from "./repo.mjs";

const $ = id => document.getElementById(id);
const repo = repoFromLocation(window.location);
const tracks = [["Ember Skyline", "Demonstration Ensemble", 228, "FLAC"],
                ["Low Tide", "Demonstration Ensemble", 251, "MP3"],
                ["Prism", "Demonstration Ensemble", 199, "OPUS"]];
const SAMPLE = sampleCover();

const state = {
  res: {stock: null, ce: null}, loading: null,
  tab: "playing", playing: true, page: 0, light: false,
  theater: true, noArt: false, art: SAMPLE, artName: "sample cover",
  track: 0, position: 72,
};

function status(message, kind = "") {
  const el = $("sim-status");
  el.textContent = message;
  el.className = "status" + (kind ? " " + kind : "");
}

async function fetchSection(name) {
  const pin = SECTIONS[name];
  const url = rawUrl(repo, pin.file);
  const end = pin.offset + pin.length - 1;
  const response = await fetch(url, {headers: {Range: "bytes=" + pin.offset + "-" + end}});
  if (!response.ok) throw new Error("GitHub returned " + response.status + " for " + pin.file);
  let bytes = new Uint8Array(await response.arrayBuffer());
  // A server that ignores the range sends the whole image.
  if (response.status === 200) bytes = bytes.subarray(pin.offset, pin.offset + pin.length);
  if (bytes.length !== pin.length || await sha256(bytes) !== pin.sha256)
    throw new Error(pin.file + " resources do not match their pinned SHA-256; refused");
  return parseResourceSection(bytes);
}

function stockFromStudio() {
  const fw = window.dapNeoStudio?.firmware?.();
  return fw ? parseResourceSection(resourceSectionOf(fw.bytes)) : null;
}

async function load() {
  if (state.loading || (state.res.stock && state.res.ce)) return state.loading;
  $("sim-retry").hidden = true;
  state.loading = (async () => {
    try {
      state.res.stock ??= stockFromStudio();
      const need = ["stock", "ce"].filter(n => !state.res[n]);
      const mb = (need.reduce((t, n) => t + SECTIONS[n].length, 0) / 1e6).toFixed(1);
      if (need.length) status("Loading firmware resources (" + mb + " MB) from " + repo + "…");
      const got = await Promise.all(need.map(fetchSection));
      need.forEach((n, i) => { state.res[n] = got[i]; });
      status("Showing real pixels from the stock V137 image and the CE standard image " +
        "(resource sections SHA-256 verified).", "good");
      render();
    } catch (err) {
      status("Could not load the firmware screens: " + err.message, "bad");
      $("sim-retry").hidden = false;
    } finally {
      state.loading = null;
    }
  })();
  return state.loading;
}

const clock = s => Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");

function groundOf(side) {
  if (side === "ce" && state.theater && !state.noArt)
    return theaterGround(state.art, ART.size, ART.size, state.light);
  return groundFor(state.light);
}

function frame(side) {
  const res = state.res[side];
  const fb = new Uint16Array(WIDTH * HEIGHT);
  const offset = state.light ? 166 : 0;
  if (state.tab === "splash") {
    draw(fb, res, 127 + offset, 0, 0);
  } else if (state.tab === "nomedia") {
    draw(fb, res, 138 + offset, 0, 0);
  } else {
    const ground = groundOf(side);
    fill(fb, 0, 0, WIDTH - 1, HEIGHT - 1, ground);
    if (side === "ce") {
      // CE: rounded, contrast-boosted cover or the outline-and-note tile,
      // then the format badge (palette cell 0, taken as the theme ground)
      if (state.noArt) paintPlaceholder(fb, state.light ? 0x0000 : 0xFFFF);
      else blitCover(fb, state.art, ART.size, ART.x, ART.y, ground);
      paintBadge(fb, groundFor(state.light));
    } else if (!state.noArt) blit(fb, state.art, ART.size, ART.size, ART.x, ART.y);
    paintPlayer(fb, res, side, {page: state.page, playing: state.playing,
                                light: state.light, ground});
    const length = tracks[state.track][2];
    paintProgress(fb, res, {fraction: state.position / length, light: state.light, ground});
  }
  return fb;
}

// Text and times are not resources. Stock: drawn at the README renderer's
// approximate positions. CE: the time follows typography.S (MM:SS on the
// 14-pixel line at y = 240, elapsed from x = 7, total from x = 191) and
// the badge label sits at the badge's text origin, both in Barlow
// SemiBold, the face CE's system font was redrawn from (the page cannot
// reach the image's 1-bit glyphs). Title and artist stay approximate.
const mmss = s => String(Math.min(99, Math.floor(s / 60))).padStart(2, "0") + ":" +
  String(s % 60).padStart(2, "0");

function drawText(ctx, side) {
  const [title, artist, length, codec] = tracks[state.track];
  const ce = side === "ce";
  const ink = state.light ? "#141414" : "#f0f0f0";
  ctx.fillStyle = ink; ctx.strokeStyle = ink; ctx.textBaseline = "middle";
  ctx.font = "bold 16px Arial, sans-serif"; ctx.textAlign = "center";
  ctx.fillText(title, 120, ce ? 200 : 206, 224);
  ctx.font = "13px Arial, sans-serif";
  ctx.fillText(artist, 120, ce ? 223 : 231, 224);
  if (ce) {
    ctx.font = "600 13px Barlow, Arial, sans-serif"; ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(mmss(state.position), 7, 240);
    ctx.fillText(mmss(length), 191, 240, 48);
    ctx.font = "600 12px Barlow, Arial, sans-serif";
    ctx.fillStyle = state.light ? "#000000" : "#ffffff";
    ctx.fillText(codec, BADGE.x + 4, BADGE.y + 3, BADGE.width - 8);
    return;
  }
  ctx.font = "11px Arial, sans-serif";
  ctx.textAlign = "left"; ctx.fillText(clock(state.position), 6, 257);
  ctx.textAlign = "right"; ctx.fillText("-" + clock(length - state.position), 234, 257);
  ctx.lineWidth = 1;
  if (state.noArt) {
    ctx.strokeRect(ART.x + 0.5, ART.y + 0.5, ART.size - 1, ART.size - 1);
    ctx.font = "12px Arial, sans-serif"; ctx.textAlign = "center";
    ctx.fillText("no art", 120, 108);
  }
}

function render() {
  for (const side of ["stock", "ce"]) {
    const canvas = $(side + "-canvas");
    const ctx = canvas.getContext("2d");
    if (!state.res[side]) continue;
    ctx.putImageData(new ImageData(toRGBA(frame(side)), WIDTH, HEIGHT), 0, 0);
    if (state.tab === "playing") drawText(ctx, side);
  }
  const theater = $("theater-status");
  if (state.tab === "playing" && state.res.ce) {
    theater.hidden = false;
    const ground = groundOf("ce");
    const [r, g, b] = rgb888(ground);
    theater.textContent = state.theater && !state.noArt
      ? "CE background 0x" + ground.toString(16).toUpperCase().padStart(4, "0") +
        " (" + r + ", " + g + ", " + b + ") from the " + state.artName + ", " +
        (state.light ? "light" : "dark") + " theme."
      : "CE background is the theme default 0x" + ground.toString(16).toUpperCase().padStart(4, "0") +
        (state.theater ? ": theater has no cover to average." : ": theater mode is off.");
  } else theater.hidden = true;
  $("toggle-play").textContent = state.playing ? "Ⅱ" : "▶";
  $("toggle-play").setAttribute("aria-label",
    state.playing ? "Pause simulated playback" : "Resume simulated playback");
}

// Scale the chosen picture to the cover box (centre crop) as RGB565.
async function loadArt(file) {
  if (!file) return;
  const url = URL.createObjectURL(file);
  try {
    const image = new Image();
    image.src = url;
    await image.decode();
    const side = Math.min(image.naturalWidth, image.naturalHeight);
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = ART.size;
    const ctx = canvas.getContext("2d", {willReadFrequently: true});
    ctx.drawImage(image, (image.naturalWidth - side) / 2, (image.naturalHeight - side) / 2,
                  side, side, 0, 0, ART.size, ART.size);
    state.art = rgbaToWords(ctx.getImageData(0, 0, ART.size, ART.size).data);
    state.artName = "chosen cover";
    state.noArt = false;
    $("sim-no-art").checked = false;
    render();
  } catch (err) {
    status("Artwork could not be read: " + err.message, "bad");
  } finally {
    URL.revokeObjectURL(url);
  }
}

function showTab(name) {
  state.tab = name;
  document.querySelectorAll("[data-show]").forEach(button =>
    button.setAttribute("aria-pressed", String(button.dataset.show === name)));
  render();
}

function step(delta) {
  state.track = (state.track + delta + tracks.length) % tracks.length;
  state.position = 0;
  showTab("playing");
}

function init() {
  document.querySelectorAll("[data-show]").forEach(button =>
    button.addEventListener("click", () => showTab(button.dataset.show)));
  $("toggle-play").addEventListener("click", () => { state.playing = !state.playing; render(); });
  $("prev-track").addEventListener("click", () => step(-1));
  $("next-track").addEventListener("click", () => step(1));
  $("sim-theme").addEventListener("change", ev => { state.light = ev.target.value === "light"; render(); });
  $("sim-page").addEventListener("change", ev => { state.page = Number(ev.target.value); render(); });
  $("theater-preview").addEventListener("change", ev => { state.theater = ev.target.checked; render(); });
  $("sim-no-art").addEventListener("change", ev => { state.noArt = ev.target.checked; render(); });
  $("theater-art").addEventListener("change", ev => loadArt(ev.target.files[0]));
  $("sim-retry").addEventListener("click", load);
  setInterval(() => {
    if (!state.playing || state.tab !== "playing" || !state.res.ce) return;
    state.position = (state.position + 1) % tracks[state.track][2];
    render();
  }, 1000);
  // The section lives in the collapsed Advanced part of the page: load
  // the resources when it is first opened.
  const advanced = $("advanced");
  if (advanced.open) load();
  advanced.addEventListener("toggle", () => { if (advanced.open) load(); });
  // A stock image loaded in section 1 makes the stock fetch unnecessary.
  window.addEventListener("stock-firmware", () => { if (!state.res.stock) load(); });
  render();
}

init();
