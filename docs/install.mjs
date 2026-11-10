// Install flow at the top of index.html: choose an image, then either
// copy it to the player's storage as RKNANOFWIMG (File System Access
// API, Chromium browsers) or download it.
//
// Nothing here writes to the player's flash. The browser only places the
// update file on the player's USB storage; the player's own installer
// flashes it when the user runs the update on the device.
import {DEFAULT_REPO, RELEASE_REF, RELEASE_DIR, UPDATE_NAME, IMAGES} from "./install-data.mjs";
import {sha256} from "./theme-core.mjs";

const $ = id => document.getElementById(id);
const fmt = n => n.toLocaleString("en-US");

// Served from <owner>.github.io/<repo>/, fetch from that repository, so a
// fork's page offers the fork's images. Otherwise use the default.
export function repoFromLocation(loc) {
  const host = loc.hostname.toLowerCase();
  if (!host.endsWith(".github.io")) return DEFAULT_REPO;
  const owner = host.slice(0, -".github.io".length);
  const first = loc.pathname.split("/").filter(Boolean)[0];
  return owner + "/" + (first || owner + ".github.io");
}

export function rawUrl(repo, file) {
  return "https://raw.githubusercontent.com/" + repo + "/" + RELEASE_REF +
    "/" + RELEASE_DIR + "/" + file;
}

const repo = repoFromLocation(window.location);
const verified = new Map();   // image id -> verified bytes
let custom = null;            // {name, bytes, sha256} from the builder
let selected = IMAGES[0].id;
let busy = false;

function setStatus(message, kind = "") {
  const el = $("install-status");
  el.hidden = false;
  el.textContent = message;
  el.className = "status" + (kind ? " " + kind : "");
}

function setProgress(done, total) {
  const bar = $("install-progress");
  if (done === null) { bar.hidden = true; return; }
  bar.hidden = false;
  bar.max = total;
  bar.value = done;
}

function choice() {
  if (selected === "custom") {
    return custom && {id: "custom", file: custom.name, title: "Your custom build",
      length: custom.bytes.length, sha256: custom.sha256};
  }
  return IMAGES.find(image => image.id === selected);
}

function renderChoices() {
  const root = $("image-choices");
  root.replaceChildren();
  const entries = [...IMAGES];
  if (custom) {
    entries.push({id: "custom", file: custom.name, title: "Your custom build",
      badge: "Built here", length: custom.bytes.length, sha256: custom.sha256,
      summary: "The image you built in Advanced below. It exists only in " +
        "this tab.", caveat: "Not a release image: its hash is the one " +
        "computed when it was built."});
  }
  for (const image of entries) {
    const label = document.createElement("label");
    label.className = "image-choice";
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "image";
    input.value = image.id;
    input.checked = image.id === selected;
    input.addEventListener("change", () => {
      selected = image.id;
      updateActions();
    });
    const body = document.createElement("span");
    body.className = "image-body";
    const head = document.createElement("span");
    head.className = "image-head";
    const title = document.createElement("strong");
    title.textContent = image.title;
    const badge = document.createElement("span");
    badge.className = "badge" + (image.id === "standard" ? " accent" : "");
    badge.textContent = image.badge;
    head.append(title, badge);
    const summary = document.createElement("span");
    summary.className = "note";
    summary.textContent = image.summary;
    const caveat = document.createElement("span");
    caveat.className = "note muted";
    caveat.textContent = image.caveat;
    const meta = document.createElement("code");
    meta.className = "image-meta";
    meta.textContent = image.file + " · " + fmt(image.length) + " bytes · SHA-256 " +
      image.sha256;
    body.append(head, summary, caveat, meta);
    label.append(input, body);
    root.append(label);
  }
}

function renderManualLinks() {
  const list = $("direct-links");
  list.replaceChildren();
  for (const image of IMAGES) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = rawUrl(repo, image.file);
    a.textContent = image.file;
    li.append(a, " (" + image.title + ")");
    list.append(li);
  }
  const sums = document.createElement("li");
  const a = document.createElement("a");
  a.href = rawUrl(repo, "SHA256SUMS");
  a.textContent = "SHA256SUMS";
  sums.append(a);
  list.append(sums);
}

function updateActions() {
  const image = choice();
  $("copy-to-player").disabled = busy || !image;
  $("download-image").disabled = busy || !image;
  $("download-update-name").disabled = busy || !image;
}

async function fetchVerified(image) {
  if (verified.has(image.id)) return verified.get(image.id);
  const url = rawUrl(repo, image.file);
  setStatus("Downloading " + image.file + " from " + repo + "…");
  setProgress(0, image.length);
  let response;
  try {
    response = await fetch(url, {cache: "no-store"});
  } catch (err) {
    throw new Error("could not reach GitHub (" + err.message + "). " +
      "Check your connection, or use a direct link under Manual install.");
  }
  if (!response.ok) {
    throw new Error("GitHub returned " + response.status + " for " + image.file +
      ". Use a direct link under Manual install.");
  }
  const bytes = new Uint8Array(image.length);
  let done = 0;
  const reader = response.body.getReader();
  for (;;) {
    const {done: end, value} = await reader.read();
    if (end) break;
    if (done + value.length > image.length) {
      await reader.cancel();
      throw new Error(image.file + " is longer than its pinned " +
        fmt(image.length) + " bytes; refused.");
    }
    bytes.set(value, done);
    done += value.length;
    setProgress(done, image.length);
  }
  if (done !== image.length) {
    throw new Error(image.file + " is " + fmt(done) + " bytes, expected " +
      fmt(image.length) + "; refused.");
  }
  setStatus("Checking SHA-256 of " + image.file + "…");
  const got = await sha256(bytes);
  if (got !== image.sha256) {
    throw new Error(image.file + " has SHA-256 " + got + ", expected " +
      image.sha256 + "; refused.");
  }
  verified.set(image.id, bytes);
  return bytes;
}

async function bytesFor(image) {
  if (image.id === "custom") return custom.bytes;
  return fetchVerified(image);
}

function save(name, bytes) {
  const url = URL.createObjectURL(new Blob([bytes], {type: "application/octet-stream"}));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function run(task) {
  if (busy) return;
  busy = true;
  updateActions();
  try {
    await task();
  } catch (err) {
    if (err?.name === "AbortError") setStatus("Cancelled. Nothing was written.");
    else setStatus("Stopped: " + err.message, "bad");
  } finally {
    busy = false;
    setProgress(null);
    updateActions();
  }
}

async function download(asUpdateName) {
  const image = choice();
  const bytes = await bytesFor(image);
  const name = asUpdateName ? UPDATE_NAME : image.file;
  save(name, bytes);
  setStatus("Saved " + name + " (" + fmt(bytes.length) + " bytes, SHA-256 " +
    image.sha256 + " verified). " + (asUpdateName
      ? "Copy it to the top level of the player's storage, then do step 3."
      : "Rename it to " + UPDATE_NAME + " (no extension) and copy it to the " +
        "top level of the player's storage, then do step 3."), "good");
}

async function copyToPlayer() {
  const image = choice();
  // Ask for the folder first: the picker needs the click's user gesture.
  const dir = await window.showDirectoryPicker({id: "dap-neo-storage", mode: "readwrite"});
  const bytes = await bytesFor(image);
  setStatus("Writing " + UPDATE_NAME + " to " + dir.name + "…");
  setProgress(0, bytes.length);
  const handle = await dir.getFileHandle(UPDATE_NAME, {create: true});
  const writable = await handle.createWritable();
  try {
    const chunk = 1 << 20;
    for (let at = 0; at < bytes.length; at += chunk) {
      await writable.write(bytes.subarray(at, Math.min(at + chunk, bytes.length)));
      setProgress(Math.min(at + chunk, bytes.length), bytes.length);
    }
    await writable.close();
  } catch (err) {
    await writable.abort().catch(() => {});
    throw err;
  }
  setStatus("Reading " + UPDATE_NAME + " back to check it…");
  const back = new Uint8Array(await (await handle.getFile()).arrayBuffer());
  const got = await sha256(back);
  if (back.length !== bytes.length || got !== image.sha256) {
    throw new Error("the copy on " + dir.name + " does not match (" +
      fmt(back.length) + " bytes, SHA-256 " + got + "). Delete " + UPDATE_NAME +
      " from the player and try again.");
  }
  setStatus("Copied " + image.file + " to " + dir.name + " as " + UPDATE_NAME +
    " and read it back: " + fmt(back.length) + " bytes, SHA-256 matches. " +
    "Eject the player safely, then do step 3.", "good");
}

function init() {
  renderChoices();
  renderManualLinks();
  $("update-name").textContent = UPDATE_NAME;
  const canCopy = typeof window.showDirectoryPicker === "function";
  $("copy-to-player").hidden = !canCopy;
  $("copy-support").textContent = canCopy
    ? "Copy to player asks for the player's drive, downloads the image, checks its SHA-256, " +
      "writes it as " + UPDATE_NAME + " and reads it back. Pick the top level of the drive, " +
      "not a folder inside it."
    : "This browser cannot write to a drive directly (Chrome and Edge on a computer can). " +
      "Download the image ready-named instead and copy it to the player yourself.";
  $("copy-to-player").addEventListener("click", () => run(copyToPlayer));
  $("download-image").addEventListener("click", () => run(() => download(false)));
  $("download-update-name").addEventListener("click", () => run(() => download(true)));
  updateActions();

  // A custom image built in the Advanced section becomes a fourth choice.
  window.addEventListener("ce-build", event => {
    custom = event.detail;
    selected = "custom";
    renderChoices();
    updateActions();
    setStatus("Your custom build (" + custom.name + ") is selected in step 1. " +
      "Use step 2 to put it on the player.", "good");
  });

  // Links into the builder open the Advanced section.
  const reveal = () => {
    const target = location.hash && document.getElementById(location.hash.slice(1));
    const advanced = $("advanced");
    if (target && advanced.contains(target) && !advanced.open) {
      advanced.open = true;
      target.scrollIntoView();
    }
  };
  window.addEventListener("hashchange", reveal);
  reveal();
}

init();
