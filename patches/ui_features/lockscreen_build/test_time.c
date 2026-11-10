/* Host boundary test for the exact UTF-16 buffer used by the firmware. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "src/lockscreen.c"

int main(void)
{
    struct { uint16_t text[20]; uint16_t guard; } b = {{0}, 0x5a5a};
    uint16_t *p = b.text;
    p = put_time(p, UINT32_MAX / 1000u);
    *p++ = ' '; *p++ = '/'; *p++ = ' ';
    p = put_time(p, UINT32_MAX / 1000u);
    *p++ = 0;
    const char *expected = "71582:47 / 71582:47";
    for (unsigned i = 0; expected[i]; i++) assert(b.text[i] == expected[i]);
    assert(p == b.text + 20 && b.text[19] == 0 && b.guard == 0x5a5a);
    puts("lock-screen maximum duration fits the UTF-16 buffer");
    return 0;
}
