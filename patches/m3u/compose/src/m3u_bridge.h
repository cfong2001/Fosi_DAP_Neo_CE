/*
 * m3u_bridge.h - device glue between the M3U parser core (m3u.h) and
 * the stock DAP Neo firmware, plus the writer for the resolver staging
 * the gap-tail hooks consume. Composed-build version: this header
 * supersedes work/m3u_bridge/bridge/m3u_bridge.h, whose contracts were
 * written before the bridge_completion pins landed. Corrections
 * relative to that draft, all from work/m3u_bridge/bridge_completion.md:
 *
 *   - The file primitives take descriptor HANDLES, not paths. A file
 *     is registered by calling the resident registrar (module 0
 *     0x0305C514) with a directory cluster and an 11-byte 8.3 name;
 *     the slot is never filled directly.
 *   - The browser keeps no path string for anything (B1). Identity is
 *     cluster-based: the playlist is the selected node, its parent
 *     directory is the browser's current level record.
 *   - stat() returns the resolver playback identity of a file: the
 *     PARENT DIRECTORY cluster plus the file's ordinal among the
 *     classifier-accepted files of that directory (the enumeration
 *     0x0305AB0A counts, card mode). m3u.h's M3uFileInfo comment calls
 *     the pair (clus, index) "the stock playback identity"; for the
 *     source-6 resolver space the operative pair is (directory
 *     cluster, within-directory index), which is what the tail hooks
 *     serve. The file's own first cluster is not part of staging.
 *
 * The staging layout written here is patches/m3u/tail_build/
 * tail_build.md's trimmed layout at 0x0307BFB4, byte for byte.
 */
#ifndef M3U_BRIDGE_H
#define M3U_BRIDGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "m3u.h"

/* ---- resolver staging (tail_build.md, trimmed layout) ------------- */

#define M3U_STAGE_BASE      0x0307BFB4u
#define M3U_STAGE_HDR_LEN   16u
#define M3U_STAGE_MAX_RUNS  12u
#define M3U_STAGE_RUN_LEN   50u   /* u32 cluster, u16 countA, u16 countB,
                                     42-byte stock context              */
#define M3U_STAGE_MAX_ENT   144u
#define M3U_STAGE_ENT_LEN   4u    /* u16 within-directory index,
                                     u8 run id, u8 flags                */
#define M3U_STAGE_RUNS_OFF  M3U_STAGE_HDR_LEN
#define M3U_STAGE_ENT_OFF   (M3U_STAGE_HDR_LEN + \
                             M3U_STAGE_MAX_RUNS * M3U_STAGE_RUN_LEN)
#define M3U_STAGE_TOTAL     (M3U_STAGE_ENT_OFF + \
                             M3U_STAGE_MAX_ENT * M3U_STAGE_ENT_LEN)

/* Entry point called by the 0040 trampoline (which has already matched
 * the node's 8.3 extension against "M3U"). node/state/ctx are the
 * registers the node-action function holds at the hook site: r4 = node,
 * r7 = browser state, r8 = play context. Returns 1 when the import was
 * staged and armed (the trampoline then leaves through the stock
 * common exit with r0 = 1), 0 to decline: the trampoline reproduces
 * the displaced stock call and stock behaviour continues. */
int m3u_bridge_node_action(const uint8_t *node, const uint8_t *state,
                           const uint8_t *ctx);

#endif /* M3U_BRIDGE_H */
