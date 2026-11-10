/*
 * test_m3u.c - host tests for the M3U parser/resolver core.
 *
 * The mock filesystem models the stock library the way the bridge will
 * see it on device: a flat set of files, each with a canonical UTF-8
 * absolute path and the (clus, index) pair the scan assigned it.
 * stat() is ASCII case-insensitive and accent-sensitive, matching FAT
 * long-name behaviour; the resolver's own fold (stage 3) is what
 * bridges accent/case differences beyond that.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../src/m3u.h"

/* ------------------------------------------------------------------ */
/* Mock filesystem                                                     */
/* ------------------------------------------------------------------ */

#define MOCK_MAX_FILES 600

typedef struct MockFile {
    char path[512];
    uint32_t clus;
    uint32_t index;
    int is_dir;
    const uint8_t *content; /* playlist bytes, when this file is one */
    uint32_t content_len;
} MockFile;

static MockFile g_files[MOCK_MAX_FILES];
static uint32_t g_nfiles;

static void mock_add(const char *path, uint32_t clus, uint32_t index, int is_dir,
                     const void *content, uint32_t content_len)
{
    MockFile *f = &g_files[g_nfiles++];
    snprintf(f->path, sizeof f->path, "%s", path);
    f->clus = clus;
    f->index = index;
    f->is_dir = is_dir;
    f->content = (const uint8_t *)content;
    f->content_len = content_len;
}

static int ascii_fold_cmp(const char *a, const char *b)
{
    for (;; a++, b++) {
        char ca = *a, cb = *b;
        if (ca >= 'A' && ca <= 'Z') {
            ca += 'a' - 'A';
        }
        if (cb >= 'A' && cb <= 'Z') {
            cb += 'a' - 'A';
        }
        if (ca != cb) {
            return (unsigned char)ca - (unsigned char)cb;
        }
        if (ca == '\0') {
            return 0;
        }
    }
}

static MockFile *mock_find(const char *path)
{
    for (uint32_t i = 0; i < g_nfiles; i++) {
        if (ascii_fold_cmp(g_files[i].path, path) == 0) {
            return &g_files[i];
        }
    }
    return NULL;
}

typedef struct MockHandle {
    const MockFile *file;
} MockHandle;

static void *mock_open(void *ctx, const char *path)
{
    MockFile *f;
    (void)ctx;
    f = mock_find(path);
    if (f == NULL || f->is_dir || f->content == NULL) {
        return NULL;
    }
    MockHandle *h = (MockHandle *)malloc(sizeof *h);
    h->file = f;
    return h;
}

static int mock_read(void *ctx, void *fh, uint32_t off, uint8_t *buf, uint32_t len)
{
    MockHandle *h = (MockHandle *)fh;
    (void)ctx;
    if (off >= h->file->content_len) {
        return 0;
    }
    uint32_t avail = h->file->content_len - off;
    if (len > avail) {
        len = avail;
    }
    memcpy(buf, h->file->content + off, len);
    return (int)len;
}

static uint32_t mock_size(void *ctx, void *fh)
{
    (void)ctx;
    return ((MockHandle *)fh)->file->content_len;
}

static void mock_close(void *ctx, void *fh)
{
    (void)ctx;
    free(fh);
}

static int mock_stat(void *ctx, const char *path, M3uFileInfo *out)
{
    MockFile *f;
    (void)ctx;
    f = mock_find(path);
    if (f == NULL) {
        return -1;
    }
    out->clus = f->clus;
    out->index = f->index;
    out->is_dir = f->is_dir != 0;
    return 0;
}

static uint32_t mock_lib_count(void *ctx)
{
    uint32_t n = 0;
    (void)ctx;
    for (uint32_t i = 0; i < g_nfiles; i++) {
        if (!g_files[i].is_dir) {
            n++;
        }
    }
    return n;
}

static int mock_lib_nth(void *ctx, uint32_t n, char *path_out, uint32_t cap, M3uFileInfo *out)
{
    (void)ctx;
    for (uint32_t i = 0; i < g_nfiles; i++) {
        if (g_files[i].is_dir) {
            continue;
        }
        if (n-- == 0) {
            snprintf(path_out, cap, "%s", g_files[i].path);
            out->clus = g_files[i].clus;
            out->index = g_files[i].index;
            out->is_dir = false;
            return 0;
        }
    }
    return -1;
}

static const M3uFs MOCK_FS = {
    .ctx = NULL,
    .open = mock_open,
    .read = mock_read,
    .size = mock_size,
    .close = mock_close,
    .stat = mock_stat,
    .lib_count = mock_lib_count,
    .lib_nth = mock_lib_nth,
};

/* ------------------------------------------------------------------ */
/* Test scaffolding                                                    */
/* ------------------------------------------------------------------ */

static int g_checks;
static int g_failures;

#define CHECK(cond, ...)                                       \
    do {                                                       \
        g_checks++;                                            \
        if (!(cond)) {                                         \
            g_failures++;                                      \
            printf("FAIL %s:%d: ", __FILE__, __LINE__);        \
            printf(__VA_ARGS__);                               \
            printf("\n");                                      \
        }                                                      \
    } while (0)

static void add_playlist(const char *path, const void *content, uint32_t len)
{
    mock_add(path, 900, 0, 0, content, len);
}

static void add_playlist_str(const char *path, const char *content)
{
    add_playlist(path, content, (uint32_t)strlen(content));
}

/* ------------------------------------------------------------------ */
/* Library fixture                                                     */
/* ------------------------------------------------------------------ */

static void build_library(void)
{
    mock_add("/Music", 0, 0, 1, NULL, 0);
    mock_add("/Music/Rock", 0, 0, 1, NULL, 0);
    mock_add("/Music/Rock/Highway Star.mp3", 100, 3, 0, NULL, 0);
    mock_add("/Music/Rock/Child in Time.mp3", 101, 4, 0, NULL, 0);
    mock_add("/Music/Pop/Bj\xC3\xB6rk - Hyperballad.flac", 102, 1, 0, NULL, 0);
    mock_add("/Music/Classical/Caf\xC3\xA9 del Mar.wav", 103, 2, 0, NULL, 0);
    mock_add("/Music/Dup/Same Name.mp3", 110, 0, 0, NULL, 0);
    mock_add("/Music/Other/Same Name.mp3", 111, 0, 0, NULL, 0);
    mock_add("/Music/Deep/Nest/Leaf Song.ogg", 120, 7, 0, NULL, 0);
    mock_add("/Playlists", 0, 0, 1, NULL, 0);
}

/* ------------------------------------------------------------------ */
/* Tests                                                               */
/* ------------------------------------------------------------------ */

static void test_windows_style(void)
{
    static const char text[] =
        "#EXTM3U\r\n"
        "#EXTINF:342,Deep Purple - Highway Star\r\n"
        "D:\\Music\\Rock\\Highway Star.mp3\r\n"
        "#EXTINF:-1,Deep Purple - Child in Time\r\n"
        "..\\Music\\Rock\\Child in Time.mp3\r\n"
        "/Music/Deep/Nest/Leaf Song.ogg\r\n";
    M3uTrack out[8];
    M3uStats st;
    add_playlist_str("/Playlists/windows.m3u", text);
    int rc = m3u_import(&MOCK_FS, "/Playlists/windows.m3u", out, 8, &st);
    CHECK(rc == 0, "windows: rc=%d", rc);
    CHECK(st.total_entries == 3 && st.resolved == 3 && st.skipped_missing == 0,
          "windows: total=%u resolved=%u missing=%u", st.total_entries, st.resolved,
          st.skipped_missing);
    CHECK(out[0].clus == 100 && out[0].index == 3, "windows: [0]=(%u,%u)", out[0].clus,
          out[0].index);
    CHECK(out[0].has_meta && out[0].duration_s == 342, "windows: [0] dur=%d", out[0].duration_s);
    CHECK(strcmp(out[0].artist, "Deep Purple") == 0 && strcmp(out[0].title, "Highway Star") == 0,
          "windows: [0] meta '%s'/'%s'", out[0].artist, out[0].title);
    CHECK(out[1].clus == 101 && out[1].index == 4, "windows: [1]=(%u,%u)", out[1].clus,
          out[1].index);
    CHECK(out[1].duration_s == -1, "windows: [1] dur=%d", out[1].duration_s);
    CHECK(out[2].clus == 120 && out[2].index == 7 && !out[2].has_meta,
          "windows: [2]=(%u,%u) meta=%d", out[2].clus, out[2].index, (int)out[2].has_meta);
    printf("ok: windows-style (CRLF, backslashes, drive letter, .., EXTINF)\n");
}

static void test_utf8_bom(void)
{
    static const char text[] =
        "\xEF\xBB\xBF#EXTM3U\n"
        "Music/Pop/Bj\xC3\xB6rk - Hyperballad.flac\n";
    M3uTrack out[4];
    M3uStats st;
    add_playlist("/utf8.m3u8", text, (uint32_t)sizeof text - 1);
    int rc = m3u_import(&MOCK_FS, "/utf8.m3u8", out, 4, &st);
    CHECK(rc == 0 && st.resolved == 1, "utf8: rc=%d resolved=%u", rc, st.resolved);
    CHECK(out[0].clus == 102 && out[0].index == 1, "utf8: (%u,%u)", out[0].clus, out[0].index);
    printf("ok: utf-8 with BOM, .m3u8, root-relative entry\n");
}

static void test_latin1(void)
{
    /* 0xE9 is 'e-acute' in Windows-1252 and an incomplete UTF-8 lead
     * here (followed by a space), so the sniff must fall back. */
    static const char text[] = "Caf\xE9 del Mar.wav\n";
    M3uTrack out[4];
    M3uStats st;
    add_playlist("/Music/Classical/latin1.m3u", text, (uint32_t)sizeof text - 1);
    int rc = m3u_import(&MOCK_FS, "/Music/Classical/latin1.m3u", out, 4, &st);
    CHECK(rc == 0 && st.resolved == 1, "latin1: rc=%d resolved=%u missing=%u", rc, st.resolved,
          st.skipped_missing);
    CHECK(out[0].clus == 103 && out[0].index == 2, "latin1: (%u,%u)", out[0].clus, out[0].index);
    printf("ok: windows-1252 playlist resolves utf-8 library name\n");
}

static void test_missing_dup_url(void)
{
    static const char text[] =
        "#EXTM3U\n"
        "/Music/Rock/Highway Star.mp3\n"
        "/Music/Rock/No Such Song.mp3\n"
        "http://example.com/stream.mp3\n"
        "/Music/Rock/Highway Star.mp3\n"
        "/Music/Rock\n";
    M3uTrack out[8];
    M3uStats st;
    add_playlist_str("/Playlists/mixed.m3u", text);
    int rc = m3u_import(&MOCK_FS, "/Playlists/mixed.m3u", out, 8, &st);
    CHECK(rc == 0, "mixed: rc=%d", rc);
    CHECK(st.total_entries == 5, "mixed: total=%u", st.total_entries);
    CHECK(st.resolved == 2 && st.skipped_missing == 2 && st.skipped_url == 1,
          "mixed: resolved=%u missing=%u url=%u", st.resolved, st.skipped_missing,
          st.skipped_url);
    CHECK(out[0].clus == 100 && out[1].clus == 100 && out[0].index == out[1].index,
          "mixed: duplicates kept in order");
    printf("ok: missing skipped, url skipped, directory skipped, duplicates kept\n");
}

static void test_suffix_rules(void)
{
    static const char tie_text[] = "Same Name.mp3\n";
    static const char deep_text[] = "Dup/Same Name.mp3\n";
    static const char fold_text[] = "Pop/Bjork - Hyperballad.flac\n";
    M3uTrack out[4];
    M3uStats st;

    add_playlist_str("/Playlists/tie.m3u", tie_text);
    int rc = m3u_import(&MOCK_FS, "/Playlists/tie.m3u", out, 4, &st);
    CHECK(rc == 0 && st.resolved == 0 && st.skipped_missing == 1,
          "tie: resolved=%u missing=%u", st.resolved, st.skipped_missing);

    add_playlist_str("/Playlists/deep.m3u", deep_text);
    rc = m3u_import(&MOCK_FS, "/Playlists/deep.m3u", out, 4, &st);
    CHECK(rc == 0 && st.resolved == 1 && out[0].clus == 110, "deep: resolved=%u clus=%u",
          st.resolved, out[0].clus);

    add_playlist_str("/Playlists/fold.m3u", fold_text);
    rc = m3u_import(&MOCK_FS, "/Playlists/fold.m3u", out, 4, &st);
    CHECK(rc == 0 && st.resolved == 1 && out[0].clus == 102, "fold: resolved=%u clus=%u",
          st.resolved, out[0].clus);
    printf("ok: suffix match (tie unresolved, deeper suffix wins, accent fold)\n");
}

static void test_extinf_association(void)
{
    static const char text[] =
        "#EXTM3U\n"
        "#EXTINF:200,Just A Title\n"
        "# a comment line does not consume the metadata\n"
        "\n"
        "/Music/Rock/Highway Star.mp3\n"
        "/Music/Rock/Child in Time.mp3\n";
    M3uTrack out[4];
    M3uStats st;
    add_playlist_str("/Playlists/meta.m3u", text);
    int rc = m3u_import(&MOCK_FS, "/Playlists/meta.m3u", out, 4, &st);
    CHECK(rc == 0 && st.resolved == 2, "meta: resolved=%u", st.resolved);
    CHECK(out[0].has_meta && out[0].duration_s == 200 && out[0].artist[0] == '\0' &&
              strcmp(out[0].title, "Just A Title") == 0,
          "meta: [0] dur=%d artist='%s' title='%s'", out[0].duration_s, out[0].artist,
          out[0].title);
    CHECK(!out[1].has_meta && out[1].duration_s == -1, "meta: [1] must carry no metadata");
    printf("ok: EXTINF association (survives comments/blanks, title-only form)\n");
}

static void test_large_playlist(void)
{
    enum { N = 500 };
    static char text[N * 48];
    uint32_t used = 0;
    for (int i = 0; i < N; i++) {
        char path[128];
        snprintf(path, sizeof path, "/Music/Gen/Track %03d.mp3", i);
        mock_add(path, 1000 + (uint32_t)i, (uint32_t)i, 0, NULL, 0);
        used += (uint32_t)snprintf(text + used, sizeof text - used, "%s\n", path);
    }
    M3uTrack *out = (M3uTrack *)malloc(sizeof *out * N);
    M3uStats st;
    add_playlist("/big.m3u", text, used);
    int rc = m3u_import(&MOCK_FS, "/big.m3u", out, N, &st);
    CHECK(rc == 0 && st.total_entries == (uint32_t)N && st.resolved == (uint32_t)N,
          "big: total=%u resolved=%u", st.total_entries, st.resolved);
    int order_ok = 1;
    for (int i = 0; i < N; i++) {
        if (out[i].clus != 1000 + (uint32_t)i || out[i].index != (uint32_t)i) {
            order_ok = 0;
        }
    }
    CHECK(order_ok, "big: order/pairs preserved across all %d entries", N);
    free(out);
    printf("ok: 500-entry playlist, order and (clus,index) verified\n");
}

static void test_overflow_and_errors(void)
{
    static const char text[] =
        "/Music/Rock/Highway Star.mp3\n"
        "/Music/Rock/Child in Time.mp3\n"
        "/Music/Deep/Nest/Leaf Song.ogg\n";
    M3uTrack out[2];
    M3uStats st;
    add_playlist_str("/Playlists/over.m3u", text);
    int rc = m3u_import(&MOCK_FS, "/Playlists/over.m3u", out, 2, &st);
    CHECK(rc == 0 && st.resolved == 2 && st.overflow == 1, "over: resolved=%u overflow=%u",
          st.resolved, st.overflow);
    rc = m3u_import(&MOCK_FS, "/Playlists/does-not-exist.m3u", out, 2, &st);
    CHECK(rc == -1, "missing playlist file: rc=%d (want -1)", rc);
    printf("ok: output-cap overflow accounting, unreadable playlist is -1\n");
}

int main(void)
{
    build_library();
    test_windows_style();
    test_utf8_bom();
    test_latin1();
    test_missing_dup_url();
    test_suffix_rules();
    test_extinf_association();
    test_large_playlist();
    test_overflow_and_errors();
    printf("---\n%d checks, %d failures\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
