/*
 * Bluetooth shortcut toggle for the Fosi DAP Neo (DP3_V137).
 *
 * Freestanding C for the module-0 extension blob (exec base 0x03079C14).
 * Transcribes the stock power sequences reassembled in the UI design doc
 * (work/ui_features/ui_features.md, section 4):
 *   - power on:  module 81 build of the BT power routine at 0x0307D1A8,
 *     plus the module 21 restart-cycle envelope (post flag 0x123, UART
 *     re-init 0x03053242, 100 ms settle, post-on state bytes, command
 *     0x53 send, tick-counter copy) in stock order.
 *   - power off: GPIO low sequence (modules 21/32/81 all agree), state
 *     bytes SAVEINFO +0x2D4/+0x2D3 cleared, status byte cleared,
 *     200 ms settle (module 21 cycle timing).
 * All helpers are module-0 resident; no overlay code is called.
 */
#include <stdint.h>

#define STOCK_FN(ret, name, addr, args) \
    static ret (*const name) args = (ret (*) args)((addr) | 1u)

STOCK_FN(void, gpio_mux,       0x030526F8, (uint32_t port, uint32_t pin, uint32_t mode));
STOCK_FN(void, gpio_dir,       0x03056098, (uint32_t port, uint32_t pin, uint32_t dir));
STOCK_FN(void, gpio_level,     0x030560D2, (uint32_t port, uint32_t pin, uint32_t level));
STOCK_FN(void, delay_ms,       0x03064944, (uint32_t ms));
STOCK_FN(void, flag_post,      0x0306723C, (uint32_t flag));
STOCK_FN(uint32_t, flag_testclear, 0x03067258, (uint32_t flag));
STOCK_FN(void, sys_idle_poll,  0x030611E0, (void));
STOCK_FN(void, bt_uart_init,   0x03053242, (void));
STOCK_FN(void, bt_send_cmd,    0x03065772, (uint32_t cmd));

#define SAVEINFO    ((volatile uint8_t *)0x030232A0u)
#define SI_BT_ON    0x2D4   /* bluetooth on/off state byte */
#define SI_BT_MODE  0x2D3   /* companion state byte */
#define BT_VERBYTE  (*(volatile uint8_t *)0x03023124u)  /* power-on result */
#define BT_STATUS   (*(volatile uint8_t *)0x0300411Cu)  /* power routine status */
#define BT_RESP     ((volatile uint8_t *)0x0300642Cu)   /* 'CV1x' banner buffer */
#define BYTE_416C   (*(volatile uint8_t *)0x0300416Cu)  /* module 21 post-on writes */
#define BYTE_416E   (*(volatile uint8_t *)0x0300416Eu)
#define BYTE_416F   (*(volatile uint8_t *)0x0300416Fu)
#define TICK_COPY   (*(volatile uint32_t *)0x03004174u)
#define TICK_SRC    (*(volatile uint32_t *)0x03023298u)

static void bt_gpio_low_all(void)
{
    gpio_mux(2, 7, 0);   gpio_dir(2, 7, 1);   gpio_level(2, 7, 0);
    gpio_mux(2, 17, 0);  gpio_dir(2, 17, 1);  gpio_level(2, 17, 0);
    gpio_mux(2, 16, 0);  gpio_dir(2, 16, 1);  gpio_level(2, 16, 0);
}

/* Word-for-word transcription of the module 81 power-on build
 * (0x0307D1A8-0x0307D29A): raise pin 7, wait up to 5000 ms for the
 * receive flag 0x1B2 carrying the 'CV1' banner, classify into the
 * result byte, power back down on timeout. */
static uint32_t bt_power_on(void)
{
    uint32_t remain = 5000;

    gpio_mux(2, 7, 0);
    gpio_dir(2, 7, 1);
    gpio_level(2, 7, 1);
    SAVEINFO[SI_BT_ON] = 1;

    for (;;) {
        sys_idle_poll();
        if (flag_testclear(0x1B2)) {
            flag_post(0x1B4);
            if (BT_RESP[0] == 0x43 && BT_RESP[1] == 0x56 && BT_RESP[2] == 0x31) {
                BT_VERBYTE = (BT_RESP[3] == 0x35) ? 5 : 0;
                BT_STATUS = 0;
                if (remain != 0) {
                    delay_ms(10);
                    return remain;
                }
                break;  /* stock falls into the timeout path here */
            }
        }
        remain = (uint16_t)(remain - 1);
        delay_ms(1);
        if (remain == 0)
            break;
    }

    BT_STATUS = 7;
    bt_gpio_low_all();
    SAVEINFO[SI_BT_ON] = 0;
    delay_ms(10);
    return 0;
}

void bt_toggle(void)
{
    if (SAVEINFO[SI_BT_ON] == 1) {
        /* Off: module 21 off-phase / module 32 apply path. */
        BT_STATUS = 0;
        bt_gpio_low_all();
        SAVEINFO[SI_BT_ON] = 0;
        SAVEINFO[SI_BT_MODE] = 0;
        delay_ms(200);
    } else {
        /* On: module 21 restart cycle minus the off-phase (already off),
         * in stock order: post 0x123, UART re-init, 100 ms settle,
         * power-on routine, then the post-on state writes and command
         * send. Deviation from module 21's letter, deliberate: module 21
         * runs the post-on writes unconditionally because its cycle
         * restarts a module that was live 200 ms earlier; here the
         * envelope runs only when the power-on routine reports success
         * (nonzero return), so a banner timeout leaves the state byte
         * at the 0 the routine itself wrote instead of claiming on. */
        uint32_t ok;
        flag_post(0x123);
        bt_uart_init();
        delay_ms(100);
        ok = bt_power_on();
        if (ok != 0) {
            BYTE_416C = 1;
            BYTE_416E = 0;
            bt_send_cmd(0x53);
            SAVEINFO[SI_BT_MODE] = 0;
            BYTE_416F = 0;
            TICK_COPY = TICK_SRC;
        }
    }
}
