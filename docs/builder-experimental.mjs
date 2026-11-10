// Expected bytes and artifact pin for the Bluetooth tail build.
// The executable payload is built locally from patches/ui_features/build.
export const BT_PATCH = {
  index: 100, name: "ui-bt-dispatcher-hook-tail", module: 0,
  region: "code", address: 0x03061e5e,
  expect: "2046bde8f09f", replace: "1af0cbbb00bf",
};
export const BT_SHA256 = "ce6ef701285885efb17b072df128602c3ee5da8359b7b267cd7e1ca92457cf06";
export const BT_OFFSET = 0x644;
export const LOCK_PATCH = {index: 105, name: "ui-lockscreen-title", module: 31, region: "code",
  address: 0x0307e89e, expect: "e4f72fbf", replace: "00f0d3ba"};
export async function lockscreenPayload(bytes, sha256) {
  if (bytes.length !== 408 || await sha256(bytes) !== "959778084e3951fec1940778ae712049c7d8b13612a535957ab6d24a3c632ed4")
    throw new Error("lock-screen payload does not match the verified build");
  return bytes;
}
export const TITLE_PATCHES = [
  {index: 120, name: "player-title-bounded-copy", module: 27, region: "code", address: 0x0307f9d0,
   expect: "adf80c70bdf80c1033f811206ab320f81120491c89b2adf80c108029f2d3",
   replace: "002133f8112042b17f2903d220f811200131f6e720f8117001e026e000bf"},
  {index: 121, name: "player-title-safe-suffix", module: 27, region: "code", address: 0x0307fa3a,
   expect: "8ab220f8127000eb410030f8081c2e2908bf20f8087c30f80a1c2e2908bf20f80a7cc7e7",
   replace: "20f8117005290ad300eb41000a3841882e2908bf478001882e2908bf0780c9e700bf00bf"},
];
export const PLAYLIST_PATCHES = [
  {index: 101, name: "ui-lockscreen-title", module: 31, region: "code", address: 0x0307e89e, expect: "e4f72fbf", replace: "02f007b8"},
  {index: 102, name: "m3u-browser-hook", module: 31, region: "code", address: 0x0307df1a, expect: "fff76df9", replace: "00f095bf"},
  {index: 103, name: "resolver-primary-hook", module: 0, region: "code", address: 0x03059dac, expect: "2de9f047", replace: "22f056bb"},
  {index: 104, name: "resolver-companion-hook", module: 0, region: "code", address: 0x0305b2c2, expect: "2de9f047", replace: "21f0e8b8"},
];

export async function bluetoothTail(bytes, sha256) {
  if (bytes.length !== 436 || await sha256(bytes) !== BT_SHA256)
    throw new Error("Bluetooth payload does not match the verified build");
  const tail = new Uint8Array(BT_OFFSET + bytes.length);
  tail.set(bytes, BT_OFFSET);
  return tail;
}

export async function playlistPayloads(overlay, resolver, sha256) {
  if (overlay.length !== 7168 || await sha256(overlay) !== "84b82518bfb02105cb4166914021b0e56a2ba16ea1cbd19ecc88abe70dbbfe28")
    throw new Error("playlist/lock-screen payload does not match the verified build");
  if (resolver.length !== 1602 || await sha256(resolver) !== "43f5867abaee882171466438e0a8fa0efa3f930b70339064759b993dc9a0dab4")
    throw new Error("playlist resolver does not match the verified build");
  return {overlay, resolver};
}

// Theater mode data lives in builder-theater.mjs (generated from
// patches/theater/build/); only its pin and guards live here.
export const THEATER_SHA256 = "96931a93bd197782f5efda40974ab31731c801e4231f29f44c1dfa7347c0fc78";
export async function theaterTail(bytes, sha256) {
  if (bytes.length !== 676 || await sha256(bytes) !== THEATER_SHA256)
    throw new Error("theater payload does not match the verified build");
  return bytes;
}

// The theater payload starts at the tail base and the feature is
// built as the image's one tail feature, so it excludes the other
// tail features and the lock screen. Returns the tail payload to
// build with: the theater payload when theater is selected, else
// the already-combined tail (see combineTails).
export function combineWithTheater(theater, tail, lockSelected) {
  if (!theater) return tail;
  if (tail || lockSelected)
    throw new Error("theater mode cannot be combined with the " +
      "Bluetooth shortcut, lock-screen or playlist features");
  return theater;
}

export function combineTails(resolver, btTail) {
  if (!resolver) return btTail;
  if (!btTail) return resolver;
  if (resolver.length > BT_OFFSET || btTail.subarray(0, BT_OFFSET).some(b => b !== 0))
    throw new Error("playlist and Bluetooth tail payloads overlap");
  const combined = new Uint8Array(btTail);
  combined.set(resolver);
  return combined;
}
