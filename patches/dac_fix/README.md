# DAC error-counter fix

Shipped in both images (Standard and Minimal) as patches 0001 and 0002 in
[`../framework/patches/`](../framework/patches/).

Stock counts total I2C errors per playback session and stops talking to the
CS43198 after two, so two transient errors freeze volume and DAC control
until playback stops. The fix counts consecutive failures instead and keeps
the dead-DAC protection.

- [`dac_fix.md`](dac_fix.md): the defect, the two-patch fix and its verification.
- `verify_dac_fix.py`: the offline check.
