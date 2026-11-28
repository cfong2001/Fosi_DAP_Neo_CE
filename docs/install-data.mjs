// Release images offered by the install flow on index.html.
//
// Every image is fetched from the repository's release/ directory and
// refused unless its length and SHA-256 match the pins below.
// tests/install-data.test.mjs checks these pins against
// release/SHA256SUMS and the files themselves, so a change to the
// release set must update this file in the same commit.

// Repository used when the page is not served from <owner>.github.io/<repo>/
// (for example from a local checkout during development).
export const DEFAULT_REPO = "cfong2001/Fosi_DAP_Neo_CE";
export const RELEASE_REF = "main";
export const RELEASE_DIR = "release";

// Visible FAT 8.3 filename: the stock installer compares the raw 11-byte
// directory name RKNANOFWIMG (8-byte basename + 3-byte extension).
// Copy to the root of the player's storage (release/README.md).
export const UPDATE_NAME = "RKNANOFW.IMG";

export const IMAGES = [
  {
    id: "standard",
    file: "DP3_V137_CE.img",
    title: "Standard",
    badge: "Recommended",
    length: 13639684,
    sha256: "175d4aff14407d7ddab3733fe7a57e25801d2082ca34ce0335af5d813d5f2c87",
    summary: "Every CE feature: full-precision Vorbis, gapless, natural sort, " +
      "Opus in place of WMA, the design refresh, theater mode, M3U " +
      "playlists, lock-screen track info and the Bluetooth shortcut.",
    caveat: "8,192 bytes longer than stock. Booted, scanned a full card and " +
      "played Opus with album art on hardware.",
  },
  {
    id: "minimal",
    file: "DP3_V137_CE_minimal.img",
    title: "Minimal",
    badge: "Stock length",
    length: 13631492,
    sha256: "43476a08ace9e4fbf942bfcab2bbd5eea2e3554ac7a7c7cf60f9770d29700565",
    summary: "Audio and library fixes only: full-precision Vorbis, gapless, " +
      "natural sort, decoder clocks and the DAC error counter. Keeps WMA.",
    caveat: "Same length as stock. Use it if Standard does not install or " +
      "if you play WMA files.",
  },
  {
    id: "recovery",
    file: "DP3_V137_CE_recovery.img",
    title: "Back to stock",
    badge: "Recovery",
    length: 13631492,
    sha256: "aff851b31d6eee55cbd4bb3fc0464ac79f0039ee86ae6723225ac036a157d223",
    summary: "Unmodified stock code dated one day after CE, so the player " +
      "prefers it over a CE install.",
    caveat: "Plain stock DP3_V137.img is older than CE and would not " +
      "replace it; use this file to go back.",
  },
];
