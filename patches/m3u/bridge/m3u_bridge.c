/*
 * m3u_bridge.c - the device side of M3U support for stock DP3_V137.
 *
 * Implements the M3uFs vtable (work/patches/m3u/src/m3u.h) over the
 * stock firmware's own services, stages the resolved tracks in
 * playlist order, and fills the play context exactly the way module
 * 31's folder-play path does (source code 6), so the player iterates
 * the staged records and the library database is never involved.
 *
 * Build (when arm-none-eabi-gcc is available; it is NOT installed in
 * the current environment, see m3u_bridge.md job 3):
 *   arm-none-eabi-gcc -Os -std=c99 -mcpu=cortex-m3 -mthumb \
 *       -ffreestanding -fno-builtin -nostdlib \
 *       -T extension.ld -o m3u_extension.elf \
 *       m3u_bridge.c ../patches/m3u/src/m3u.c
 * with the blob laid out as: trampoline at +0x00, this file's entry
 * at +0x80 (EXT_BRIDGE_OFF), parser + bridge code after it.
 *
 * BLOCKERS (named in m3u_bridge.md; the code below stops at each):
 *   B1 current-directory path for the playlist's folder: module 31's
 *      state layout for "current directory" is not traced, so
 *      bridge_playlist_path() cannot yet be completed. It is the
 *      only missing piece between the hook and a running import.
 *   B2 staging arena address: candidate RAM exists (module 39's
 *      arena when not scanning; module 0 data BSS) but no slice is
 *      proven free, so STAGE_BASE is a build-time parameter, not a
 *      constant this file invents.
 *   B3 module 33's index->record fetch for source 6: the playback
 *      task's advance is uniform in (total, index), but the fetch
 *      chain's array base was not traced; the context fill below
 *      mirrors module 31's own stores, which is the strongest
 *      available evidence, and B3 is the hardware/emulation check
 *      that remains.
 *   B5 walker block +0x08 (directory entry count) producer.
 */

#include "m3u_bridge.h"
#include "../../patches/m3u/src/m3u.h"

/* ------------------------------------------------------------------ */
/* Configuration that must be pinned before a device build (B2).      */
/* ------------------------------------------------------------------ */
#ifndef STAGE_BASE
#error "STAGE_BASE (staging arena) is blocker B2: pin it against the SAVEINFO/BSS map before building for device"
#endif
#define STAGE_MAX_TRACKS 512u   /* 512 x 0x1C-byte records = 14 KB */

/* Playback-record-shaped staging entry: the fields module 24's fetch
 * (0x0306C7AC) and the play context use: +0x00 clus, +0x04 index,
 * then the +0x10/+0x14/+0x18 fields copied from the browser record. */
typedef struct StageRec {
    uint32_t clus;
    uint32_t index;
    uint32_t f08;
    uint32_t f0c;
    uint32_t f10;
    uint32_t f14;
    uint32_t f18;
} StageRec;                     /* 0x1C bytes */

static StageRec *const stage = (StageRec *)STAGE_BASE;

/* ------------------------------------------------------------------ */
/* M3uFs over stock: the playlist file itself                         */
/* ------------------------------------------------------------------ */

/* The stock file model is whole-file (module 37 precedent): size,
 * then one read into RAM. The parser wants offset reads; serve them
 * from the RAM copy. One playlist is open at a time (the import is
 * synchronous), so a single static handle is honest. */
typedef struct PlHandle {
    const uint8_t *buf;
    uint32_t len;
} PlHandle;

static uint8_t pl_buf[M3U_PATH_CAP * 4];  /* playlist text, RAM copy;
                                             sized 2 KB; a longer
                                             playlist is read in two
                                             passes by the chunked
                                             reader in m3u.c through
                                             this same buffer only if
                                             read() is called with
                                             advancing offsets -- see
                                             pl_read's window note. */

static void *pl_open(void *ctx, const char *path)
{
    static PlHandle h;
    int n;
    (void)ctx;
    stock_fs_acquire();
    n = stock_file_size(path);
    if (n < 0)
        return 0;
    if ((uint32_t)n > sizeof pl_buf) {
        /* The stock read caps at the buffer; m3u.c's chunked reader
         * asks for 512-byte windows at increasing offsets. A file
         * larger than the window buffer is served by re-reading the
         * whole file per window is NOT possible with the stock
         * whole-file API alone: windowed serving of >2 KB playlists
         * needs the (unpinned) seek primitive. Named limitation:
         * v1 supports playlists up to sizeof pl_buf; larger ones
         * fail open cleanly (import returns -1) rather than parse
         * garbage. */
        h.len = 0;
        h.buf = 0;
        return &h;      /* non-NULL so size() reports the true size;
                           read() below refuses out-of-window ranges */
    }
    if (stock_file_read(path, pl_buf, (uint32_t)n, 0) < 0)
        return 0;
    h.buf = pl_buf;
    h.len = (uint32_t)n;
    return &h;
}

static int pl_read(void *ctx, void *fh, uint32_t off, uint8_t *buf, uint32_t len)
{
    PlHandle *h = (PlHandle *)fh;
    uint32_t i;
    (void)ctx;
    if (!h->buf || off + len > h->len)
        return -1;
    for (i = 0; i < len; i++)
        buf[i] = h->buf[off + i];
    return 0;
}

static uint32_t pl_size(void *ctx, void *fh)
{
    (void)ctx;
    return ((PlHandle *)fh)->len;
}

static void pl_close(void *ctx, void *fh)
{
    (void)ctx;
    (void)fh;
}

/* ------------------------------------------------------------------ */
/* M3uFs over stock: stat() via the directory walker                  */
/* ------------------------------------------------------------------ */

/* Accept-everything table for the classifier at 0x0305A15C: a first
 * byte of '*' (0x2A) matches every entry unconditionally (proven),
 * so stat's walk is not limited to audio extensions. The zero entry
 * after it terminates the table. */
static const uint8_t accept_all[6] = { '*', 0, 0, 0, 0, 0 };

/*
 * Walk one directory level.
 *
 *   dir_block/cluster: the parameter block for the walker wrapper.
 *   The wrapper (0x0305A970) takes (ctx, block, table, mode); the
 *   walker's mode-3 path enumerates entries of the directory whose
 *   cluster is block+0x00, keeps a cursor at block+0x04, and writes
 *   the found entry's dirent fields to ctx +0x00 (start cluster),
 *   +0x04, +0x08 (attributes byte is at ctx +0x0B), with the entry's
 *   ordinal in the enumeration kept in the walker's match counter.
 *
 * The bridge's stat() walks component by component:
 *   for each component, enumerate the current directory with the
 *   accept-all table; for every entry, compare its 8.3 name (ctx
 *   record + name field) and, for the final component, record
 *   (clus = ctx +0x00, index = the enumeration ordinal).
 * The ordinal is definitionally the scan's index: the scan's records
 * are built from this same enumeration (m3u_design.md section 5.2).
 *
 * What is NOT yet pinned (B5): who writes block +0x08 (the directory
 * entry count the walker bounds against). Module 38's flow suggests
 * the count is established by the 0x03059F58 context init before the
 * wrapper calls; bridge_stat() therefore takes the block pre-
 * initialised by the caller, the same way module 38's stack block
 * is. The name field offset inside the walker's ctx record is the
 * second sub-pin: the mode-3 path copies an 11-byte name into the
 * record at +0x?? via 0x03054EBE (0x0305A702..708 copies a constant
 * string in one branch; entry names are handled at 0x0305A1A4's
 * record builder). bridge_stat() is therefore delivered as the
 * algorithm + vtable wiring with the two field pins named, and is
 * compiled only when BRIDGE_STAT_FIELDS is defined by the pinning
 * pass. Everything else in this file compiles without it.
 */
#ifdef BRIDGE_STAT_FIELDS
extern int bridge_walker_stat(const char *path, M3uFileInfo *out);
static int br_stat(void *ctx, const char *path, M3uFileInfo *out)
{
    (void)ctx;
    stock_fs_acquire();
    return bridge_walker_stat(path, out);
}
#else
static int br_stat(void *ctx, const char *path, M3uFileInfo *out)
{
    (void)ctx;
    (void)path;
    (void)out;
    return -1;  /* blocked: B5 + walker ctx name-field pin */
}
#endif

/* lib_count/lib_nth: iterate the post-scan node array (rooted at
 * 0x030228A8, node array 0x0307A8DC, 56-byte stride; the browser
 * reconstructs absolute paths from the node chain). At browser-open
 * time (v1) the array is populated. The chain-walk that rebuilds a
 * node's absolute path is module 31's own (its Display path); the
 * bridge version is written against the same array geometry in
 * bridge_lib.c during the pinning pass. Until then these return
 * "empty library", which makes m3u_import's stage 1 and 2 (folder-
 * relative and root-relative) work and stage 3 (library suffix
 * match) find nothing: a stated, safe degradation, not a silent
 * wrong answer. */
static uint32_t br_lib_count(void *ctx)
{
    (void)ctx;
    return 0;
}

static int br_lib_nth(void *ctx, uint32_t n, char *path_out, uint32_t cap,
                      M3uFileInfo *out)
{
    (void)ctx;
    (void)n;
    (void)path_out;
    (void)cap;
    (void)out;
    return -1;
}

static const M3uFs bridge_fs = {
    .ctx = 0,
    .open = pl_open,
    .read = pl_read,
    .size = pl_size,
    .close = pl_close,
    .stat = br_stat,
    .lib_count = br_lib_count,
    .lib_nth = br_lib_nth,
};

/* ------------------------------------------------------------------ */
/* Entry from the hook trampoline                                     */
/* ------------------------------------------------------------------ */

/* B1: build the playlist's absolute path (current directory + the
 * node's name). The node's 8.3 name at +0x4F decodes mechanically
 * (8 chars, dot, 3 chars, space-padded); the current-directory
 * prefix is the unpinned part. Returns 0 until B1 is pinned. */
static int bridge_playlist_path(void *node, void *state, char *out,
                                uint32_t cap)
{
    (void)node;
    (void)state;
    (void)out;
    (void)cap;
    return 0;   /* B1 */
}

int m3u_bridge_node_action(void *node, void *state, void *ctx)
{
    char path[M3U_PATH_CAP];
    M3uTrack tracks[STAGE_MAX_TRACKS];
    M3uStats stats;
    uint32_t i, n;

    (void)ctx;
    if (!bridge_playlist_path(node, state, path, sizeof path))
        return 0;

    if (m3u_import(&bridge_fs, path, tracks, STAGE_MAX_TRACKS, &stats) != 0)
        return 0;
    n = stats.resolved;
    if (n == 0)
        return 0;

    /* Stage the records in playlist order. +0x10..+0x18 of a browser
     * record carry the node's own fields; for a resolved library
     * file the authoritative identity is (clus, index) itself, and
     * the remaining fields are filled from the same values module 24's
     * fetch would return. Zeroing them is the conservative choice:
     * module 33's open resolves the full record by (clus, index)
     * through the same fetch the scan's records use. */
    for (i = 0; i < n; i++) {
        stage[i].clus = tracks[i].clus;
        stage[i].index = tracks[i].index;
        stage[i].f08 = 0;
        stage[i].f0c = 0;
        stage[i].f10 = 0;
        stage[i].f14 = 0;
        stage[i].f18 = 0;
    }

    /* Fill the play context the way module 31's folder-play path
     * does at 0x0307E088: source code 6 at +0xF2, total at +0x00,
     * index at +0x02. Wiring the staged array as the list the
     * player iterates is B3 (see header). */
    PLAY_CTX_TOTAL = (uint16_t)n;
    PLAY_CTX_INDEX = 0;
    PLAY_CTX_SOURCE = PLAY_SOURCE_FOLDER;
    return 1;
}
