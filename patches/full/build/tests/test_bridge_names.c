/* Exercise the real bridge directory matcher with raw FAT entries. */
#define HOST_TEST
#include "../src/m3u_bridge.c"
#include <stdio.h>
#include <string.h>

uint8_t *m3u_host_stage;
uint32_t m3u_host_root_cluster;
const uint8_t *m3u_host_ctx42;
uint8_t m3u_host_fs_type;
const uint8_t *m3u_host_table;
static uint8_t dirents[24][32];
static int dir_read(uint8_t *out, uint32_t cluster, uint32_t index)
{
    (void)cluster;
    if (index >= 24) return -1;
    memcpy(out, dirents[index], 32);
    return 0;
}
static int accept(const uint8_t *ext, const uint8_t *table, uint32_t attr)
{ (void)ext; (void)table; (void)attr; return 1; }
static void file_at(int idx, const char *sfn)
{
    memcpy(dirents[idx], sfn, 11);
    dirents[idx][11] = 0x20;
}
static void lfn_at(int idx, unsigned seq, int last, const char *name,
                   const char *sfn)
{
    uint8_t *de = dirents[idx];
    unsigned j, base = (seq - 1) * 13;
    size_t len = strlen(name);
    de[0] = (uint8_t)(seq | (last ? 0x40 : 0));
    de[11] = 0x0f;
    de[13] = sfn_checksum((const uint8_t *)sfn);
    for (j = 0; j < 13; j++) {
        unsigned off = j < 5 ? 1 + 2*j : j < 11 ? 14 + 2*(j-5) : 28 + 2*(j-11);
        unsigned n = base + j;
        uint16_t c = n < len ? (uint8_t)name[n] : n == len ? 0 : 0xffff;
        de[off] = (uint8_t)c;
        de[off+1] = (uint8_t)(c >> 8);
    }
}
static int find(const char *name)
{ return find_in_dir(1, (const uint8_t *)name, (uint32_t)strlen(name)).found; }
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"failed line %d: %s\n", __LINE__, #x); return 1; } } while(0)
int main(void)
{
    char long_name[261];
    stock_dirent_read = dir_read;
    stock_classifier = accept;
    file_at(0, "ABCDEFGHMP3");
    CHECK(!find(""));
    CHECK(find("abcdefgh.mp3"));
    CHECK(!find("abcdefghijk.mp3"));
    CHECK(!find("abc defgh.mp3"));
    CHECK(!find("abcd.efgh.mp3"));
    memset(dirents, 0, sizeof dirents);
    lfn_at(0, 2, 1, "Long File Name.flac", "LONGFI~1FLA");
    lfn_at(1, 1, 0, "Long File Name.flac", "LONGFI~1FLA");
    file_at(2, "LONGFI~1FLA");
    CHECK(find("Long File Name.flac"));
    dirents[1][13] ^= 1;
    CHECK(!find("Long File Name.flac"));
    dirents[1][13] ^= 1;
    dirents[1][0] = 2; /* repeated ordinal */
    CHECK(!find("Long File Name.flac"));
    dirents[1][0] = 1;
    /* An incomplete group must not match stale/uninitialised stack bytes. */
    memcpy(dirents[1], dirents[2], 32);
    memset(dirents[2], 0, 32);
    CHECK(!find("Long File Name.flac"));
    /* 20 full LFN entries with no terminator must never read 260 cells. */
    memset(dirents, 0, sizeof dirents);
    memset(long_name, 'A', 260); long_name[260] = 0;
    for (unsigned seq = 20; seq >= 1; seq--)
        lfn_at((int)(20-seq), seq, seq == 20, long_name, "LONGFI~1MP3");
    file_at(20, "LONGFI~1MP3");
    CHECK(!find(long_name));
    /* Maximum legal name still works when the final component terminates. */
    memset(dirents, 0, sizeof dirents);
    long_name[255] = 0;
    for (unsigned seq = 20; seq >= 1; seq--)
        lfn_at((int)(20-seq), seq, seq == 20, long_name, "LONGFI~1MP3");
    file_at(20, "LONGFI~1MP3");
    CHECK(find(long_name));
    puts("bridge filename tests passed");
    return 0;
}
