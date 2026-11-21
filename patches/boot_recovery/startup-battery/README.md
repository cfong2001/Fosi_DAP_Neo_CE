# Startup battery check

V137 reads the battery ADC 18 times during startup. Its cutoff checks only the
last sample, so a single dip below 3.30 V can drop the power-hold GPIO on
battery. The modified routine counts samples below the existing cutoff and
requires at least nine of the eighteen to shut down. A tie favors shutdown.
The USB exception, ADC polling and restoration, and displayed battery level
still use the stock behavior.

Build a dated test image with `tools/prepare_flash.py --boot-patch startup-battery`
and the normal arguments in the [flash review](../../../release/FLASH_REVIEW.md).
Standard and Minimal release images omit this patch. The tests execute the
firmware with synthetic ADC readings. A device trial still needs to verify
behavior with a weak battery under startup load and with USB power.
