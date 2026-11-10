# Feature preview validation

The existing Stageshow bento, sorting list and Vorbis counter are retained.
DevicePicture replaces the separate EQ card and Power-key illustration with
physical-player models using the hero's casing styles. Theater, EQ, Bluetooth,
playlist, lock-screen, gapless, Opus and wheel-timer screens share that model.
Screens are illustrative, as the page states; they are not hardware captures
or newly implemented firmware interfaces. EQ is labeled as a build option.

Checked in Chromium at 1440 and 390 pixels: section order, eight player
previews, font/page rendering, no horizontal overflow, no page errors,
Bluetooth preview toggling in both directions and expanded configuration fit.
TypeScript, production build and whitespace validation pass. The compiled
stage assets are rebuilt. Normal-motion Bluetooth hold/state and EQ drawing
are exercised separately, together with a dark reduced-motion screenshot.

Remaining limits: no physical-device, Safari or Firefox testing. No claim of
hardware validation. The physical-player geometry has the same limits for
Stageshow's UI-card geometry gate documented in ../hero/REHEARSAL.md; a new
passing film gate is not claimed for these illustrations.
