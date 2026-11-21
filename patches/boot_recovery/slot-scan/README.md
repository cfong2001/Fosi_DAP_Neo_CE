# Secondary firmware-slot scan

The V137 module-1 validator intended to bound the secondary scan to 20
candidates. The magic-mismatch branch jumps around the limit, and the
mirror-mismatch branch stops the search before trying the next candidate. Some
read failures also leave stale contents in the scan buffers.

The patched scan tries at most 20 candidates and skips secondary candidates
with failed reads, bad magic, an invalid mirror offset or a mismatching
mirror. The stock scan direction and selection rules apply to valid slots.
Primary fallback uses the original candidate sector, which is saved before
secondary mirror reads reuse the primary header buffer.

Build a dated test image with `tools/prepare_flash.py --boot-patch slot-scan`
and the normal arguments in the [flash review](../../../release/FLASH_REVIEW.md).
Standard and Minimal release images omit this patch. This changes the
validator packaged in V137. Whether an earlier boot stage executes this copy
on the DAP Neo remains unverified. Emulation uses synthetic sector reads.
