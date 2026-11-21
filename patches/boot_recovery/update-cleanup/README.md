# Update file cleanup

During startup, V137 looks for `RKNANOFW.IMG` and the versioned update
filenames. The installer tries to delete the source after copying the image.
It originally discarded the deletion result. If deletion failed after a
successful copy, the update window entered its success wait loop, stopped
servicing the watchdog, and could encounter the same file on the next boot.

The patched installer returns zero only when the copy and deletion both
succeed. On a cleanup failure the update window retains its existing failure
handling. The update file may still be detected on a later independent boot
until it is removed. The flash write and slot geometry are exercised through
stubs in the regression tests. Physical update and restart behavior remains
to be verified.

Build a dated test image with `tools/prepare_flash.py --boot-patch update-cleanup`
and the normal candidate, official recovery and output arguments in the
[flash review](../../../release/FLASH_REVIEW.md). Standard and Minimal release
images omit this patch.
