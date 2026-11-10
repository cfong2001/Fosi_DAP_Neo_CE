/*
 * m3u.c - see m3u.h for provenance and interface notes.
 *
 * Structure: a chunked byte reader with encoding sniffing, a line
 * assembler that also captures #EXTINF metadata, path utilities
 * (separator normalisation, dot-component collapsing, case/accent
 * folding, component splitting), and the three-stage resolver.
 * No heap, no libc calls: the only external surface is the M3uFs
 * vtable and the local byte helpers below, which the device port maps
 * onto stock module-0 routines.
 */

#include "m3u.h"

/* ------------------------------------------------------------------ */
/* Local helpers (port surface)                                        */
/* ------------------------------------------------------------------ */

static uint32_t x_strlen(const char *s)
{
    uint32_t n = 0;
    while (s[n] != '\0') {
        n++;
    }
    return n;
}

static void x_strcpy(char *dst, const char *src, uint32_t cap)
{
    uint32_t i = 0;
    if (cap == 0) {
        return;
    }
    while (src[i] != '\0' && i + 1 < cap) {
        dst[i] = src[i];
        i++;
    }
    dst[i] = '\0';
}

static bool x_starts(const char *s, const char *prefix)
{
    while (*prefix != '\0') {
        if (*s++ != *prefix++) {
            return false;
        }
    }
    return true;
}

static const char *x_strstr(const char *s, const char *needle)
{
    uint32_t nl = x_strlen(needle);
    if (nl == 0) {
        return s;
    }
    for (; *s != '\0'; s++) {
        uint32_t i = 0;
        while (i < nl && s[i] == needle[i]) {
            i++;
        }
        if (i == nl) {
            return s;
        }
    }
    return NULL;
}

/* ------------------------------------------------------------------ */
/* UTF-8 / Windows-1252 decoding                                       */
/* ------------------------------------------------------------------ */

/* Windows-1252 assignments for 0x80..0x9F (0xFFFD = undefined there). */
static const uint16_t CP1252_HIGH[32] = {
    0x20AC, 0xFFFD, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021,
    0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0xFFFD, 0x017D, 0xFFFD,
    0xFFFD, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014,
    0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0xFFFD, 0x017E, 0x0178,
};

static uint32_t utf8_seq_len(uint8_t lead)
{
    if (lead < 0x80) {
        return 1;
    }
    if (lead >= 0xC2 && lead <= 0xDF) {
        return 2;
    }
    if (lead >= 0xE0 && lead <= 0xEF) {
        return 3;
    }
    return (lead >= 0xF0 && lead <= 0xF4) ? 4 : 0;
}

static bool utf8_second_ok(uint8_t lead, uint8_t second)
{
    if (lead == 0xE0) {
        return second >= 0xA0 && second <= 0xBF;
    }
    if (lead == 0xED) {
        return second >= 0x80 && second <= 0x9F;
    }
    if (lead == 0xF0) {
        return second >= 0x90 && second <= 0xBF;
    }
    if (lead == 0xF4) {
        return second >= 0x80 && second <= 0x8F;
    }
    return second >= 0x80 && second <= 0xBF;
}

/* Encode one code point as UTF-8; returns bytes written (cap permitting). */
static uint32_t utf8_encode(uint32_t cp, char *out, uint32_t cap)
{
    uint8_t tmp[4];
    uint32_t size = cp < 0x80 ? 1 : cp < 0x800 ? 2 : cp < 0x10000 ? 3 : 4;
    uint32_t value = cp;
    if (size > cap) {
        return 0;
    }
    for (uint32_t i = size - 1; i > 0; i--) {
        tmp[i] = (uint8_t)(0x80 | (value & 0x3F));
        value >>= 6;
    }
    tmp[0] = (uint8_t)((size == 1 ? 0x00 : size == 2 ? 0xC0 : size == 3 ? 0xE0 : 0xF0) | value);
    for (uint32_t i = 0; i < size; i++) {
        out[i] = (char)tmp[i];
    }
    return size;
}

/* Decode a code point. Paths may have been truncated after sniffing,
 * so reject incomplete sequences without reading beyond their NUL. */
static uint32_t utf8_decode(const char *s, uint32_t *len_out)
{
    uint8_t lead = (uint8_t)s[0];
    uint32_t len = utf8_seq_len(lead);
    uint32_t cp;
    if (len == 0) {
        *len_out = 1;
        return 0xFFFD;
    }
    cp = len == 1 ? lead : (lead & (0x7Fu >> len));
    for (uint32_t i = 1; i < len; i++) {
        uint8_t next = (uint8_t)s[i];
        if (next == 0 || (i == 1 ? !utf8_second_ok(lead, next)
                                  : (next < 0x80 || next > 0xBF))) {
            *len_out = 1;
            return 0xFFFD;
        }
        cp = (cp << 6) | (next & 0x3F);
    }
    *len_out = len;
    return cp;
}

/* ------------------------------------------------------------------ */
/* Case/accent folding                                                 */
/*                                                                     */
/* A deliberate subset of the fold EchoPod generates from full         */
/* Unicode tables: ASCII case plus the Latin-1 letters a playlist or   */
/* a FAT long filename realistically carries. Both sides of every      */
/* comparison pass through this same function, so the fold only has    */
/* to be internally consistent, not universal.                         */
/* ------------------------------------------------------------------ */

static uint32_t fold_cp(uint32_t cp, char *out, uint32_t cap)
{
    char single = '\0';
    const char *pair = NULL;
    if (cp >= 'A' && cp <= 'Z') {
        single = (char)(cp + ('a' - 'A'));
    } else if (cp < 0xC0 || cp == 0xD7 || cp == 0xF7) {
        return utf8_encode(cp, out, cap);
    } else if (cp <= 0xFF) {
        switch (cp) {
        case 0xC0: case 0xC1: case 0xC2: case 0xC3: case 0xC4: case 0xC5:
        case 0xE0: case 0xE1: case 0xE2: case 0xE3: case 0xE4: case 0xE5:
            single = 'a';
            break;
        case 0xC6: case 0xE6:
            pair = "ae";
            break;
        case 0xC7: case 0xE7:
            single = 'c';
            break;
        case 0xC8: case 0xC9: case 0xCA: case 0xCB:
        case 0xE8: case 0xE9: case 0xEA: case 0xEB:
            single = 'e';
            break;
        case 0xCC: case 0xCD: case 0xCE: case 0xCF:
        case 0xEC: case 0xED: case 0xEE: case 0xEF:
            single = 'i';
            break;
        case 0xD0: case 0xF0:
            single = 'd';
            break;
        case 0xD1: case 0xF1:
            single = 'n';
            break;
        case 0xD2: case 0xD3: case 0xD4: case 0xD5: case 0xD6: case 0xD8:
        case 0xF2: case 0xF3: case 0xF4: case 0xF5: case 0xF6: case 0xF8:
            single = 'o';
            break;
        case 0xD9: case 0xDA: case 0xDB: case 0xDC:
        case 0xF9: case 0xFA: case 0xFB: case 0xFC:
            single = 'u';
            break;
        case 0xDD: case 0xFD: case 0xFF:
            single = 'y';
            break;
        case 0xDE: case 0xFE:
            pair = "th";
            break;
        case 0xDF:
            pair = "ss";
            break;
        default:
            return utf8_encode(cp, out, cap);
        }
    } else {
        return utf8_encode(cp, out, cap);
    }
    if (pair != NULL) {
        if (cap < 2) {
            return 0;
        }
        out[0] = pair[0];
        out[1] = pair[1];
        return 2;
    }
    if (cap < 1) {
        return 0;
    }
    out[0] = single;
    return 1;
}

/* Fold a whole UTF-8 string into out (cap incl. NUL); returns length. */
static uint32_t fold_text(const char *in, char *out, uint32_t cap)
{
    uint32_t used = 0;
    uint32_t i = 0;
    if (cap == 0) {
        return 0;
    }
    while (in[i] != '\0') {
        uint32_t len = 1;
        uint32_t cp = utf8_decode(in + i, &len);
        uint32_t room = (used + 1 < cap) ? (cap - 1 - used) : 0;
        uint32_t wrote = room > 0 ? fold_cp(cp, out + used, room) : 0;
        if (wrote == 0) {
            break;
        }
        used += wrote;
        i += len;
    }
    out[used] = '\0';
    return used;
}

/* ------------------------------------------------------------------ */
/* Path utilities                                                      */
/* ------------------------------------------------------------------ */

typedef struct Span {
    uint32_t start;
    uint32_t length;
} Span;

typedef struct Parts {
    Span spans[M3U_MAX_PARTS];
    uint32_t count;
} Parts;

/* Split into '/'-separated components (text itself is not modified). */
static void split_parts(const char *path, Parts *parts)
{
    uint32_t i = 0;
    parts->count = 0;
    while (path[i] != '\0' && parts->count < M3U_MAX_PARTS) {
        while (path[i] == '/') {
            i++;
        }
        if (path[i] == '\0') {
            break;
        }
        uint32_t start = i;
        while (path[i] != '\0' && path[i] != '/') {
            i++;
        }
        parts->spans[parts->count].start = start;
        parts->spans[parts->count].length = i - start;
        parts->count++;
    }
}

static bool span_is(const char *text, Span span, const char *word)
{
    uint32_t wl = x_strlen(word);
    if (span.length != wl) {
        return false;
    }
    for (uint32_t i = 0; i < wl; i++) {
        if (text[span.start + i] != word[i]) {
            return false;
        }
    }
    return true;
}

/* Fold path into out, dropping "." and ".." components (the resolver
 * works on already-joined absolute paths, so ".." has been collapsed
 * by join_normalised; suffix matching drops dot components outright,
 * as the reference implementation does). */
static uint32_t fold_parts(const char *path, char *out, uint32_t cap, Parts *parts)
{
    char raw[M3U_PATH_CAP];
    Parts raw_parts;
    uint32_t used = 0;
    x_strcpy(raw, path, sizeof raw);
    split_parts(raw, &raw_parts);
    parts->count = 0;
    if (cap == 0) {
        return 0;
    }
    for (uint32_t i = 0; i < raw_parts.count && parts->count < M3U_MAX_PARTS; i++) {
        Span span = raw_parts.spans[i];
        char comp[M3U_PATH_CAP];
        uint32_t cl = span.length < sizeof comp - 1 ? span.length : sizeof comp - 1;
        uint32_t k;
        if (span_is(raw, span, ".") || span_is(raw, span, "..")) {
            continue;
        }
        for (k = 0; k < cl; k++) {
            comp[k] = raw[span.start + k];
        }
        comp[cl] = '\0';
        uint32_t folded = fold_text(comp, out + used, cap - used);
        parts->spans[parts->count].start = used;
        parts->spans[parts->count].length = folded;
        parts->count++;
        used += folded;
        if (used + 1 < cap) {
            out[used++] = '/';
        }
    }
    if (used > 0 && out[used - 1] == '/') {
        used--;
    }
    out[used] = '\0';
    return used;
}

static bool span_equal(const char *a_text, Span a, const char *b_text, Span b)
{
    if (a.length != b.length) {
        return false;
    }
    for (uint32_t i = 0; i < a.length; i++) {
        if (a_text[a.start + i] != b_text[b.start + i]) {
            return false;
        }
    }
    return true;
}

static uint32_t common_suffix(const char *a_text, const Parts *a, const char *b_text,
                              const Parts *b)
{
    uint32_t n = 0;
    while (n < a->count && n < b->count &&
           span_equal(a_text, a->spans[a->count - 1 - n], b_text, b->spans[b->count - 1 - n])) {
        n++;
    }
    return n;
}

/* Convert '\' to '/' in place; returns string length. */
static uint32_t normalise_separators(char *s)
{
    uint32_t n = 0;
    while (s[n] != '\0') {
        if (s[n] == '\\') {
            s[n] = '/';
        }
        n++;
    }
    return n;
}

/* Collapse "." and ".." components of an absolute or relative path in
 * place (textual normalisation; no filesystem access). */
static void collapse_dots(char *path)
{
    char tmp[M3U_PATH_CAP];
    Parts parts;
    uint32_t used = 0;
    bool absolute = path[0] == '/';
    x_strcpy(tmp, path, sizeof tmp);
    split_parts(tmp, &parts);
    if (absolute) {
        path[used++] = '/';
    }
    for (uint32_t i = 0; i < parts.count; i++) {
        Span span = parts.spans[i];
        if (span_is(tmp, span, ".")) {
            continue;
        }
        if (span_is(tmp, span, "..")) {
            /* pop the last written component */
            if (used > (absolute ? 1u : 0u)) {
                used--;
                while (used > (absolute ? 1u : 0u) && path[used - 1] != '/') {
                    used--;
                }
            }
            continue;
        }
        for (uint32_t k = 0; k < span.length && used + 1 < M3U_PATH_CAP; k++) {
            path[used++] = tmp[span.start + k];
        }
        if (used + 1 < M3U_PATH_CAP) {
            path[used++] = '/';
        }
    }
    if (used > (absolute ? 1u : 0u) && path[used - 1] == '/') {
        used--;
    }
    path[used] = '\0';
}

/* Join folder + entry into out as an absolute path and normalise. */
static void join_path(const char *folder, const char *entry, char *out)
{
    uint32_t used = 0;
    for (uint32_t i = 0; folder[i] != '\0' && used + 1 < M3U_PATH_CAP; i++) {
        out[used++] = folder[i];
    }
    if (used == 0 || out[used - 1] != '/') {
        if (used + 1 < M3U_PATH_CAP) {
            out[used++] = '/';
        }
    }
    for (uint32_t i = 0; entry[i] != '\0' && used + 1 < M3U_PATH_CAP; i++) {
        out[used++] = entry[i];
    }
    out[used] = '\0';
    collapse_dots(out);
}

/* Strip a leading "X:" drive designator and leading '/' characters,
 * writing the remainder (still '/'-separated) into out. */
static void root_relative(const char *entry, char *out)
{
    const char *p = entry;
    if (((p[0] >= 'A' && p[0] <= 'Z') || (p[0] >= 'a' && p[0] <= 'z')) && p[1] == ':') {
        p += 2;
    }
    while (*p == '/') {
        p++;
    }
    x_strcpy(out, p, M3U_PATH_CAP);
}

static bool has_drive_prefix(const char *entry)
{
    return ((entry[0] >= 'A' && entry[0] <= 'Z') || (entry[0] >= 'a' && entry[0] <= 'z')) &&
           entry[1] == ':';
}

static bool is_url(const char *entry)
{
    return x_strstr(entry, "://") != NULL;
}

/* ------------------------------------------------------------------ */
/* Streaming line reader                                               */
/* ------------------------------------------------------------------ */

enum { READER_CHUNK = 512 };

typedef struct Reader {
    const M3uFs *fs;
    void *fh;
    uint32_t size;
    uint32_t offset;
    bool utf8;
    bool failed;
    uint8_t chunk[READER_CHUNK];
    uint32_t chunk_start;
    uint32_t chunk_len;
} Reader;

static bool reader_byte(Reader *r, uint32_t off, uint8_t *value)
{
    if (off >= r->size) {
        return false;
    }
    if (off < r->chunk_start || off >= r->chunk_start + r->chunk_len) {
        uint32_t want = r->size - off < READER_CHUNK ? r->size - off : READER_CHUNK;
        int got = r->fs->read(r->fs->ctx, r->fh, off, r->chunk, want);
        if (got <= 0 || (uint32_t)got > want) {
            r->failed = true;
            return false;
        }
        r->chunk_start = off;
        r->chunk_len = (uint32_t)got;
    }
    *value = r->chunk[off - r->chunk_start];
    return true;
}

static bool sniff_utf8(Reader *r)
{
    uint32_t off = 0;
    uint8_t lead = 0;
    while (reader_byte(r, off, &lead)) {
        uint32_t len = utf8_seq_len(lead);
        if (len == 0) {
            return false;
        }
        for (uint32_t i = 1; i < len; i++) {
            uint8_t next = 0;
            if (!reader_byte(r, off + i, &next)) {
                return false;
            }
            if (i == 1 ? !utf8_second_ok(lead, next) : (next < 0x80 || next > 0xBF)) {
                return false;
            }
        }
        off += len;
    }
    return true;
}

static bool reader_open(Reader *r, const M3uFs *fs, const char *path)
{
    r->fs = fs;
    r->fh = fs->open(fs->ctx, path);
    if (r->fh == NULL) {
        return false;
    }
    r->size = fs->size(fs->ctx, r->fh);
    r->offset = 0;
    r->chunk_start = 0;
    r->chunk_len = 0;
    r->failed = false;
    r->utf8 = sniff_utf8(r);
    if (r->failed) {
        fs->close(fs->ctx, r->fh);
        return false;
    }
    if (r->utf8) {
        uint8_t b[3];
        if (reader_byte(r, 0, &b[0]) && reader_byte(r, 1, &b[1]) && reader_byte(r, 2, &b[2]) &&
            b[0] == 0xEF && b[1] == 0xBB && b[2] == 0xBF) {
            r->offset = 3;
        }
    }
    return true;
}

static uint32_t reader_next_cp(Reader *r)
{
    uint8_t lead = 0;
    if (!reader_byte(r, r->offset++, &lead)) {
        return 0;
    }
    if (!r->utf8) {
        if (lead >= 0x80 && lead < 0xA0) {
            return CP1252_HIGH[lead - 0x80];
        }
        return lead;
    }
    uint32_t len = utf8_seq_len(lead);
    uint32_t cp = len == 1 ? lead : (lead & (0x7Fu >> len));
    if (len == 0) {
        return 0xFFFD;
    }
    for (uint32_t i = 1; i < len; i++) {
        uint8_t next = 0;
        if (!reader_byte(r, r->offset++, &next)) {
            return 0;
        }
        cp = (cp << 6) | (next & 0x3F);
    }
    return cp;
}

static bool cp_is_space(uint32_t cp)
{
    return cp == ' ' || (cp >= 0x09 && cp <= 0x0D) || cp == 0x85 || cp == 0xA0 ||
           cp == 0x1680 || (cp >= 0x2000 && cp <= 0x200A) || cp == 0x2028 || cp == 0x2029 ||
           cp == 0x202F || cp == 0x205F || cp == 0x3000;
}

static bool cp_is_break(uint32_t cp, bool utf8)
{
    if (cp == '\n' || cp == '\r') {
        return true;
    }
    return utf8 && (cp == 0x85 || cp == 0x2028 || cp == 0x2029);
}

/* Read one logical line into out (UTF-8, trimmed of leading/trailing
 * whitespace). Returns false at end of input. */
static bool reader_line(Reader *r, char *out, uint32_t cap)
{
    uint32_t len = 0;
    uint32_t content_end = 0;
    if (r->offset >= r->size) {
        return false;
    }
    while (r->offset < r->size) {
        uint32_t cp = reader_next_cp(r);
        if (r->failed) {
            return false;
        }
        if (cp_is_break(cp, r->utf8)) {
            if (cp == '\r') {
                uint8_t next = 0;
                if (reader_byte(r, r->offset, &next) && next == '\n') {
                    r->offset++;
                }
            }
            break;
        }
        if (len == 0 && cp_is_space(cp)) {
            continue;
        }
        uint32_t room = (len + 1 < cap) ? (cap - 1 - len) : 0;
        uint32_t wrote = room > 0 ? utf8_encode(cp, out + len, room) : 0;
        len += wrote;
        if (!cp_is_space(cp)) {
            content_end = len;
        }
    }
    if (cap > 0) {
        out[content_end < cap ? content_end : cap - 1] = '\0';
    }
    return true;
}

/* ------------------------------------------------------------------ */
/* #EXTINF                                                             */
/* ------------------------------------------------------------------ */

typedef struct Meta {
    bool present;
    int32_t duration_s;
    char title[M3U_TEXT_CAP];
    char artist[M3U_TEXT_CAP];
} Meta;

static void meta_clear(Meta *m)
{
    m->present = false;
    m->duration_s = -1;
    m->title[0] = '\0';
    m->artist[0] = '\0';
}

/* Parse "#EXTINF:<dur>,<text>" (the line is known to start with '#'). */
static void meta_parse(const char *line, Meta *m)
{
    const char *p;
    const char *comma;
    meta_clear(m);
    if (!x_starts(line, "#EXTINF:")) {
        return;
    }
    m->present = true;
    p = line + 8;
    /* duration: optional sign + digits; anything else leaves -1 */
    {
        bool neg = false;
        bool any = false;
        uint32_t value = 0;
        bool overflow = false;
        if (*p == '-' || *p == '+') {
            neg = *p == '-';
            p++;
        }
        while (*p >= '0' && *p <= '9') {
            uint32_t digit = (uint32_t)(*p - '0');
            uint32_t limit = neg ? 2147483648u : 2147483647u;
            if (value > (limit - digit) / 10u) {
                overflow = true;
            } else if (!overflow) {
                value = value * 10u + digit;
            }
            any = true;
            p++;
        }
        if (any && !overflow) {
            m->duration_s = neg && value == 2147483648u
                ? (-2147483647 - 1)
                : neg ? -(int32_t)value : (int32_t)value;
        }
    }
    comma = p;
    while (*comma != '\0' && *comma != ',') {
        comma++;
    }
    if (*comma != ',') {
        return;
    }
    p = comma + 1;
    while (*p == ' ' || *p == '\t') {
        p++;
    }
    /* "Artist - Title" split on the first " - ", else all title. */
    {
        const char *sep = x_strstr(p, " - ");
        if (sep != NULL) {
            uint32_t alen = (uint32_t)(sep - p);
            if (alen >= M3U_TEXT_CAP) {
                alen = M3U_TEXT_CAP - 1;
            }
            for (uint32_t i = 0; i < alen; i++) {
                m->artist[i] = p[i];
            }
            m->artist[alen] = '\0';
            x_strcpy(m->title, sep + 3, M3U_TEXT_CAP);
        } else {
            x_strcpy(m->title, p, M3U_TEXT_CAP);
        }
    }
    /* trim trailing spaces of title */
    {
        uint32_t n = x_strlen(m->title);
        while (n > 0 && (m->title[n - 1] == ' ' || m->title[n - 1] == '\t')) {
            m->title[--n] = '\0';
        }
    }
}

/* ------------------------------------------------------------------ */
/* Resolver                                                            */
/* ------------------------------------------------------------------ */

static bool stat_path(const M3uFs *fs, const char *path, M3uFileInfo *info)
{
    return fs->stat(fs->ctx, path, info) == 0 && !info->is_dir;
}

/* Stage 3: unique longest case-folded component-suffix match across
 * the whole library. A tie for the best score counts as not found
 * (same rule as the reference implementation). */
static bool resolve_suffix(const M3uFs *fs, const char *entry, M3uFileInfo *info)
{
    char wanted_text[M3U_PATH_CAP];
    Parts wanted;
    uint32_t best_score = 0;
    uint32_t best_count = 0;
    M3uFileInfo best_info = {0, 0, false};
    uint32_t total = fs->lib_count(fs->ctx);

    fold_parts(entry, wanted_text, sizeof wanted_text, &wanted);
    if (wanted.count == 0) {
        return false;
    }
    for (uint32_t i = 0; i < total; i++) {
        char cand_path[M3U_PATH_CAP];
        char cand_text[M3U_PATH_CAP];
        Parts cand;
        M3uFileInfo cand_info;
        if (fs->lib_nth(fs->ctx, i, cand_path, sizeof cand_path, &cand_info) != 0 ||
            cand_info.is_dir) {
            continue;
        }
        fold_parts(cand_path, cand_text, sizeof cand_text, &cand);
        if (cand.count == 0) {
            continue;
        }
        /* prefilter: last components must agree */
        if (!span_equal(wanted_text, wanted.spans[wanted.count - 1], cand_text,
                        cand.spans[cand.count - 1])) {
            continue;
        }
        uint32_t score = common_suffix(wanted_text, &wanted, cand_text, &cand);
        if (score > best_score) {
            best_score = score;
            best_count = 1;
            best_info = cand_info;
        } else if (score == best_score) {
            best_count++;
        }
    }
    if (best_count == 1 && best_score > 0) {
        *info = best_info;
        return true;
    }
    return false;
}

static bool resolve_entry(const M3uFs *fs, const char *folder, const char *raw_entry,
                          M3uFileInfo *info)
{
    char entry[M3U_PATH_CAP];
    x_strcpy(entry, raw_entry, sizeof entry);
    normalise_separators(entry);

    /* Stage 1: relative to the playlist's own folder. Absolute and
     * drive-prefixed entries cannot be folder-relative. */
    if (entry[0] != '/' && !has_drive_prefix(entry)) {
        char joined[M3U_PATH_CAP];
        join_path(folder, entry, joined);
        if (stat_path(fs, joined, info)) {
            return true;
        }
    }
    /* Stage 2: relative to the volume root (drive designator and
     * leading separators stripped). */
    {
        char rel[M3U_PATH_CAP];
        char abs_path[M3U_PATH_CAP];
        root_relative(entry, rel);
        abs_path[0] = '/';
        x_strcpy(abs_path + 1, rel, sizeof abs_path - 1);
        collapse_dots(abs_path);
        if (stat_path(fs, abs_path, info)) {
            return true;
        }
    }
    /* Stage 3: case-folded suffix match over the library. */
    return resolve_suffix(fs, entry, info);
}

/* ------------------------------------------------------------------ */
/* Entry point                                                         */
/* ------------------------------------------------------------------ */

int m3u_import(const M3uFs *fs, const char *playlist_path, M3uTrack *out, uint32_t out_cap,
               M3uStats *stats)
{
    Reader reader;
    M3uStats local_stats = {0, 0, 0, 0, 0};
    Meta meta;
    char folder[M3U_PATH_CAP];
    char line[M3U_LINE_CAP];
    uint32_t written = 0;

    meta_clear(&meta);

    /* The playlist's folder: playlist_path up to the last '/'. */
    {
        uint32_t n = x_strlen(playlist_path);
        uint32_t cut = 0;
        for (uint32_t i = 0; i < n; i++) {
            if (playlist_path[i] == '/') {
                cut = i;
            }
        }
        if (cut == 0) {
            folder[0] = '/';
            folder[1] = '\0';
        } else {
            if (cut >= sizeof folder) {
                cut = sizeof folder - 1;
            }
            for (uint32_t i = 0; i < cut; i++) {
                folder[i] = playlist_path[i];
            }
            folder[cut] = '\0';
        }
    }

    if (!reader_open(&reader, fs, playlist_path)) {
        return -1;
    }

    while (reader_line(&reader, line, sizeof line)) {
        if (line[0] == '\0') {
            continue;
        }
        if (line[0] == '#') {
            if (x_starts(line, "#EXTINF:")) {
                meta_parse(line, &meta);
            }
            continue;
        }
        local_stats.total_entries++;
        if (is_url(line)) {
            local_stats.skipped_url++;
            meta_clear(&meta);
            continue;
        }
        {
            M3uFileInfo info;
            if (resolve_entry(fs, folder, line, &info)) {
                if (written < out_cap) {
                    M3uTrack *t = &out[written++];
                    t->clus = info.clus;
                    t->index = info.index;
                    t->duration_s = meta.duration_s;
                    t->has_meta = meta.present;
                    x_strcpy(t->title, meta.title, M3U_TEXT_CAP);
                    x_strcpy(t->artist, meta.artist, M3U_TEXT_CAP);
                    local_stats.resolved++;
                } else {
                    local_stats.overflow++;
                }
            } else {
                local_stats.skipped_missing++;
            }
        }
        meta_clear(&meta);
    }

    fs->close(fs->ctx, reader.fh);
    if (reader.failed) {
        return -1;
    }
    if (stats != NULL) {
        *stats = local_stats;
    }
    return 0;
}
