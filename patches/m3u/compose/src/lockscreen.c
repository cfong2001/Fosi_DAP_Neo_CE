/* Lock-screen title routine for the module 31 painter (Fosi DAP Neo).
 *
 * Entered by B.W from patch 0033 at module 31 code 0x0307E89E, the tail
 * of the painter's flag-0x2E segment. Entry state (pinned in
 * work/ui_features/renderer/renderer.md): the flag is already
 * test-cleared, {r4, lr} are already popped, and r0 holds the DrawImage
 * argument, 0x26 plus bit 2 of the byte at 0x030230EC. The displaced
 * stock instruction is the tail call B.W DrawImage; this routine
 * performs that call first, exactly as stock, then adds text.
 *
 * Stage 1 (title): if SAVEINFO +0x60 == 1 (the same gate the name
 * buffer's snapshot uses), draw the track title from the UTF-16 name
 * buffer at 0x030235CE through the stock text routine 0x03062CEE, with
 * the pen colours and display-mode bracket module 31's own Display uses
 * around its string calls.
 *
 * Stage 2 (elapsed / total): separately gated on the playback state
 * field (+0x44 == 1), a non-null codec object, and a positive segment
 * length. Both values are segment-relative, matching module 27's own
 * arithmetic: elapsed = codec-object live position (+4) minus the
 * latched segment start (+0x48), clamped at zero; total = +0x4C minus
 * +0x48. Formatted as m:ss / m:ss into a UTF-16 buffer and drawn
 * through the same text routine. +0x48 is latched, so the readout is
 * elapsed-from-segment-start; no other meaning is claimed for it.
 *
 * Placement: linked at the module 31 segment extension base
 * 0x0307EE48 for this scratch build (see lockscreen.ld). Final
 * placement is the same extension; only the link base and the patch
 * 0033 branch target change if the extension base moves.
 */
#include <stdint.h>

#define STOCK_FN(ret, name, addr, args) \
    static ret (*const name) args = (ret (*) args)((addr) | 1u)

STOCK_FN(void, draw_image,      0x03063700, (uint32_t image));
STOCK_FN(uint32_t, mode_set,    0x0306316E, (uint32_t mode));
STOCK_FN(void, text_draw,       0x03062CEE, (const void *desc0,
                                             const void *desc1,
                                             const uint16_t *str,
                                             uint32_t flags));

#define SAVEINFO     ((volatile uint8_t *)0x030232A0u)
#define NAME_BUF     ((const uint16_t *)0x030235CEu)
#define DISP_CTX     ((volatile uint16_t *)0x0302385Cu) /* +0, +2: pen colours */
#define COLOR_CELL_A (*(volatile uint16_t *)0x030235B6u)
#define COLOR_CELL_B (*(volatile uint16_t *)0x03023144u)
#define FILEINFO     ((volatile uint32_t *)0x03023980u)
#define FI_STATE     0x44u
#define FI_LATCHED   0x48u
#define FI_TOTAL     0x4Cu
#define CODEC_OBJ_PP ((volatile uint32_t *)0x0304AD78u)

/* Stage 2 text buffer. In .data (not .bss): the extension payload is a
 * plain byte copy, so every writable byte the routine uses must be
 * carried in the blob image itself. Worst case text is
 * "71582:47 / 71582:47" plus the NUL, 20 halfwords, when both
 * unsigned millisecond counters are at their maximum. */
static uint16_t time_text[20] __attribute__((section(".data"), used));

static uint16_t *put_dec(uint16_t *p, uint32_t v)
{
    uint16_t tmp[10];
    int n = 0;
    do {
        tmp[n++] = (uint16_t)(0x30u + (v % 10u));
        v /= 10u;
    } while (v != 0u);
    while (n > 0) {
        *p++ = tmp[--n];
    }
    return p;
}

static uint16_t *put_time(uint16_t *p, uint32_t seconds)
{
    uint32_t min = seconds / 60u;
    uint32_t sec = seconds - min * 60u;
    p = put_dec(p, min);
    *p++ = (uint16_t)':';
    *p++ = (uint16_t)(0x30u + sec / 10u);
    *p++ = (uint16_t)(0x30u + sec % 10u);
    return p;
}

__attribute__((section(".text.entry"), used))
void ui_lockscreen_paint(uint32_t image)
{
    /* 1. The displaced tail call, with r0 unchanged. */
    draw_image(image);

    /* 2. The gate: SAVEINFO +0x60 must be 1. */
    if (SAVEINFO[0x60] != 1u) {
        return;
    }

    /* 3. Pen colours the way module 31 Display sets them, then the
     * display-mode bracket Display wraps around its string calls. */
    uint16_t saved_fg = DISP_CTX[0];
    uint16_t saved_bg = DISP_CTX[1];
    DISP_CTX[0] = COLOR_CELL_A;
    DISP_CTX[1] = COLOR_CELL_B;
    uint32_t saved_mode = mode_set(1u);

    /* Title descriptor {x_left 11, y_top 24, x_right 231, y_bottom 39}:
     * Display's proven x extent and 16 px strip (y_bottom = y_top + 15);
     * y_top 24 sits directly below the status icon row. */
    uint16_t desc[4];
    desc[0] = 11u;
    desc[1] = 24u;
    desc[2] = 231u;
    desc[3] = 39u;
    text_draw(desc, desc, NAME_BUF, 0u);

    /* Stage 2: elapsed / total, segment-relative (see header). Own
     * gate, own descriptor {11, 40, 231, 55}. */
    uint32_t state   = FILEINFO[FI_STATE / 4u];
    uint32_t latched = FILEINFO[FI_LATCHED / 4u];
    uint32_t total   = FILEINFO[FI_TOTAL / 4u];
    if (state == 1u && total > latched) {
        uint32_t obj = *CODEC_OBJ_PP;
        if (obj != 0u) {
            uint32_t live = *(volatile uint32_t *)(uintptr_t)(obj + 4u);
            uint32_t elapsed_ms = (live >= latched) ? (live - latched) : 0u;
            uint32_t total_ms = total - latched;
            uint16_t *p = time_text;
            p = put_time(p, elapsed_ms / 1000u);
            *p++ = (uint16_t)' ';
            *p++ = (uint16_t)'/';
            *p++ = (uint16_t)' ';
            p = put_time(p, total_ms / 1000u);
            *p = 0u;
            desc[1] = 40u;
            desc[3] = 55u;
            text_draw(desc, desc, time_text, 0u);
        }
    }

    mode_set(saved_mode);
    DISP_CTX[0] = saved_fg;
    DISP_CTX[1] = saved_bg;
}
