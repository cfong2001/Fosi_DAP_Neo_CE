/*
 * m3u.h - M3U/M3U8 playlist parser + resolver core for the DAP Neo stock
 * firmware patch.
 *
 * The parsing and resolution logic is informed by EchoPod's
 * playlist_reader.c and library_builder_paths.c (BasilSkyWalk/echopod,
 * GPL-3.0) and its NeoPod port (danielNZ27, GPL-3.0): the UTF-8 sniff
 * with Windows-1252 fallback, BOM/comment handling, and the three-stage
 * path resolution (playlist folder -> volume root -> case-folded suffix
 * match) are their design. This implementation is an independent
 * re-implementation in a different structure, written for the stock
 * firmware's constraints: no heap, no libc beyond byte/string helpers
 * that the port layer can map onto stock module-0 routines, and an
 * abstract filesystem whose stat() returns the stock playback identity
 * of a file - its (clus, index) pair - instead of a path handle.
 *
 * All paths in this interface are UTF-8, '/'-separated, and absolute
 * paths start with '/'. A leading drive designator in playlist entries
 * ("D:\Music\...") is handled by the resolver, not the caller.
 */
#ifndef M3U_H
#define M3U_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum {
    M3U_PATH_CAP = 512,     /* longest path we carry, incl. NUL */
    M3U_LINE_CAP = 1024,    /* longest raw playlist line, decoded, incl. NUL */
    M3U_TEXT_CAP = 128,     /* EXTINF title/artist fields, incl. NUL */
    M3U_MAX_PARTS = 16      /* max path components used by suffix matching */
};

/* The stock playback identity of one file: starting cluster + the
 * directory-entry ordinal the scan stores in the playback record
 * (see analysis/library_m3u.md, record layout +0x00/+0x04). */
typedef struct M3uFileInfo {
    uint32_t clus;
    uint32_t index;
    bool is_dir;
} M3uFileInfo;

/* Abstract filesystem. On device this is implemented over the stock
 * directory walker (module 0 0x0305A2F0 via the 0x0305A970 wrapper) and
 * the browser/scan node arrays; on host it is implemented by the mock
 * in tests/mock_fs.c. stat() must be case-insensitive in the FAT sense:
 * a path that differs only in letter case or in '/' vs the stored
 * separator convention still finds the file. lib_nth() enumerates every
 * file the library knows, returning its canonical absolute path. */
typedef struct M3uFs {
    void *ctx;
    void *(*open)(void *ctx, const char *path);
    int (*read)(void *ctx, void *fh, uint32_t off, uint8_t *buf, uint32_t len);
    uint32_t (*size)(void *ctx, void *fh);
    void (*close)(void *ctx, void *fh);
    int (*stat)(void *ctx, const char *path, M3uFileInfo *out);
    uint32_t (*lib_count)(void *ctx);
    int (*lib_nth)(void *ctx, uint32_t n, char *path_out, uint32_t cap, M3uFileInfo *out);
} M3uFs;

typedef struct M3uTrack {
    uint32_t clus;
    uint32_t index;
    int32_t duration_s; /* -1 when the playlist gave no #EXTINF duration */
    char title[M3U_TEXT_CAP];
    char artist[M3U_TEXT_CAP];
    bool has_meta; /* an #EXTINF line preceded this entry */
} M3uTrack;

typedef struct M3uStats {
    uint32_t total_entries;   /* non-comment lines seen */
    uint32_t resolved;        /* entries written to out[] */
    uint32_t skipped_missing; /* no stage could resolve the entry */
    uint32_t skipped_url;     /* http:// etc. entries */
    uint32_t overflow;        /* resolved but out[] was full */
} M3uStats;

/*
 * Parse the playlist at playlist_path (absolute, UTF-8) and resolve each
 * entry to a (clus, index) pair, preserving playlist order and
 * duplicates. Unresolvable entries are skipped, never fatal.
 *
 * Returns 0 on success (even if some entries skipped), -1 if the
 * playlist itself could not be opened/read. stats may be NULL.
 */
int m3u_import(const M3uFs *fs, const char *playlist_path, M3uTrack *out, uint32_t out_cap,
               M3uStats *stats);

#endif /* M3U_H */
