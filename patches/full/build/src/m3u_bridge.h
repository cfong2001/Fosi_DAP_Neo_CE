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
 * The staging layout written here is the packed layout below, at
 * 0x0307BFB4 in the merged gap tail.
 */
#ifndef M3U_BRIDGE_H
#define M3U_BRIDGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "m3u.h"

/* ---- resolver staging (packed layout) -------------------------------
 *
 * 552 bytes at 0x0307BFB4, the same span the merged gap tail reserves.
 * Every folder run used to carry its own copy of the 42-byte stock
 * context, but the bridge captures that context once per import (the
 * standing context at 0x0307BF5C) and the copies were identical, so the
 * packed layout stores it once and keeps runs and entries as flat
 * arrays:
 *
 *   +0    u8  flag (set last), +1 u8 entry count, +2 u16 last position
 *         served, +4 u16 last ordinal served, +6 u8 run count, +7..+15 0
 *   +16   42-byte stock context, then 2 bytes of padding
 *   +60   u32 run cluster[32]
 *   +188  u16 run total[32]           countA + countB of the run folder
 *   +252  u16 entry[150]              bits 0-10: 0-based ordinal among
 *                                     the folder's accepted files,
 *                                     bits 11-15: run id
 *
 * The resolver hooks (resolver_hook.S) read this layout; keep the two
 * in step. */

#define M3U_STAGE_BASE      0x0307BFB4u
#define M3U_STAGE_TOTAL     552u
#define M3U_STAGE_HDR_LEN   16u
#define M3U_STAGE_CTX_OFF   16u
#define M3U_STAGE_CTX_LEN   42u
#define M3U_STAGE_MAX_RUNS  32u
#define M3U_STAGE_CLUS_OFF  60u
#define M3U_STAGE_SUM_OFF   (M3U_STAGE_CLUS_OFF + 4u * M3U_STAGE_MAX_RUNS)
#define M3U_STAGE_MAX_ENT   150u
#define M3U_STAGE_ENT_OFF   (M3U_STAGE_SUM_OFF + 2u * M3U_STAGE_MAX_RUNS)
#define M3U_STAGE_ORD_BITS  11u
#define M3U_STAGE_MAX_ORD   ((1u << M3U_STAGE_ORD_BITS) - 1u)

#if M3U_STAGE_ENT_OFF + 2u * M3U_STAGE_MAX_ENT != M3U_STAGE_TOTAL
#error "staging layout does not fill its 552-byte span exactly"
#endif
#if M3U_STAGE_MAX_RUNS > (1u << (16u - M3U_STAGE_ORD_BITS))
#error "run id does not fit the entry's high bits"
#endif

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
