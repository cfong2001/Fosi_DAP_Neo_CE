#include "frame_average.h"

int theater_top_init(TheaterTopAverage *state, uint32_t width,
                     uint32_t height, int big_endian)
{
    if (!state) return 0;
    state->width = state->rows_needed = state->rows_seen = 0;
    state->sum[0] = state->sum[1] = state->sum[2] = 0;
    state->big_endian = 0;
    if (!width || !height || width > 8192u || height > 8192u ||
        (big_endian != 0 && big_endian != 1)) return 0;
    state->width = width;
    state->rows_needed = (height + 2u) / 3u;
    state->rows_seen = 0;
    state->big_endian = big_endian;
    return 1;
}

int theater_top_row(TheaterTopAverage *state, const uint8_t *row, size_t length)
{
    if (!state || !row || !state->width || state->width > 8192u ||
        !state->rows_needed || state->rows_needed > 2731u ||
        state->rows_seen >= state->rows_needed || length < (size_t)state->width * 2u ||
        (state->big_endian != 0 && state->big_endian != 1)) return 0;
    for (uint32_t x = 0; x < state->width; x++) {
        const uint8_t *p = row + (size_t)x * 2u;
        uint16_t word = state->big_endian ? (uint16_t)(((uint16_t)p[0] << 8) | p[1])
                                          : (uint16_t)(((uint16_t)p[1] << 8) | p[0]);
        state->sum[0] += ((word >> 11) & 31u) * 255u / 31u;
        state->sum[1] += ((word >> 5) & 63u) * 255u / 63u;
        state->sum[2] += (word & 31u) * 255u / 31u;
    }
    state->rows_seen++;
    return 1;
}

int theater_top_finish(const TheaterTopAverage *state, uint8_t out[3])
{
    if (!state || !out || !state->width || state->width > 8192u ||
        !state->rows_needed || state->rows_needed > 2731u ||
        state->rows_seen != state->rows_needed) return 0;
    uint32_t count = state->width * state->rows_seen;
    for (unsigned c = 0; c < 3; c++) out[c] = (uint8_t)((state->sum[c] + count / 2u) / count);
    return 1;
}
