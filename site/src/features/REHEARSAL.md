# Rehearsal: interactive DAP Neo feature studies

## Composition and source

Starting point: the existing Stageshow bento and natural-sort scene. Compared
against the upstream `device-pair` gold (captured locally). Retained Stage,
poster, once-in-view timing and kit controls; the physical model is authored
for the supplied Fosi reference photos rather than a generic phone.

The plan gives three primary interactions distinct compositions: album art
beside explanatory copy; an EQ screen closeup; and a Power-button study with
an actual sustained hold. Lock-screen title/time gets a separate closeup.
Supporting features are a playlist, waveform, format comparison, timer bars
and Vorbis statistic rather than repeated whole-player miniatures.

## Behavior

Three.js builds a beveled aluminum body, glass/display, wheel, center button,
side keys and ports. Canvas textures are illustrative screens, explicitly
identified as previews in the page. They are not hardware captures or new
firmware editor screens. EQ uses the existing fitted 31-band example.

Bluetooth: authored off → hold → on; manual pointer/touch/Space/Enter hold
requires 1.2 seconds, and early release/cancel/blur aborts it. Raycasting maps
holds on the model's orange Power button to the same handler. EQ controls
interpolate the curve between stock and fitted values. Artwork choices change
both the cover and its derived playback background. Result posters remain
complete under reduced motion; renderers do no continuous idle work and dispose
GPU resources and listeners when unmounted.

## Captures and checks

Chromium, 1440 and 390 CSS pixels, light and dark, normal and reduced motion.
Reviewed full feature-page captures, model closeups, stock-to-fitted EQ contact
sheet, Bluetooth off/hold/on contact sheet and phone state sheet. Tested actual
side-button hit, early release, sustained pointer hold, sustained keyboard hold,
EQ screen pixel changes, artwork controls, page overflow and configuration fit.
Seven browser integration tests pass, including firmware simulator, verified
install/download, builder output and the new device interaction regression.
TypeScript and production build pass; committed stage assets rebuilt.

Film gate last lines for Bluetooth wide, Bluetooth phone states and EQ phone:
`rehearsal passed (necessary, not sufficient: references/verify.md and the fresh eye in review.md still stand)`.
The filming tool exits 2 overall because the software WebGL renderer/readback
causes sampling gaps. It does not establish complete per-frame motion coverage.
The contact sheets and live interaction checks supplement the gate; no claim
of verified 60fps hardware performance is made.

Fresh-eye review found small focal screens, a playlist highlight between rows,
redundant delayed Bluetooth status, and abrupt internal crops. Increased screen
camera scale, anchored the selection to its actual row wrapper, removed the
external status, preserved Bluetooth's silhouette and faded lower casing in
screen closeups. Re-captured after these fixes.

Not checked: physical mobile hardware, Safari/Firefox, real-device firmware
behavior, every GPU/driver, and complete fine-interval coverage under software
WebGL. Shader literals in the generated Three.js bundle retain upstream whitespace.

## Context review (follow-up)

Each picture was reviewed in place after it had time to play, at 1440 and
390 CSS pixels. Fixed: the theater screen now draws the previous, play and
next glyphs directly over the derived background, which is what its copy
and the firmware change describe, and its camera pulls back so the player
clears the tile's top edge; the lock screen shows elapsed / total time, as
the lock routine draws it, and its copy says so; the Vorbis stat reads
"more than 40 dB" (stock measures 38.1 to 42.1 dB and CE at least 84.9 dB on
the corpus) and spans the last row as one statement instead of sitting alone
beside an empty cell. The hero, EQ, Bluetooth, playlist, sort, gapless, Opus
and wheel-timer pictures were checked and left as they were.
