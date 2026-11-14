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
    sha256: "8a9f32fc06ed2459ffd936a9203d6df6e665b273b49fb25e1083b0b96d8c5ce0",
    summary: "Every CE feature: full-precision Vorbis, gapless, natural sort, " +
      "Opus in place of WMA, the design refresh, theater mode, M3U " +
      "playlists, lock-screen track info and the Bluetooth shortcut.",
    caveat: "8,192 bytes longer than stock. CE has booted on hardware; " +
      "the current scan and responsiveness repair awaits full-card acceptance.",
  },
  {
    id: "minimal",
    file: "DP3_V137_CE_minimal.img",
    title: "Minimal",
    badge: "Stock length",
    length: 13631492,
    sha256: "0dfd10e23749f9b6c65499266f1a7a2ec038160b089ba0fc2ca68dcf2b24c986",
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
