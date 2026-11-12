/*
 * m3u_bridge.c - M3U import bridge for the DAP Neo stock firmware.
 *
 * Entered from the patch 0040 trampoline when the user activates a
 * browser node whose 8.3 extension is "M3U". The bridge registers the
 * playlist file with the stock descriptor registrar, runs the parser
 * core (m3u.c) over it through the M3uFs vtable implemented below, and
 * writes the resolver staging the resident hooks consume (packed
 * layout, m3u_bridge.h). Playback itself is served by those hooks; the
 * bridge only imports and arms.
 *
 * Filesystem model (bridge_completion.md, B1/B5 as built):
 *   - Identity is cluster-based; there are no path strings on device.
 *     The parser's path namespace is a bridge-local fiction: the first
 *     component "\x01" names the browser's current directory, any
 *     other absolute path starts at the volume root cluster.
 *   - stat() walks directories with the stock raw dirent reader
 *     0x03057F8E, the same reader 0x0305AB0A's card path counts with,
 *     applying that counter's skip rules (deleted, LFN components,
 *     hidden, volume labels) and the stock classifier 0x0305A15C
 *     against the volume accept table at 0x03005714. A file's index
 *     is its ordinal among the accepted files of its directory, the
 *     space the resolver and module 33's advance arithmetic use.
 *   - Long names: FAT LFN dirent groups preceding an entry are
 *     reassembled and matched case-folded alongside the 8.3 form.
 *     This is on-disk format handling, not a stock contract.
 *   - FS type 3 (the parsed/LFN volume kind, byte at 0x0307A024)
 *     declines the whole import: under type 3 the stock counters and
 *     the resolver take the context-based paths (0x0305AC92 /
 *     0x03059746), whose per-directory enumeration contract is not
 *     pinned by any project document. See the composition report.
 *   - The parser's stage 3 (library suffix match) is disabled:
 *     lib_count reports an empty library. No library enumeration
 *     order is pinned, and the value of stage 3 depends on the LFN
 *     forms it compares. Stages 1 and 2 are complete.
 *
 * The playlist file itself is read through the parser's own chunk
 * requests: fs->read passes (buffer, length, position) straight to
 * the stock read primitive, which is the module 37 whole-file model
 * (registrar, size query, positional reads) without a bridge-side
 * file buffer.
 *
 * Placement: linked into the module 31 segment extension payload;
 * m3u_bridge_node_action is the first symbol of the bridge section
 * (see the composition build). No heap, no libc.
 */
#include "m3u_bridge.h"

#include <stddef.h>
#include <stdint.h>

/* ---- machine seams -------------------------------------------------
 * On target these are the pinned firmware addresses. Under HOST_TEST
 * the host harness supplies equivalents so the same source runs
 * against a mock firmware layer. */
#ifdef HOST_TEST
extern uint8_t *m3u_host_stage;
extern uint32_t m3u_host_root_cluster;
extern const uint8_t *m3u_host_ctx42;
extern uint8_t m3u_host_fs_type;
extern const uint8_t *m3u_host_table;
#define STAGE_PTR      (m3u_host_stage)
#define ROOT_CLUSTER   (m3u_host_root_cluster)
#define CTX42_PTR      (m3u_host_ctx42)
#define FS_TYPE_BYTE   (m3u_host_fs_type)
#define ACCEPT_TABLE   (m3u_host_table)
#else
#define STAGE_PTR      ((uint8_t *)M3U_STAGE_BASE)
#define ROOT_CLUSTER   (*(const uint32_t *)0x0307BF58u)
#define CTX42_PTR      ((const uint8_t *)0x0307BF5Cu)
#define FS_TYPE_BYTE   (*(const uint8_t *)0x0307A024u)
#define ACCEPT_TABLE   ((const uint8_t *)0x03005714u)
#endif

/* ---- stock bindings -------------------------------------------------
 * Absolute Thumb entry points, bound as function pointers with the
 * low bit set (the lock-screen build's STOCK_FN pattern). The
 * pointers are writable storage only so the host harness can rebind
 * them; device code never writes them. Under HOST_TEST they are
 * globals for the same reason. */
#ifdef HOST_TEST
#define STOCK_FN(ret, name, addr, args) \
    ret (*name) args = (ret (*) args)((addr) | 1u)
#else
#define STOCK_FN(ret, name, addr, args) \
    static ret (*name) args = (ret (*) args)((addr) | 1u)
#endif

STOCK_FN(int, stock_registrar, 0x0305C514,
         (uint32_t dir_cluster, const uint8_t *name11, uint32_t attr));
STOCK_FN(int, stock_file_size, 0x030545D4, (int handle));
STOCK_FN(int, stock_file_read, 0x030693EA,
         (int handle, uint8_t *buf, int len, int pos));
STOCK_FN(void, stock_fs_acquire, 0x030611E0, (void));
STOCK_FN(int, stock_count_a, 0x0305AB0A,
         (uint32_t cluster, const uint8_t *table, int mode));
STOCK_FN(int, stock_count_b, 0x0305965C, (uint32_t cluster, int mode));
STOCK_FN(int, stock_dirent_read, 0x03057F8E,
         (uint8_t *buf32, uint32_t cluster, uint32_t index));
STOCK_FN(int, stock_classifier, 0x0305A15C,
         (const uint8_t *ext3, const uint8_t *table, uint32_t attr));

/* Counter mode for the card paths: the scan's own mode (module 38
 * calls the directory-stack initialiser with mode 6). Playback
 * recomputes totals against the scan database in mode 1; for an
 * unchanged card the two agree, and the card is the only side an
 * import can measure.
 *
 * Mode 6 also arms a CUE-sheet branch inside 0x0305AB0A: for a .CUE
 * entry it calls module 37's parser at 0x0307D73A, which is module 31
 * code while the browser is loaded, and passes a directory entry it has
 * marked (byte 0x0C = 0x55) to 0x0305B818 with its directory cluster
 * and index, a write back to the card. That branch is gated on "CUE" being in the
 * table the caller passes (0x0305B32C). ACCEPT_TABLE has no CUE entry,
 * so the branch is unreachable from here; never pass a table that
 * contains CUE (module 38's scan table does) to stock_count_a. */
#define COUNT_MODE 6

/* ---- bridge state --------------------------------------------------- */

typedef struct BridgeCtx {
    const uint8_t *state;      /* browser state (vtable ctx)        */
    uint32_t cur_cluster;      /* browser's current directory       */
    int handle;                /* registrar handle of the playlist  */
    char pl_name[13];          /* playlist file name, text form     */
} BridgeCtx;

/* Writable state. The payload is a plain byte copy with no loader,
 * so every writable byte must ride inside the image as .data: each
 * object below carries a nonzero initializer (an all-zero or absent
 * initializer would land in .bss and be lost). The values are inert;
 * node_action resets the log state before any use, and the parser
 * overwrites the dummy track's fields it writes. */
static BridgeCtx g_ctx = { .handle = -1 };

/* Resolution log. stat() records each entry the parser resolves
 * straight into the staging span, in resolution order: the folder
 * goes into the run cluster array (first-use order) and the entry
 * word into the entry array. The flag byte is cleared before the
 * parser runs, so the hooks never read the span while it fills.
 * stat_path() in m3u.c issues exactly one fs->stat per resolution
 * attempt and accepts exactly when stat returns 0 for a non-directory,
 * so the entries stay aligned with the parser's track order by
 * construction. */
static uint32_t g_log_count = 1;    /* reset to 0 at entry */
static uint32_t g_log_runs = 1;     /* reset to 0 at entry */
static int g_log_overflow = 1;      /* reset to 0 at entry */

static M3uTrack g_dummy_track = { .duration_s = -1 };
                                    /* parser out[] sink; the log is
                                       the record the bridge uses   */

/* ---- small helpers -------------------------------------------------- */

static uint32_t get_u32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static void put_u16(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

static void put_u32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

static uint32_t fold_cp(uint32_t cp)
{
    if (cp >= 'A' && cp <= 'Z') {
        return cp + 32u;
    }
    if (cp >= 0xC0u && cp <= 0xDEu && cp != 0xD7u) {
        return cp + 32u;
    }
    return cp;
}

/* Decode one UTF-8 code point; returns 0 and consumes 1 byte on
 * malformed input (which then simply fails to match). */
static uint32_t utf8_next(const uint8_t *s, uint32_t len, uint32_t *used)
{
    uint8_t c = s[0];
    if (c < 0x80u) {
        *used = 1;
        return c;
    }
    if ((c & 0xE0u) == 0xC0u && len >= 2) {
        *used = 2;
        return ((uint32_t)(c & 0x1Fu) << 6) | (uint32_t)(s[1] & 0x3Fu);
    }
    if ((c & 0xF0u) == 0xE0u && len >= 3) {
        *used = 3;
        return ((uint32_t)(c & 0x0Fu) << 12) |
               ((uint32_t)(s[1] & 0x3Fu) << 6) | (uint32_t)(s[2] & 0x3Fu);
    }
    if ((c & 0xF8u) == 0xF0u && len >= 4) {
        *used = 4;
        return ((uint32_t)(c & 0x07u) << 18) |
               ((uint32_t)(s[1] & 0x3Fu) << 12) |
               ((uint32_t)(s[2] & 0x3Fu) << 6) | (uint32_t)(s[3] & 0x3Fu);
    }
    *used = 1;
    return 0;
}

/* ---- directory enumeration ------------------------------------------ */

/* Convert only exact ASCII FAT short names. Never truncate or discard
 * characters: a long playlist component must match its real LFN. */
static int sfn_form(const uint8_t *comp, uint32_t len, uint8_t out[11])
{
    uint32_t i, pos = 0, limit = 8;
    if (!len) return 0;
    for (i = 0; i < 11; i++) out[i] = ' ';
    for (i = 0; i < len; i++) {
        uint8_t c = comp[i];
        if (c == '.') {
            if (limit != 8 || pos == 0 || i + 1 == len) return 0;
            pos = 8;
            limit = 11;
            continue;
        }
        /* FAT short names cannot contain spaces, control or punctuation
         * with reserved directory/path meanings. Treat non-ASCII as LFN. */
        if (c <= 0x20 || c >= 0x7f || c == '"' || c == '*' ||
            c == '+' || c == ',' || c == '/' || c == ':' || c == ';' ||
            c == '<' || c == '=' || c == '>' || c == '?' || c == '[' ||
            c == '\\' || c == ']' || c == '|') return 0;
        if (pos >= limit) return 0;
        if (c >= 'a' && c <= 'z') c = (uint8_t)(c - 'a' + 'A');
        out[pos++] = c;
    }
    return 1;
}

static uint8_t sfn_checksum(const uint8_t *name11)
{
    uint8_t sum = 0;
    int i;
    for (i = 0; i < 11; i++) {
        sum = (uint8_t)(((sum & 1u) << 7) + (sum >> 1) + name11[i]);
    }
    return sum;
}

static int lfn_match(const uint8_t *comp, uint32_t len,
                     const uint16_t *lfn, uint32_t lfn_len)
{
    uint32_t pos = 0;
    uint32_t k = 0;
    while (pos < len) {
        uint32_t used;
        uint32_t cp = utf8_next(comp + pos, len - pos, &used);
        pos += used;
        if (cp > 0xFFFFu) {
            /* FAT stores a code point past the BMP as a UTF-16
             * surrogate pair: two LFN units for one UTF-8 sequence. */
            if (k + 1u >= lfn_len ||
                lfn[k] != (uint16_t)(0xD800u + ((cp - 0x10000u) >> 10)) ||
                lfn[k + 1u] != (uint16_t)(0xDC00u + (cp & 0x3FFu))) {
                return 0;
            }
            k += 2u;
            continue;
        }
        if (k >= lfn_len) {
            return 0;
        }
        if (fold_cp(cp) != fold_cp(lfn[k])) {
            return 0;
        }
        k++;
    }
    return k == lfn_len;
}

typedef struct DirHit {
    int found;
    int is_dir;
    uint32_t entry_clus;   /* directory entries: the directory cluster */
    uint32_t ordinal;      /* file entries: accepted-file ordinal      */
} DirHit;

/* Find one component inside one directory, in raw dirent order.
 * Mirrors the stock count loops' skip rules exactly: end at a zero
 * first byte, skip deleted (0xE5), LFN components (0x0F, reassembled
 * for matching), hidden (attr 0x02) and volume labels (attr 0x08);
 * files count toward the ordinal only when the classifier accepts
 * them, and a name that matches an unaccepted file does not resolve. */
static DirHit find_in_dir(uint32_t cluster, const uint8_t *comp,
                          uint32_t len)
{
    DirHit hit;
    uint8_t de[32];
    uint8_t want[11];
    uint32_t idx = 0;
    uint32_t ordinal = 0;
    uint16_t lfn[256];
    uint32_t lfn_len = 0;
    int lfn_live = 0;
    uint8_t lfn_sum = 0;
    uint32_t lfn_next = 0;
    int have_sfn;

    hit.found = 0;
    hit.is_dir = 0;
    hit.entry_clus = 0;
    hit.ordinal = 0;
    have_sfn = sfn_form(comp, len, want);

    for (;;) {
        uint8_t first;
        uint8_t attr;
        if (stock_dirent_read(de, cluster, idx) != 0) {
            return hit;                 /* read error: treat as end */
        }
        idx++;
        first = de[0];
        if (first == 0) {
            return hit;                 /* end of directory */
        }
        if (first == 0xE5u) {
            lfn_live = 0;
            continue;                   /* deleted */
        }
        attr = de[0x0B];
        if (attr == 0x0Fu) {            /* LFN component */
            uint32_t seq = de[0] & 0x1Fu;
            uint32_t base, j;
            if ((de[0] & 0xA0u) || seq == 0u || seq > 20u ||
                de[12] != 0 || de[26] != 0 || de[27] != 0) {
                lfn_live = 0;
                continue;
            }
            base = (seq - 1u) * 13u;
            if (de[0] & 0x40u) {
                lfn_live = 1;
                lfn_sum = de[13];
                lfn_next = seq;
                lfn_len = base + 13u;
                for (j = 0; j < 13u; j++) {
                    uint32_t off = (j < 5u) ? (1u + 2u * j)
                                 : (j < 11u) ? (14u + 2u * (j - 5u))
                                             : (28u + 2u * (j - 11u));
                    uint16_t ch = (uint16_t)(de[off] |
                                             ((uint16_t)de[off + 1] << 8));
                    if (ch == 0 || ch == 0xFFFFu) {
                        lfn_len = base + j;
                        break;
                    }
                }
                /* 255 UTF-16 code units is the FAT LFN maximum. */
                if (lfn_len > 255u) lfn_live = 0;
            }
            if (!lfn_live || seq != lfn_next || de[13] != lfn_sum) {
                lfn_live = 0;
                continue;
            }
            for (j = 0; j < 13u && base + j < 256u; j++) {
                uint32_t off = (j < 5u) ? (1u + 2u * j)
                             : (j < 11u) ? (14u + 2u * (j - 5u))
                                         : (28u + 2u * (j - 11u));
                lfn[base + j] = (uint16_t)(de[off] |
                                           ((uint16_t)de[off + 1] << 8));
            }
            lfn_next--;
            continue;
        }
        /* a real entry: any pending LFN belongs to it */
        {
            int have_lfn = lfn_live && lfn_next == 0u && lfn_len != 0u &&
                           lfn_sum == sfn_checksum(de);
            int matched;
            lfn_live = 0;
            if ((attr & 0x02u) || (attr & 0x08u)) {
                continue;               /* hidden / volume label */
            }
            matched = 0;
            {
                uint32_t k;
                int same = have_sfn;
                for (k = 0; same && k < 11u; k++) {
                    if (de[k] != want[k]) {
                        same = 0;
                        break;
                    }
                }
                matched = same;
            }
            if (!matched && have_lfn) {
                matched = lfn_match(comp, len, lfn, lfn_len);
            }
            if (attr & 0x10u) {         /* directory */
                if (matched) {
                    hit.found = 1;
                    hit.is_dir = 1;
                    hit.entry_clus = (uint32_t)de[0x1A] |
                                     ((uint32_t)de[0x1B] << 8) |
                                     ((uint32_t)de[0x14] << 16) |
                                     ((uint32_t)de[0x15] << 24);
                    return hit;
                }
                continue;
            }
            /* file */
            if (stock_classifier(de + 8, ACCEPT_TABLE, attr) == 0) {
                if (matched) {
                    return hit;         /* named but not playable */
                }
                continue;
            }
            if (matched) {
                hit.found = 1;
                hit.is_dir = 0;
                hit.ordinal = ordinal;
                return hit;
            }
            ordinal++;
        }
    }
}

/* ---- M3uFs implementation -------------------------------------------- */

static void *bridge_open(void *vctx, const char *path)
{
    BridgeCtx *b = (BridgeCtx *)vctx;
    const char *last = path;
    const char *p;
    uint32_t i = 0;
    /* The only file the parser opens is the playlist itself, already
     * registered in node_action. Verify the final component is the
     * playlist's text name, then hand back the bound token. */
    for (p = path; *p != '\0'; p++) {
        if (*p == '/') {
            last = p + 1;
        }
    }
    while (last[i] != '\0' && b->pl_name[i] != '\0') {
        uint8_t a = (uint8_t)last[i];
        uint8_t c = (uint8_t)b->pl_name[i];
        if (a >= 'a' && a <= 'z') {
            a = (uint8_t)(a - 'a' + 'A');
        }
        if (c >= 'a' && c <= 'z') {
            c = (uint8_t)(c - 'a' + 'A');
        }
        if (a != c) {
            return NULL;
        }
        i++;
    }
    if (last[i] != '\0' || b->pl_name[i] != '\0') {
        return NULL;
    }
    return (void *)b;                   /* token: the ctx itself */
}

static int bridge_read(void *vctx, void *fh, uint32_t off, uint8_t *buf,
                       uint32_t len)
{
    BridgeCtx *b = (BridgeCtx *)vctx;
    (void)fh;
    return stock_file_read(b->handle, buf, (int)len, (int)off);
}

static uint32_t bridge_size(void *vctx, void *fh)
{
    BridgeCtx *b = (BridgeCtx *)vctx;
    int n;
    (void)fh;
    n = stock_file_size(b->handle);
    return n < 0 ? 0u : (uint32_t)n;
}

static void bridge_close(void *vctx, void *fh)
{
    (void)vctx;
    (void)fh;
    /* No stock close primitive is pinned; descriptor slots are the
     * device manager's fixed pool and module 37's model never closes. */
}

/* Append one resolved entry to the staging span. Any cap (entries,
 * runs, or an ordinal too large for the entry word) sets the overflow
 * flag, and node_action then declines the whole import. */
static void log_entry(uint32_t clus, uint32_t ordinal)
{
    uint8_t *stage = STAGE_PTR;
    uint32_t id;
    if (g_log_count >= M3U_STAGE_MAX_ENT || ordinal > M3U_STAGE_MAX_ORD) {
        g_log_overflow = 1;
        return;
    }
    for (id = 0; id < g_log_runs; id++) {
        if (get_u32(stage + M3U_STAGE_CLUS_OFF + 4u * id) == clus) {
            break;
        }
    }
    if (id == g_log_runs) {
        if (g_log_runs >= M3U_STAGE_MAX_RUNS) {
            g_log_overflow = 1;
            return;
        }
        put_u32(stage + M3U_STAGE_CLUS_OFF + 4u * id, clus);
        g_log_runs++;
    }
    put_u16(stage + M3U_STAGE_ENT_OFF + 2u * g_log_count,
            ordinal | (id << M3U_STAGE_ORD_BITS));
    g_log_count++;
}

#define STAT_MAX_DEPTH 16

static int bridge_stat(void *vctx, const char *path, M3uFileInfo *out)
{
    BridgeCtx *b = (BridgeCtx *)vctx;
    const uint8_t *s = (const uint8_t *)path;
    uint32_t stack[STAT_MAX_DEPTH];     /* ancestor clusters */
    int sp = 0;                         /* ancestors pushed so far */
    uint32_t cur;

    /* Start directory: the sentinel component selects the browser's
     * current directory; anything else starts at the volume root.
     * Paths are absolute, so skip the leading separator first. */
    if (*s == '/') {
        s++;
    }
    {
        const uint8_t *e = s;
        while (*e != '\0' && *e != '/') {
            e++;
        }
        if ((uint32_t)(e - s) == 1u && s[0] == 0x01u) {
            cur = b->cur_cluster;
            s = (*e == '/') ? e + 1 : e;
        } else {
            cur = ROOT_CLUSTER;
        }
    }

    for (;;) {
        const uint8_t *e = s;
        uint32_t len;
        int last;
        while (*e != '\0' && *e != '/') {
            e++;
        }
        len = (uint32_t)(e - s);
        last = (*e == '\0');
        if (len == 0) {                 /* empty component */
            if (last) {
                break;
            }
            s = e + 1;
            continue;
        }
        if (len == 1u && s[0] == '.') {
            if (last) {
                break;
            }
            s = e + 1;
            continue;
        }
        if (len == 2u && s[0] == '.' && s[1] == '.') {
            if (sp == 0) {
                return -1;              /* above the start directory */
            }
            cur = stack[--sp];
            if (last) {
                break;
            }
            s = e + 1;
            continue;
        }
        {
            DirHit hit = find_in_dir(cur, s, len);
            if (!hit.found) {
                return -1;
            }
            if (!last) {
                if (!hit.is_dir) {
                    return -1;
                }
                if (sp >= STAT_MAX_DEPTH) {
                    return -1;
                }
                stack[sp++] = cur;      /* push the directory left */
                cur = hit.entry_clus;
                s = e + 1;
                continue;
            }
            /* final component */
            if (hit.is_dir) {
                out->clus = hit.entry_clus;
                out->index = 0;
                out->is_dir = true;
                return 0;
            }
            out->clus = cur;
            out->index = hit.ordinal;
            out->is_dir = false;
            log_entry(cur, hit.ordinal);
            return 0;
        }
    }
    /* The path names the start directory itself. */
    out->clus = cur;
    out->index = 0;
    out->is_dir = true;
    return 0;
}

static uint32_t bridge_lib_count(void *vctx)
{
    (void)vctx;
    return 0;                           /* stage 3 disabled, see header */
}

static int bridge_lib_nth(void *vctx, uint32_t n, char *path_out,
                          uint32_t cap, M3uFileInfo *out)
{
    (void)vctx;
    (void)n;
    (void)path_out;
    (void)cap;
    (void)out;
    return -1;
}

static const M3uFs g_fs = {
    NULL,           /* ctx, bound at import time */
    bridge_open,
    bridge_read,
    bridge_size,
    bridge_close,
    bridge_stat,
    bridge_lib_count,
    bridge_lib_nth
};

/* ---- staging writer ---------------------------------------------------- */

/* Complete the staging stat() filled: the shared context, each run's
 * folder total, then the header, and the flag byte last. Returns 1 on
 * success; if a counter fails or a total does not fit, returns 0 with
 * the flag still clear, so the hooks ignore the partial table and the
 * file opens with stock behaviour. */
static int write_staging(void)
{
    uint8_t *stage = STAGE_PTR;
    uint32_t id;
    int j;

    for (j = 0; j < (int)M3U_STAGE_CTX_LEN; j++) {
        stage[M3U_STAGE_CTX_OFF + j] = CTX42_PTR[j];
    }
    stage[M3U_STAGE_CTX_OFF + M3U_STAGE_CTX_LEN] = 0;
    stage[M3U_STAGE_CTX_OFF + M3U_STAGE_CTX_LEN + 1] = 0;
    for (id = 0; id < g_log_runs; id++) {
        uint32_t clus = get_u32(stage + M3U_STAGE_CLUS_OFF + 4u * id);
        int ca = stock_count_a(clus, ACCEPT_TABLE, COUNT_MODE);
        int cb = stock_count_b(clus, COUNT_MODE);
        if (ca < 0 || cb < 0 || ca + cb > 0xFFFF) {
            return 0;
        }
        put_u16(stage + M3U_STAGE_SUM_OFF + 2u * id, (uint32_t)(ca + cb));
    }
    stage[1] = (uint8_t)g_log_count;
    put_u16(stage + 2, 0xFFFFu);        /* current position: none */
    put_u16(stage + 4, 0);              /* last served ordinal */
    stage[6] = (uint8_t)g_log_runs;
    for (j = 7; j < (int)M3U_STAGE_HDR_LEN; j++) {
        stage[j] = 0;
    }
    stage[0] = 1;                       /* flag last: table complete */
    return 1;
}

/* ---- entry point -------------------------------------------------------- */

__attribute__((section(".text.entry"), used))
int m3u_bridge_node_action(const uint8_t *node, const uint8_t *state,
                           const uint8_t *ctx)
{
    uint8_t *stage = STAGE_PTR;
    uint32_t level;
    const uint8_t *rec;
    int handle;
    char pl_path[20];
    M3uFs fs;
    M3uStats stats;
    uint32_t i;
    int o;

    (void)ctx;
    g_log_count = 0;
    g_log_runs = 0;
    g_log_overflow = 0;

    /* Disarm an earlier playlist even if this volume is unsupported;
     * otherwise the resident resolver could serve stale entries. */
    stage[0] = 0;
    /* FS type 3 declines: its enumeration contract is unpinned (see
     * the file header). */
    if (FS_TYPE_BYTE == 3u) {
        return 0;
    }

    /* The playlist's parent directory is the browser's current one:
     * level record at state + 56*level, cluster at rec+0x14. */
    level = state[0x1CC];
    rec = state + 56u * level;
    g_ctx.state = state;
    g_ctx.cur_cluster = get_u32(rec + 0x14);

    /* Register the playlist file itself: directory cluster, the
     * node's 11-byte name at node+0x4F, its attribute byte at
     * node+0x5A (the dirent copy the node embeds at +0x4F, attr at
     * +0x0B within it). */
    stock_fs_acquire();
    handle = stock_registrar(g_ctx.cur_cluster, node + 0x4F, node[0x5A]);
    if (handle < 0) {
        return 0;
    }
    g_ctx.handle = handle;

    /* Text form of the name, for the parser's path namespace. */
    o = 0;
    for (i = 0; i < 8u; i++) {
        uint8_t c = node[0x4F + i];
        if (c == ' ') {
            break;
        }
        g_ctx.pl_name[o++] = (char)c;
    }
    if (node[0x57] != ' ') {
        g_ctx.pl_name[o++] = '.';
        for (i = 0; i < 3u; i++) {
            uint8_t c = node[0x57 + i];
            if (c == ' ') {
                break;
            }
            g_ctx.pl_name[o++] = (char)c;
        }
    }
    g_ctx.pl_name[o] = '\0';

    /* playlist_path in the bridge namespace: "/<sentinel>/<name>". */
    pl_path[0] = '/';
    pl_path[1] = '\x01';
    pl_path[2] = '/';
    for (i = 0; g_ctx.pl_name[i] != '\0'; i++) {
        pl_path[3 + i] = g_ctx.pl_name[i];
    }
    pl_path[3 + i] = '\0';

    fs = g_fs;
    fs.ctx = &g_ctx;
    if (m3u_import(&fs, pl_path, &g_dummy_track, 1, &stats) != 0) {
        return 0;
    }
    if (g_log_overflow || g_log_count == 0) {
        return 0;
    }
    /* Alignment invariant: one log entry per entry the parser
     * resolved and wrote or overflowed. A mismatch means the stat
     * contract drifted; decline rather than stage a wrong table. */
    if (g_log_count != stats.resolved + stats.overflow) {
        return 0;
    }
    return write_staging();
}

