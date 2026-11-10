#include "frame_average.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    /* For height 4, two rows are needed; lower rows must never be fed. */
    const uint8_t red[] = {0x00,0xf8, 0x00,0xf8, 0x00,0xf8};
    const uint8_t blue[] = {0x1f,0x00, 0x1f,0x00, 0x1f,0x00};
    const uint8_t be[] = {0xf8,0x00, 0x00,0x1f};
    TheaterTopAverage state;
    uint8_t out[3] = {9, 9, 9};
    assert(theater_top_init(&state, 3, 4, 0));
    assert(theater_top_row(&state, red, sizeof red));
    assert(!theater_top_finish(&state, out));
    assert(!theater_top_row(&state, blue, sizeof blue - 1));
    assert(state.rows_seen == 1);
    assert(theater_top_row(&state, blue, sizeof blue));
    assert(!theater_top_row(&state, red, sizeof red));
    assert(theater_top_finish(&state, out));
    assert(out[0] == 128 && out[1] == 0 && out[2] == 128);
    assert(theater_top_init(&state, 2, 1, 1));
    assert(theater_top_row(&state, be, sizeof be));
    assert(theater_top_finish(&state, out));
    assert(out[0] == 128 && out[1] == 0 && out[2] == 128);
    memset(out, 9, sizeof out);
    assert(!theater_top_init(&state, 0, 1, 0));
    assert(!theater_top_finish(&state, out));
    assert(!theater_top_init(&state, 2, 1, 2));
    assert(out[0] == 9 && out[1] == 9 && out[2] == 9);
    puts("PASS: top-third streaming, rounding, endianness and bounds");
    return 0;
}
