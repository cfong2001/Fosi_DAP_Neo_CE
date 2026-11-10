#ifndef THEATER_FRAME_AVERAGE_H
#define THEATER_FRAME_AVERAGE_H
#include <stddef.h>
#include <stdint.h>

/* Caller-owned state: never persist across pictures. Feed the first
 * ceil(height/3) rendered RGB565 rows, in order, then finish. The
 * byte order is explicit because the complete decoder path is still
 * under investigation. No memory is allocated or retained. */
typedef struct {
    uint64_t sum[3];
    uint32_t width, rows_needed, rows_seen;
    int big_endian;
} TheaterTopAverage;
int theater_top_init(TheaterTopAverage *state, uint32_t width,
                     uint32_t height, int big_endian);
int theater_top_row(TheaterTopAverage *state, const uint8_t *row, size_t length);
int theater_top_finish(const TheaterTopAverage *state, uint8_t out[3]);
#endif
