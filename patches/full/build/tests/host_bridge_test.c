/*
 * host_bridge_test.c - host exercise of the completed M3U bridge
 * (src/m3u_bridge.c, compiled with HOST_TEST) against a mock firmware
 * layer and a fake FAT tree.
 *
 * The mocks replace the eight stock bindings: registrar, file size,
 * file read, FS acquire, the two directory counters, the raw dirent
 * reader and the classifier (the classifier mock runs the real accept
 * table bytes read from the stock image, MP1..DSF). The dirent reader
 * serves programmatic dirent streams built from the fake tree,
 * including LFN dirent groups, a deleted entry, a hidden file and a
 * volume label.
 *
 * Scenario 1 imports a nine-entry playlist from the fake MUSIC
 * directory and checks the staging bytes field by field against the
 * packed layout in m3u_bridge.h, with every expected count and ordinal
 * derived by hand from the tree (see the tree comments). Scenario 2
 * checks the FS-type-3 decline clears an old playlist flag. Scenario 3
 * checks that an import needing 33 folder runs declines with the flag
 * clear, and scenario 5 that 32 runs (the cap) arm. Scenario 4 checks
 * a playlist with no resolvable entries declines. Scenario 6 checks
 * the entry cap: 150 entries arm, 151 decline. Scenario 7 imports a
 * .m3u8 playlist through its 8.3 alias (EVENIN~1.M3U for
 * "Evening.m3u8"): UTF-8 with a BOM, CRLF line ends, a Windows drive
 * path, an LFN entry, and a long name holding a code point past the
 * BMP (stored as a surrogate pair) plus a case-folded accent.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "m3u.h"
#include "m3u_bridge.h"

/* ---- HOST_TEST seams (declared extern in m3u_bridge.c) ------------- */

static uint8_t stage_buf[M3U_STAGE_TOTAL];
uint8_t *m3u_host_stage = stage_buf;
uint32_t m3u_host_root_cluster = 0x0002u;
static uint8_t ctx42_pattern[42];
const uint8_t *m3u_host_ctx42 = ctx42_pattern;
uint8_t m3u_host_fs_type = 1;
/* the stock accept table at 0x03005714, byte for byte */
static const uint8_t table_bytes[42] = {
    'M', 'P', '1', 'M', 'P', '2', 'M', 'P', '3', 'W', 'M', 'A',
    'W', 'A', 'V', 'A', 'P', 'E', 'F', 'L', 'A', 'A', 'A', 'C',
    'M', '4', 'A', 'O', 'G', 'G', 'M', 'P', '4', '3', 'G', 'P',
    'D', 'F', 'F', 'D', 'S', 'F'
};
const uint8_t *m3u_host_table = table_bytes;

/* stock bindings the bridge TU exposes under HOST_TEST */
extern int (*stock_registrar)(uint32_t, const uint8_t *, uint32_t);
extern int (*stock_file_size)(int);
extern int (*stock_file_read)(int, uint8_t *, int, int);
extern void (*stock_fs_acquire)(void);
extern int (*stock_count_a)(uint32_t, const uint8_t *, int);
extern int (*stock_count_b)(uint32_t, int);
extern int (*stock_dirent_read)(uint8_t *, uint32_t, uint32_t);
extern int (*stock_classifier)(const uint8_t *, const uint8_t *, uint32_t);

/* ---- fake FAT tree ---------------------------------------------------- */

typedef struct FakeEnt {
    char sfn[12];          /* 11 bytes + NUL */
    uint8_t attr;
    uint32_t clus;
    int deleted;
    const char *lfn;       /* NULL, or the long name */
} FakeEnt;

typedef struct FakeDir {
    uint32_t clus;
    const FakeEnt *ents;
    int n;
} FakeDir;

#define E(sfn, attr, clus)            { sfn, attr, clus, 0, NULL }
#define ED(sfn, attr, clus)           { sfn, attr, clus, 1, NULL }
#define EL(sfn, attr, clus, lfn)      { sfn, attr, clus, 0, lfn }

/* Root: accepted files ROOT1.MP3 (ordinal 0) and the LFN file
 * (ordinal 1); two subdirectories; one deleted file; one volume
 * label. countA = 2, countB = 2. */
static const FakeEnt root_ents[] = {
    E("NO NAME    ", 0x08, 0),
    E("MUSIC      ", 0x10, 0x1001),
    E("ROOT1   MP3", 0x20, 0x5001),
    ED("GONE    MP3", 0x20, 0x5002),
    EL("LONGFI~1FLA", 0x20, 0x5003, "Long File Name.flac"),
    E("PODCAST    ", 0x10, 0x1002)
};
/* MUSIC (the browser's current directory): the playlist itself (M3U
 * is not in the accept table, so it takes no ordinal), SONG1.MP3
 * ordinal 0, SONG2.WAV hidden (skipped entirely), NOTES.TXT not
 * accepted, TRACK3.FLA ordinal 1, one subdirectory.
 * countA = 2, countB = 1. */
static const FakeEnt music_ents[] = {
    E("TEST    M3U", 0x20, 0x6001),
    E("SONG1   MP3", 0x20, 0x6002),
    E("SONG2   WAV", 0x22, 0x6003),
    E("LIVE       ", 0x10, 0x1003),
    E("NOTES   TXT", 0x20, 0x6004),
    E("TRACK3  FLA", 0x20, 0x6005)
};
/* LIVE: SET1.MP3 ordinal 0, SET2.MP3 ordinal 1. countA = 2, countB = 0. */
static const FakeEnt live_ents[] = {
    E("SET1    MP3", 0x20, 0x6101),
    E("SET2    MP3", 0x20, 0x6102)
};
/* PODCAST: EP1.MP3 ordinal 0, and an LFN file whose name holds a
 * code point past the BMP (headphones emoji) and an accented letter,
 * ordinal 1. countA = 2, countB = 0. */
static const FakeEnt podcast_ents[] = {
    E("EP1     MP3", 0x20, 0x6201),
    EL("EP2~1   MP3", 0x20, 0x6202, "Ep 2 \xF0\x9F\x8E\xA7 Caf\xC3\xA9.mp3")
};

static const FakeDir dirs1[] = {
    { 0x0002, root_ents, 6 },
    { 0x1001, music_ents, 6 },
    { 0x1003, live_ents, 2 },
    { 0x1002, podcast_ents, 2 }
};

/* Scenario 3 and 5 tree: MUSIC with TREE3_DIRS subdirectories D00..,
 * each with one A.MP3. Filled in by init_tree3(). */
#define TREE3_DIRS 33
static FakeEnt music3_ents[TREE3_DIRS];
static FakeEnt sub3_ents[TREE3_DIRS][1];
static FakeDir dirs3[TREE3_DIRS + 2];
static char sub3_names[TREE3_DIRS][12];

static const FakeDir *g_dirs;
static int g_ndirs;

static const FakeDir *find_dir(uint32_t clus)
{
    int i;
    for (i = 0; i < g_ndirs; i++) {
        if (g_dirs[i].clus == clus) {
            return &g_dirs[i];
        }
    }
    return NULL;
}

/* ---- mock stock primitives --------------------------------------------- */

static const char *g_playlist;
static int g_registrar_calls;
static uint32_t g_reg_dir;
static uint8_t g_reg_name[11];
static uint32_t g_reg_attr;
static int g_acquire_calls;

static int mock_registrar(uint32_t dir_cluster, const uint8_t *name11,
                          uint32_t attr)
{
    g_registrar_calls++;
    g_reg_dir = dir_cluster;
    memcpy(g_reg_name, name11, 11);
    g_reg_attr = attr;
    if (memcmp(name11, "TEST    M3U", 11) != 0 &&
        memcmp(name11, "BIG     M3U", 11) != 0 &&
        memcmp(name11, "EMPTY   M3U", 11) != 0 &&
        memcmp(name11, "CAP     M3U", 11) != 0 &&
        memcmp(name11, "LONG    M3U", 11) != 0 &&
        memcmp(name11, "EVENIN~1M3U", 11) != 0) {
        return -1;
    }
    return 5;
}

static int mock_size(int handle)
{
    (void)handle;
    return (int)strlen(g_playlist);
}

static int mock_read(int handle, uint8_t *buf, int len, int pos)
{
    int total = (int)strlen(g_playlist);
    int n;
    (void)handle;
    if (pos >= total) {
        return 0;
    }
    n = total - pos;
    if (n > len) {
        n = len;
    }
    memcpy(buf, g_playlist + pos, (size_t)n);
    return n;
}

static void mock_acquire(void)
{
    g_acquire_calls++;
}

static int mock_classifier(const uint8_t *ext3, const uint8_t *table,
                           uint32_t attr)
{
    int i;
    if (attr & 0x18u) {
        return 0;
    }
    for (i = 0; i < 14; i++) {
        if (memcmp(ext3, table + 3 * i, 3) == 0) {
            return 1;
        }
    }
    return 0;
}

static int mock_count_a(uint32_t cluster, const uint8_t *table, int mode)
{
    const FakeDir *d = find_dir(cluster);
    int i;
    int n = 0;
    (void)mode;
    if (d == NULL) {
        return -1;
    }
    for (i = 0; i < d->n; i++) {
        const FakeEnt *e = &d->ents[i];
        if (e->deleted || (e->attr & 0x02u) || (e->attr & 0x18u)) {
            continue;
        }
        if (mock_classifier((const uint8_t *)e->sfn + 8, table, e->attr)) {
            n++;
        }
    }
    return n;
}

static int mock_count_b(uint32_t cluster, int mode)
{
    const FakeDir *d = find_dir(cluster);
    int i;
    int n = 0;
    (void)mode;
    if (d == NULL) {
        return -1;
    }
    for (i = 0; i < d->n; i++) {
        const FakeEnt *e = &d->ents[i];
        if (!e->deleted && (e->attr & 0x10u)) {
            n++;
        }
    }
    return n;
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

/* Long names in the fake tree are UTF-8; FAT stores UTF-16 units,
 * with a surrogate pair for a code point past the BMP. */
static int utf8_to_utf16(const char *in, uint16_t *out)
{
    const uint8_t *p = (const uint8_t *)in;
    int n = 0;
    while (*p) {
        uint32_t cp;
        if (p[0] < 0x80u) {
            cp = *p++;
        } else if ((p[0] & 0xE0u) == 0xC0u) {
            cp = ((uint32_t)(p[0] & 0x1Fu) << 6) | (p[1] & 0x3Fu);
            p += 2;
        } else if ((p[0] & 0xF0u) == 0xE0u) {
            cp = ((uint32_t)(p[0] & 0x0Fu) << 12) |
                 ((uint32_t)(p[1] & 0x3Fu) << 6) | (p[2] & 0x3Fu);
            p += 3;
        } else {
            cp = ((uint32_t)(p[0] & 0x07u) << 18) |
                 ((uint32_t)(p[1] & 0x3Fu) << 12) |
                 ((uint32_t)(p[2] & 0x3Fu) << 6) | (p[3] & 0x3Fu);
            p += 4;
        }
        if (cp > 0xFFFFu) {
            out[n++] = (uint16_t)(0xD800u + ((cp - 0x10000u) >> 10));
            out[n++] = (uint16_t)(0xDC00u + (cp & 0x3FFu));
        } else {
            out[n++] = (uint16_t)cp;
        }
    }
    return n;
}

/* One fake directory as a raw dirent stream: each entry expands to
 * its LFN dirents (reverse order, flagged last part first) plus its
 * SFN dirent; the stream ends with a zero dirent. */
typedef struct StreamEnt {
    uint8_t de[32];
} StreamEnt;

static StreamEnt g_stream[64];
static int g_stream_len;
static uint32_t g_stream_clus;

static void build_stream(const FakeDir *d)
{
    int i;
    int o = 0;
    for (i = 0; i < d->n; i++) {
        const FakeEnt *e = &d->ents[i];
        if (e->lfn != NULL) {
            uint16_t units[256];
            int chars = utf8_to_utf16(e->lfn, units);
            int parts = (chars + 13) / 13;
            int p;
            for (p = parts; p >= 1; p--) {
                uint8_t *de = g_stream[o++].de;
                int j;
                memset(de, 0, 32);
                de[0] = (uint8_t)(p | (p == parts ? 0x40 : 0));
                de[11] = 0x0F;
                de[13] = sfn_checksum((const uint8_t *)e->sfn);
                for (j = 0; j < 13; j++) {
                    int ci = (p - 1) * 13 + j;
                    uint16_t ch = 0xFFFFu;
                    if (ci < chars) {
                        ch = units[ci];
                    } else if (ci == chars) {
                        ch = 0;
                    }
                    {
                        int off = (j < 5) ? (1 + 2 * j)
                                : (j < 11) ? (14 + 2 * (j - 5))
                                           : (28 + 2 * (j - 11));
                        de[off] = (uint8_t)ch;
                        de[off + 1] = (uint8_t)(ch >> 8);
                    }
                }
            }
        }
        {
            uint8_t *de = g_stream[o++].de;
            memset(de, 0, 32);
            memcpy(de, e->sfn, 11);
            if (e->deleted) {
                de[0] = 0xE5;
            }
            de[11] = e->attr;
            de[0x14] = (uint8_t)(e->clus >> 16);
            de[0x15] = (uint8_t)(e->clus >> 24);
            de[0x1A] = (uint8_t)e->clus;
            de[0x1B] = (uint8_t)(e->clus >> 8);
        }
    }
    memset(g_stream[o++].de, 0, 32);    /* end marker */
    g_stream_len = o;
}

static int mock_dirent_read(uint8_t *buf32, uint32_t cluster,
                            uint32_t index)
{
    const FakeDir *d;
    if (cluster != g_stream_clus) {
        d = find_dir(cluster);
        if (d == NULL) {
            return -1;
        }
        build_stream(d);
        g_stream_clus = cluster;
    }
    if (index >= (uint32_t)g_stream_len) {
        return -1;
    }
    memcpy(buf32, g_stream[index].de, 32);
    return 0;
}

/* ---- checks -------------------------------------------------------------- */

static int failures;

#define CHECK(cond) do { \
        if (!(cond)) { \
            printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
            failures++; \
        } \
    } while (0)

static uint16_t rd16(const uint8_t *p)
{
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}

static uint32_t rd32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static void check_ctx(void)
{
    int j;
    for (j = 0; j < 42; j++) {
        CHECK(stage_buf[M3U_STAGE_CTX_OFF + j] == ctx42_pattern[j]);
    }
    CHECK(stage_buf[M3U_STAGE_CTX_OFF + 42] == 0);
    CHECK(stage_buf[M3U_STAGE_CTX_OFF + 43] == 0);
}

static void check_run(int id, uint32_t clus, int ca, int cb)
{
    CHECK(rd32(stage_buf + M3U_STAGE_CLUS_OFF + 4 * id) == clus);
    CHECK(rd16(stage_buf + M3U_STAGE_SUM_OFF + 2 * id) ==
          (uint16_t)(ca + cb));
}

static void check_entry(int i, int idx, int run)
{
    uint16_t w = rd16(stage_buf + M3U_STAGE_ENT_OFF + 2 * i);
    CHECK((w & 0x07FFu) == (uint16_t)idx);
    CHECK((w >> 11) == (uint16_t)run);
}

/* Build a fake browser node + state pair. level 2, current directory
 * cluster `cur`. The node embeds the playlist dirent at +0x4F. */
static void make_node_state(uint8_t *node, uint8_t *state, uint32_t cur,
                            const char *pl_sfn)
{
    memset(node, 0, 0x80);
    memset(state, 0, 0x400);
    memcpy(node + 0x4F, pl_sfn, 11);
    node[0x5A] = 0x20;
    state[0x1CC] = 2;
    {
        uint8_t *rec = state + 56 * 2;
        rec[0x14] = (uint8_t)cur;
        rec[0x15] = (uint8_t)(cur >> 8);
        rec[0x16] = (uint8_t)(cur >> 16);
        rec[0x17] = (uint8_t)(cur >> 24);
    }
}

static const char playlist1[] =
    "#EXTM3U\n"
    "#EXTINF:120,Someone - Song One\n"
    "SONG1.MP3\n"
    "LIVE/SET2.MP3\n"
    "/ROOT1.MP3\n"
    "Long File Name.flac\n"
    "../PODCAST/EP1.MP3\n"
    "MISSING.MP3\n"
    "SONG1.MP3\n"
    "track3.fla\n"
    "SONG2.WAV\n";

static void init_tree3(void)
{
    int i;
    for (i = 0; i < TREE3_DIRS; i++) {
        char *nm = sub3_names[i];
        memset(nm, ' ', 11);
        nm[11] = '\0';
        nm[0] = 'D';
        nm[1] = (char)('0' + i / 10);
        nm[2] = (char)('0' + i % 10);
        music3_ents[i].attr = 0x10;
        music3_ents[i].clus = 0x2000u + (uint32_t)i;
        music3_ents[i].deleted = 0;
        music3_ents[i].lfn = NULL;
        memcpy(music3_ents[i].sfn, nm, 12);
        memcpy(sub3_ents[i][0].sfn, "A       MP3", 12);
        sub3_ents[i][0].attr = 0x20;
        sub3_ents[i][0].clus = 0x9000u + (uint32_t)i;
        sub3_ents[i][0].deleted = 0;
        sub3_ents[i][0].lfn = NULL;
        dirs3[2 + i].clus = 0x2000u + (uint32_t)i;
        dirs3[2 + i].ents = sub3_ents[i];
        dirs3[2 + i].n = 1;
    }
    dirs3[0].clus = 0x0002;
    dirs3[0].ents = root_ents;
    dirs3[0].n = 6;
    dirs3[1].clus = 0x1001;
    dirs3[1].ents = music3_ents;
    dirs3[1].n = TREE3_DIRS;
}

int main(void)
{
    uint8_t node[0x80];
    uint8_t state[0x400];
    int i;
    int rc;

    for (i = 0; i < 42; i++) {
        ctx42_pattern[i] = (uint8_t)(0xA0 + i);
    }
    stock_registrar = mock_registrar;
    stock_file_size = mock_size;
    stock_file_read = mock_read;
    stock_fs_acquire = mock_acquire;
    stock_count_a = mock_count_a;
    stock_count_b = mock_count_b;
    stock_dirent_read = mock_dirent_read;
    stock_classifier = mock_classifier;

    /* ---- scenario 1: the full import ---------------------------- */
    g_dirs = dirs1;
    g_ndirs = 4;
    g_stream_clus = 0xFFFFFFFFu;
    g_playlist = playlist1;
    g_registrar_calls = 0;
    g_acquire_calls = 0;
    memset(stage_buf, 0xEE, sizeof stage_buf);
    make_node_state(node, state, 0x1001, "TEST    M3U");
    rc = m3u_bridge_node_action(node, state, NULL);
    CHECK(rc == 1);
    CHECK(g_registrar_calls == 1);
    CHECK(g_reg_dir == 0x1001u);
    CHECK(memcmp(g_reg_name, "TEST    M3U", 11) == 0);
    CHECK(g_reg_attr == 0x20u);
    CHECK(g_acquire_calls >= 1);
    /* header, packed layout field by field */
    CHECK(stage_buf[0] == 1);                    /* flag, set last */
    CHECK(stage_buf[1] == 7);                    /* entry count */
    CHECK(rd16(stage_buf + 2) == 0xFFFF);        /* position: none */
    CHECK(rd16(stage_buf + 4) == 0);             /* residual */
    CHECK(stage_buf[6] == 4);                    /* run count */
    for (i = 7; i < 16; i++) {
        CHECK(stage_buf[i] == 0);
    }
    check_ctx();
    /* runs in first-use order: MUSIC, LIVE, ROOT, PODCAST */
    check_run(0, 0x1001, 2, 1);
    check_run(1, 0x1003, 2, 0);
    check_run(2, 0x0002, 2, 2);
    check_run(3, 0x1002, 2, 0);
    /* entries: playlist order, duplicates kept */
    check_entry(0, 0, 0);   /* SONG1.MP3 in MUSIC */
    check_entry(1, 1, 1);   /* LIVE/SET2.MP3 */
    check_entry(2, 0, 2);   /* /ROOT1.MP3 */
    check_entry(3, 1, 2);   /* Long File Name.flac (LFN match) */
    check_entry(4, 0, 3);   /* ../PODCAST/EP1.MP3 via stage 2 */
    check_entry(5, 0, 0);   /* SONG1.MP3 again */
    check_entry(6, 1, 0);   /* track3.fla, folded, in MUSIC */
    printf("scenario 1 (full import, staging layout): %s\n",
           failures ? "FAILURES" : "ok");

    /* ---- scenario 2: FS type 3 declines, stale playlist disarmed */
    {
        int before = failures;
        m3u_host_fs_type = 3;
        memset(stage_buf, 0x55, sizeof stage_buf);
        rc = m3u_bridge_node_action(node, state, NULL);
        CHECK(rc == 0);
        CHECK(stage_buf[0] == 0);
        for (i = 1; i < (int)sizeof stage_buf; i++) {
            CHECK(stage_buf[i] == 0x55);
        }
        m3u_host_fs_type = 1;
        printf("scenario 2 (FS type 3 decline): %s\n",
               failures == before ? "ok" : "FAILURES");
    }

    /* ---- scenario 3: 33 runs needed, cap is 32 ------------------- */
    init_tree3();
    {
        int before = failures;
        static char big_playlist[2048];
        int o = 0;
        g_dirs = dirs3;
        g_ndirs = TREE3_DIRS + 2;
        g_stream_clus = 0xFFFFFFFFu;
        for (i = 0; i < TREE3_DIRS; i++) {
            o += snprintf(big_playlist + o, sizeof big_playlist - (size_t)o,
                          "D%02d/A.MP3\n", i);
        }
        g_playlist = big_playlist;
        memset(stage_buf, 0xEE, sizeof stage_buf);
        make_node_state(node, state, 0x1001, "BIG     M3U");
        rc = m3u_bridge_node_action(node, state, NULL);
        CHECK(rc == 0);
        CHECK(stage_buf[0] == 0);       /* disarmed, never armed */
        printf("scenario 3 (run cap decline): %s\n",
               failures == before ? "ok" : "FAILURES");
    }

    /* ---- scenario 5: exactly 32 runs arm --------------------------- */
    {
        int before = failures;
        static char cap_playlist[2048];
        int o = 0;
        g_dirs = dirs3;
        g_ndirs = TREE3_DIRS + 2;
        g_stream_clus = 0xFFFFFFFFu;
        for (i = 0; i < (int)M3U_STAGE_MAX_RUNS; i++) {
            o += snprintf(cap_playlist + o, sizeof cap_playlist - (size_t)o,
                          "D%02d/A.MP3\n", i);
        }
        g_playlist = cap_playlist;
        memset(stage_buf, 0xEE, sizeof stage_buf);
        make_node_state(node, state, 0x1001, "CAP     M3U");
        rc = m3u_bridge_node_action(node, state, NULL);
        CHECK(rc == 1);
        CHECK(stage_buf[0] == 1);
        CHECK(stage_buf[1] == M3U_STAGE_MAX_RUNS);
        CHECK(stage_buf[6] == M3U_STAGE_MAX_RUNS);
        check_ctx();
        for (i = 0; i < (int)M3U_STAGE_MAX_RUNS; i++) {
            check_run(i, 0x2000u + (uint32_t)i, 1, 0);
            check_entry(i, 0, i);
        }
        printf("scenario 5 (32 runs arm): %s\n",
               failures == before ? "ok" : "FAILURES");
    }

    /* ---- scenario 4: nothing resolves ----------------------------- */
    {
        int before = failures;
        g_dirs = dirs1;
        g_ndirs = 4;
        g_stream_clus = 0xFFFFFFFFu;
        g_playlist = "NOPE1.MP3\nNOPE2.WAV\n";
        memset(stage_buf, 0xEE, sizeof stage_buf);
        make_node_state(node, state, 0x1001, "EMPTY   M3U");
        rc = m3u_bridge_node_action(node, state, NULL);
        CHECK(rc == 0);
        CHECK(stage_buf[0] == 0);
        printf("scenario 4 (no resolvable entries): %s\n",
               failures == before ? "ok" : "FAILURES");
    }

    /* ---- scenario 6: entry cap, 150 arm and 151 decline ----------- */
    {
        int before = failures;
        static char rep_playlist[4096];
        int n;
        for (n = (int)M3U_STAGE_MAX_ENT; n <= (int)M3U_STAGE_MAX_ENT + 1;
             n++) {
            int o = 0;
            g_dirs = dirs1;
            g_ndirs = 4;
            g_stream_clus = 0xFFFFFFFFu;
            for (i = 0; i < n; i++) {
                o += snprintf(rep_playlist + o,
                              sizeof rep_playlist - (size_t)o,
                              (i & 1) ? "TRACK3.FLA\n" : "LIVE/SET2.MP3\n");
            }
            g_playlist = rep_playlist;
            memset(stage_buf, 0xEE, sizeof stage_buf);
            make_node_state(node, state, 0x1001, "LONG    M3U");
            rc = m3u_bridge_node_action(node, state, NULL);
            if (n == (int)M3U_STAGE_MAX_ENT) {
                CHECK(rc == 1);
                CHECK(stage_buf[0] == 1);
                CHECK(stage_buf[1] == M3U_STAGE_MAX_ENT);
                CHECK(stage_buf[6] == 2);
                check_run(0, 0x1003, 2, 0);
                check_run(1, 0x1001, 2, 1);
                check_entry(0, 1, 0);
                check_entry(1, 1, 1);
                check_entry(n - 2, 1, 0);
                check_entry(n - 1, 1, 1);
            } else {
                CHECK(rc == 0);
                CHECK(stage_buf[0] == 0);
            }
        }
        printf("scenario 6 (entry cap 150 arm, 151 decline): %s\n",
               failures == before ? "ok" : "FAILURES");
    }

    /* ---- scenario 7: .m3u8 through its 8.3 alias ------------------ */
    {
        int before = failures;
        g_dirs = dirs1;
        g_ndirs = 4;
        g_stream_clus = 0xFFFFFFFFu;
        g_playlist = "\xEF\xBB\xBF#EXTM3U\r\n"
                     "#EXTINF:200,Artist - Title\r\n"
                     "D:\\MUSIC\\LIVE\\SET1.MP3\r\n"
                     "..\\Long File Name.flac\r\n"
                     "SONG1.MP3\r\n"
                     "/PODCAST/ep 2 \xF0\x9F\x8E\xA7 CAF\xC3\x89.MP3\r\n";
        memset(stage_buf, 0xEE, sizeof stage_buf);
        make_node_state(node, state, 0x1001, "EVENIN~1M3U");
        rc = m3u_bridge_node_action(node, state, NULL);
        CHECK(rc == 1);
        CHECK(stage_buf[0] == 1);
        CHECK(stage_buf[1] == 4);
        CHECK(stage_buf[6] == 4);
        check_run(0, 0x1003, 2, 0);     /* LIVE */
        check_run(1, 0x0002, 2, 2);     /* root */
        check_run(2, 0x1001, 2, 1);     /* MUSIC */
        check_entry(0, 0, 0);           /* D:\MUSIC\LIVE\SET1.MP3 */
        check_entry(1, 1, 1);           /* ..\Long File Name.flac */
        check_entry(2, 0, 2);           /* SONG1.MP3 */
        check_run(3, 0x1002, 2, 0);     /* PODCAST */
        check_entry(3, 1, 3);           /* emoji + case-folded accent */
        printf("scenario 7 (.m3u8 via 8.3 alias, BOM, CRLF): %s\n",
               failures == before ? "ok" : "FAILURES");
    }

    printf("host bridge test: %s (%d failures)\n",
           failures ? "FAILED" : "PASSED", failures);
    return failures ? 1 : 0;
}
