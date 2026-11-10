/*
 * m3u_bridge.h - device bridge between the M3U parser core
 * (work/patches/m3u/src/m3u.h) and the DAP Neo stock firmware.
 *
 * Target: the module 0 code-region extension, exec 0x03079C14.
 * Layout (see m3u_bridge.md):
 *   +0x00  m3u_hook        hook trampoline (assembled, in the blob)
 *   +0x80  m3u_bridge_node_action   this bridge's entry (stub today)
 *   +0x84  parser core + bridge code, once arm-none-eabi-gcc exists
 *
 * Every stock address below is pinned in m3u_bridge.md with its
 * evidence grade. Anything marked [open] is a named blocker, not a
 * guess: the code that depends on it is written against the pinned
 * part only and stops at the blocker.
 */
#ifndef M3U_BRIDGE_H
#define M3U_BRIDGE_H

#include <stdint.h>

/* ---- extension layout ---- */
#define EXT_BASE        0x03079C14u
#define EXT_HOOK_OFF    0x00u
#define EXT_BRIDGE_OFF  0x80u
#define EXT_MAX         11164u

/* ---- stock primitives (module 0, resident) ---- */

/* FS acquire: called by every overlay before file work (module 37
 * calls it at 0x0307D804 inside its parse loop). [proven call sites] */
extern void stock_fs_acquire(void);                 /* 0x030611E0 */

/* Whole-file model, from module 37's CUE parse entry 0x0307D73A:
 * it asks for the size, then reads the whole file into a RAM buffer
 * and parses from RAM (BOM sniff on the buffer at 0x0307D772).
 *   size: 0x030545D4(path) -> count used as the read cap and as the
 *          parse loop bound.              [inferred from call sites]
 *   read: 0x030693EA(path, buf, cap, 0) -> >= 0 on success (the
 *          caller error-branches on a negative return and then
 *          parses buf).                    [inferred from call sites]
 *   log:  0x0306D8F0(fmt, ...) error/string logging, called with
 *          ADR string pointers on module 37's error paths. [likely] */
extern int  stock_file_size(const char *path);      /* 0x030545D4 */
extern int  stock_file_read(const char *path, void *buf, uint32_t cap, int zero);
                                                    /* 0x030693EA */
extern void stock_log(const char *fmt, ...);        /* 0x0306D8F0 */

/* Directory walker wrapper (module 0 0x0305A970):
 *   walker_wrap(ctx, block, table, mode)
 *     ctx   = the walker's path context (its r0; the dirent record
 *             is written at ctx +0x00/+0x04/+0x08/+0x0A/+0x0B)
 *     block = parameter block (walker arg 5):
 *             +0x00  directory cluster to walk        [walker reads]
 *             +0x04  cursor: wrapper zeroes it on entry; the walker
 *                    stores the found entry's position here
 *             +0x08  entry count of the directory     [walker reads;
 *                    producer is open pin B5 in m3u_bridge.md]
 *             +0x0C  found entry ordinal (halfword out)
 *             +0x10  found flag (0/1 out)
 *             +0x14/+0x18  found entry fields (mode-dependent)
 *             +0x1C  inline name buffer
 *     table = 3-byte extension codes, terminated by an entry whose
 *             first byte is 0; a first byte of '*' (0x2A) matches
 *             every entry (classifier 0x0305A15C, proven).
 *     mode  = walker arg 7 (module 38 passes 6, module 31 passes
 *             its fp register; semantics per-source).
 *   The wrapper hard-codes walker arg 6 = 3.
 * Returns the walker's result (nonzero = entry found, per the
 * mode-3 call sites in module 38 at 0x0307E63E/0x0307E7B6). */
extern int stock_walker(void *ctx, void *block, const uint8_t *table,
                        uint32_t mode);             /* 0x0305A970 */

/* ---- play context (0x03023980), fields as written by module 31's
 * folder-play path at 0x0307E088 and consumed by module 33 ---- */
#define PLAY_CTX            0x03023980u
#define PLAY_CTX_TOTAL      (*(volatile uint16_t *)(PLAY_CTX + 0x00))
#define PLAY_CTX_INDEX      (*(volatile uint16_t *)(PLAY_CTX + 0x02))
#define PLAY_CTX_SOURCE     (*(volatile uint16_t *)(PLAY_CTX + 0xF2))
#define PLAY_SOURCE_FOLDER  6   /* the folder-play source code */

/* ---- bridge entry, called by the hook trampoline ----
 * node  = the browser's selected display node (module 31 r4):
 *         +0x4E class byte, +0x4F 11-byte 8.3 name (ext at +0x57)
 * state = module 31's browser state (r7)
 * ctx   = the play context pointer (r8 at the hook site)
 * Returns nonzero when the node was a playlist and playback was
 * staged; zero declines (the trampoline then runs the stock path). */
int m3u_bridge_node_action(void *node, void *state, void *ctx);

#endif /* M3U_BRIDGE_H */
