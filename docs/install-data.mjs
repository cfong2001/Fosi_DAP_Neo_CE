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

// The stock installer looks for this name, with no dot and no extension,
// at the root of the player's storage (release/README.md).
export const UPDATE_NAME = "RKNANOFWIMG";

export const IMAGES = [
  {
    id: "standard",
    file: "DP3_V137_CE.img",
    title: "Standard",
    badge: "Recommended",
    length: 13638454,
    sha256: "6305014618c35c6c78d573dfda760ee75cd1978a9448961fed5d0fe04015f2b7",
    summary: "Every CE feature: full-precision Vorbis, gapless, natural sort, " +
      "Opus in place of WMA, the design refresh, theater mode, M3U " +
      "playlists, lock-screen track info and the Bluetooth shortcut.",
    caveat: "6,962 bytes longer than stock. No longer-than-stock image has " +
      "been installed yet; if this one does not install, use Minimal.",
  },
  {
    id: "minimal",
    file: "DP3_V137_CE_minimal.img",
    title: "Minimal",
    badge: "Stock length",
    length: 13631492,
    sha256: "92c446066e715d74a719671d3ee643ed4b7587c94801eb6dc3893f2271ed944d",
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
