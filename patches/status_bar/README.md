# Remaining status-bar black rectangles (draft)

The accepted Standard release fixes the progress gaps and substantially improves
background fill and wheel response. Small black rectangles remain at the top
status bar. Keep this correction independent of general performance work.

## Reproduction baseline

`test_status_resource_draw.py` draws 13 small indicator resources through the
real native DrawImageAt entry over a nonblack background. It reuses the existing
staged-resource/DMA model and records final framebuffer pixels. Resource 133
(the real player painter draws it at 10,7) writes 28 black pixels. Neighboring
resources 143 and 144 write 88 and 102 black pixels. The ten sampled battery-like
resources write no exact-black pixels but do overwrite their whole rectangles.
These are isolated resource observations, not proof of which live status-window
writer produced the reported rectangles. Black may also be legitimate icon ink.

```sh
python patches/status_bar/test_status_resource_draw.py
```

No release bytes or shared icon behavior change in this initial draft.

## Diagnosis and acceptance

1. Execute the complete status-window lifecycle and trace the last writer for
   each unwanted surround pixel, including erase/fill/text and resource paths.
   Do not treat every black pixel as an error or globally recolor the resources.
2. Reproduce battery level/charging, Bluetooth on/off/connected, volume, shuffle
   and repeat transitions, both themes, bright/dark/no-art track changes and
   player entry/exit. Record per-state unwanted-surround counts and last-writer PCs.
3. Repair the proved status-specific draw or erase path. Require zero unwanted
   surround pixels, identical intended indicator ink and zero ghost pixels after
   transitions, with all outside-region bytes preserved.
4. Run the existing progress, full-ground, focus and selected-control gates.
   Confirm on hardware before merging or replacing the accepted release.

Residual transport-first background staging is recorded separately from these
boxes; neither cause nor a complete fix is claimed by this resource census.
