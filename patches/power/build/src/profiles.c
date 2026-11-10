/*
 * Battery profiles: defaults writer, selector entry, and apply routine.
 *
 * Design: patches/power/power.md, job 2 (storage layout, apply path,
 * migration) and job 3 (selector hook). This file is the build of that
 * design. It is freestanding: no library calls, no state of its own.
 * The selected profile and some stock fields live in SAVEINFO. Timer
 * and clock-table changes are transient: there is no profile boot hook.
 *
 * Placement: this code is linked into the module 32 segment extension
 * (see profiles.ld and power_build.md for the residency argument). Its
 * only caller is module 32's settings apply dispatch, reached through
 * the cave stubs in hooks.S. Every stock function and data target it
 * uses is module 0 resident, so an overlay home can reach all of it.
 */

#include <stdint.h>

typedef uint8_t u8;
typedef uint32_t u32;

/* ------------------------------------------------------------------ */
/* Stock addresses, each re-verified against the extracted segments.   */

/* SAVEINFO live struct base. Module 32's apply paths use it as r6:
 * item 173 writes [r6, 0x68], item 196 writes [r6, 0x14], and the
 * literal 0x030232A0 sits in module 32's literal pools (first at exec
 * 0x0307DEF8). */
#define SAVEINFO_BASE 0x030232A0u

/* TimerPeriodSet (module 0, 0x030510A2). Argument layout proven from
 * its body and from the key init call site at module 1 exec
 * 0x0307D2DE: r0 = timer number, r2:r3 = 64-bit period in
 * microseconds (low:high), first stack argument = nanosecond part.
 * r1 is not read by the callee. The body stores r2:r3 to the timer
 * registers and reprograms the timer, the same call key init makes. */
typedef void (*timer_period_set_t)(u32 timer, u32 unused, u32 us_lo,
                                   u32 us_hi, u32 ns);
static timer_period_set_t const stock_timer_period_set =
    (timer_period_set_t)(0x030510A2u | 1u);

/* Backlight apply (module 0, 0x03064964). Called by module 32's item
 * 196 path at exec 0x0307DF88 with r0 still holding the level byte it
 * just wrote to SAVEINFO +0x14; the callee body indexes its duty
 * table with r0. So the argument is the level, not a channel. */
typedef void (*backlight_apply_t)(u32 level);
static backlight_apply_t const stock_backlight_apply =
    (backlight_apply_t)(0x03064964u | 1u);

/* Event flag post (module 0, 0x0306723C): r0 = flag id, sets the bit
 * in the flag bitmap. Module 32 posts 0xFB after an EQ change and
 * 0xC6 as its generic settings-changed flag through this function. */
typedef void (*flag_post_t)(u32 flag);
static flag_post_t const stock_flag_post = (flag_post_t)(0x0306723Cu | 1u);

/* SAVEINFO saver (module 0, 0x0306CA10): r0 != 0 sets the commit
 * marker at struct +0x2F4, then the checksum (struct +0x2FC, over
 * [0, +0x2FC)) is recomputed and the struct is written out. */
typedef void (*saver_t)(u32 commit);
static saver_t const stock_saver = (saver_t)(0x0306CA10u | 1u);

/* RAM clock table (module 0 exec 0x03079824): 36 rows of 7 words.
 * Word 0 is the row id (never written here), words 1..4 are PLL and
 * the A fields (never written here), word 5 is B core, word 6 is
 * B bus. The clock solver 0x03066EFC reads the table on every
 * request and release, so writes take effect at the next transition. */
#define CLOCK_TABLE ((volatile u32 *)0x03079824u)
#define CLOCK_ROW_WORDS 7u
#define CLOCK_B_CORE 5u
#define CLOCK_B_BUS 6u

/* ------------------------------------------------------------------ */
/* Profile area layout (design job 2, storage table).                  */

#define SI(off) (*(volatile u8 *)(SAVEINFO_BASE + (u32)(off)))

#define SI_BRIGHTNESS 0x14u /* stock level byte */
#define SI_EQ_SELECT 0x68u  /* stock EQ selector byte */
#define SI_BT_STATE 0x2D4u  /* stock Bluetooth state byte */

#define PROF_BASE 0x290u
#define PROF_MAGIC0 0x50u /* 'P' */
#define PROF_MAGIC1 0x46u /* 'F' */
#define PROF_VERSION 1u
#define PROF_ACTIVE (PROF_BASE + 3u) /* +0x293 */
#define PROF_FLAGS (PROF_BASE + 4u)  /* +0x294 */
#define PROF_FLAG_USER_WRITTEN 0x01u
#define PROF_ENTRIES (PROF_BASE + 8u) /* +0x298 */
#define PROF_ENTRY_LEN 8u
#define PROF_COUNT 3u

#define ENTRY_WHEEL 0u
#define ENTRY_BRIGHTNESS 1u
#define ENTRY_BT 2u
#define ENTRY_EQ 3u
#define ENTRY_CLOCK 4u

#define LEAVE 0xFFu /* entry byte value: leave the stock field alone */

#define WHEEL_CODE_400US 0u
#define WHEEL_CODE_1000US 1u
#define WHEEL_400US 400u
#define WHEEL_1000US 1000u

/* ------------------------------------------------------------------ */
/* Clock values.                                                       */
/*                                                                     */
/* The restore set is the clock v1 state of the managed fields: the   */
/* apply routine manages the table, so every apply writes the full    */
/* managed set for the active policy, computed from these base        */
/* values. That makes policies order-independent (switching cap B     */
/* back to cap A restores the EQ rows) and idempotent.                */
/*                                                                     */
/* Rows 18..22 (FLAC, ALAC, APE, DSD-DFF, DSD-DSF): clock v1 set the  */
/* B fields to 288 MHz (patches 0014..0018 in the framework series).  */
/* Rows 23..25 (EQ tiers): clock v1 did not touch them, so the base   */
/* values are the stock 36, 72 and 140 MHz, read from the table in    */
/* the extracted module 0 segment.                                    */

#define HZ_288M 288000000u /* clock v1 B value, rows 18..22 */
#define HZ_36M 36000000u   /* stock row 23 */
#define HZ_72M 72000000u   /* stock row 24 */
#define HZ_140M 140000000u /* stock row 25 */

#define CLOCK_ROW_FIRST 18u
#define CLOCK_ROW_LAST 25u
#define CLOCK_LOSSLESS_ROWS 5u /* rows 18..22 */

/* Cap values are the design's proposed values (power.md job 2 and
 * open item 3): cap A caps the lossless rows' B fields at 240 MHz,
 * the tier clock v1 proved for OGG; cap B additionally caps the EQ
 * rows at the 72 MHz tier. Only a hardware listening test can clear
 * 240 MHz for FLAC; policy 0 (no cap) is exactly the shipped clock
 * v1 behaviour and needs no validation. */
#define CAP_A_HZ 240000000u
#define CAP_B_EQ_HZ 72000000u

#define CLOCK_POLICY_NONE 0u
#define CLOCK_POLICY_CAP_A 1u
#define CLOCK_POLICY_CAP_B 2u

static const u32 clock_base_b[CLOCK_ROW_LAST - CLOCK_ROW_FIRST + 1u] = {
    HZ_288M, HZ_288M, HZ_288M, HZ_288M, HZ_288M, /* rows 18..22 */
    HZ_36M, HZ_72M, HZ_140M                     /* rows 23..25 */
};

/* ------------------------------------------------------------------ */
/* Default profile entries (design job 2, defaults table).             */
/*                                                                     */
/* PROFILE_BRIGHTNESS_ENDURANCE: the design's Endurance default is    */
/* "the lowest level item 196 offers", a build-phase constant to      */
/* read from item 196's descriptor. That descriptor is built at       */
/* runtime (the design's open item 4) and cannot be read offline,     */
/* so no number is invented here: the shipped value is LEAVE, the     */
/* stock behaviour, until the descriptor is decoded on hardware.      */
/* Fill in the level here when it is known.                           */
#define PROFILE_BRIGHTNESS_ENDURANCE LEAVE

/* PROFILE_EQ_ENDURANCE: the design's Endurance default is selector   */
/* value 0, with the design's own condition (note 2 and open item 4): */
/* confirm preset 0 is the flat/off preset before shipping 0; if it   */
/* is not, the default becomes LEAVE. The confirmation is             */
/* outstanding, so the shipped value is LEAVE. Change to 0u once      */
/* preset 0 is confirmed flat.                                        */
#define PROFILE_EQ_ENDURANCE LEAVE

static const u8 profile_defaults[PROF_COUNT][PROF_ENTRY_LEN] = {
    /* wheel, brightness, bt, eq, clock, reserved... */
    {WHEEL_CODE_400US, LEAVE, LEAVE, LEAVE, CLOCK_POLICY_NONE, 0, 0, 0},
    {WHEEL_CODE_1000US, LEAVE, LEAVE, LEAVE, CLOCK_POLICY_NONE, 0, 0, 0},
    {WHEEL_CODE_1000US, PROFILE_BRIGHTNESS_ENDURANCE, 0u,
     PROFILE_EQ_ENDURANCE, CLOCK_POLICY_CAP_A, 0, 0, 0},
};

/* ------------------------------------------------------------------ */

static int profile_area_valid(void)
{
    return SI(PROF_BASE) == PROF_MAGIC0 && SI(PROF_BASE + 1u) == PROF_MAGIC1 &&
           SI(PROF_BASE + 2u) == PROF_VERSION;
}

/*
 * profiles_write_defaults: one-time initialization of the 32-byte
 * profile area with the default table and the chosen active id.
 * Writes the SAVEINFO struct only; it does not persist (the apply
 * routine's saver call does). Called from profile_select when the
 * magic is absent, so no boot patch is needed.
 */
void profiles_write_defaults(u32 active_id)
{
    u32 i, j;

    SI(PROF_BASE) = PROF_MAGIC0;
    SI(PROF_BASE + 1u) = PROF_MAGIC1;
    SI(PROF_BASE + 2u) = PROF_VERSION;
    SI(PROF_ACTIVE) = (u8)active_id;
    SI(PROF_FLAGS) = PROF_FLAG_USER_WRITTEN;
    SI(PROF_BASE + 5u) = 0u;
    SI(PROF_BASE + 6u) = 0u;
    SI(PROF_BASE + 7u) = 0u;
    for (i = 0u; i < PROF_COUNT; i++) {
        for (j = 0u; j < PROF_ENTRY_LEN; j++) {
            SI(PROF_ENTRIES + i * PROF_ENTRY_LEN + j) =
                profile_defaults[i][j];
        }
    }
}

/*
 * profiles_apply: the runtime apply routine (design job 2, apply
 * path). Performs the design's steps in the design's order; each
 * step writes the stock field itself and uses the stock call the
 * settings window itself uses. The timer and clock settings are not
 * restored from the profile at boot. The saver runs last, including the
 * preceding field writes in one save; write atomicity is unproven.
 * If the profile area fails its magic or version
 * check, nothing is written and nothing is called (the migration
 * fail-safe: stock behaviour, byte for byte).
 */
void profiles_apply(void)
{
    const u32 entry_base = PROF_ENTRIES;
    u32 id, i, policy;
    u8 wheel, brightness, bt, eq;

    if (!profile_area_valid()) {
        return;
    }
    id = SI(PROF_ACTIVE);
    if (id >= PROF_COUNT) {
        return; /* corrupt active id: fail safe, like a bad magic */
    }

    wheel = SI(entry_base + id * PROF_ENTRY_LEN + ENTRY_WHEEL);
    brightness = SI(entry_base + id * PROF_ENTRY_LEN + ENTRY_BRIGHTNESS);
    bt = SI(entry_base + id * PROF_ENTRY_LEN + ENTRY_BT);
    eq = SI(entry_base + id * PROF_ENTRY_LEN + ENTRY_EQ);
    policy = SI(entry_base + id * PROF_ENTRY_LEN + ENTRY_CLOCK);

    /* Step 2, wheel: the same TimerPeriodSet call key init makes. */
    if (wheel == WHEEL_CODE_400US) {
        stock_timer_period_set(0u, 0u, WHEEL_400US, 0u, 0u);
    } else if (wheel == WHEEL_CODE_1000US) {
        stock_timer_period_set(0u, 0u, WHEEL_1000US, 0u, 0u);
    }
    /* An out-of-domain wheel code skips the step, like LEAVE. */

    /* Step 3, brightness: module 32's item 196 pair, write then call
     * with the level as the argument. */
    /* Module 1's boot loader bounds +0x14 to 0..5 at 0x0307DEA8.
     * The backlight routine indexes a byte table without a bounds check. */
    if (brightness <= 5u) {
        SI(SI_BRIGHTNESS) = brightness;
        stock_backlight_apply(brightness);
    }

    /* Step 4, EQ: module 32's item 173 shape, post flag 0xFB only
     * when the value changes, write unconditionally. */
    /* The same loader bounds the EQ selector +0x68 to 0..6. */
    if (eq <= 6u) {
        if (SI(SI_EQ_SELECT) != eq) {
            stock_flag_post(0xFBu);
        }
        SI(SI_EQ_SELECT) = eq;
    }

    /* Step 5, Bluetooth: write the state byte only. Module 81 reads
     * it at its init and state paths; apply does not drive the
     * radio. */
    if (bt <= 1u) {
        SI(SI_BT_STATE) = bt;
    }

    /* Step 6, clock cap: write the managed B fields (rows 18..25,
     * core and bus) to the active policy's values, computed from the
     * clock v1 base set. An out-of-domain policy byte is treated as
     * policy 0 (no cap), which converges the table to the known
     * clock v1 state. */
    if (policy > CLOCK_POLICY_CAP_B) {
        policy = CLOCK_POLICY_NONE;
    }
    for (i = 0u; i <= CLOCK_ROW_LAST - CLOCK_ROW_FIRST; i++) {
        u32 target = clock_base_b[i];
        if (policy >= CLOCK_POLICY_CAP_A && i < CLOCK_LOSSLESS_ROWS &&
            target > CAP_A_HZ) {
            target = CAP_A_HZ;
        }
        if (policy >= CLOCK_POLICY_CAP_B && i >= CLOCK_LOSSLESS_ROWS &&
            target > CAP_B_EQ_HZ) {
            target = CAP_B_EQ_HZ;
        }
        CLOCK_TABLE[(CLOCK_ROW_FIRST + i) * CLOCK_ROW_WORDS + CLOCK_B_CORE] =
            target;
        CLOCK_TABLE[(CLOCK_ROW_FIRST + i) * CLOCK_ROW_WORDS + CLOCK_B_BUS] =
            target;
    }

    /* Step 7, persist: one saver call commits the profile area and
     * every stock field written above. */
    stock_saver(1u);
}

/*
 * profile_select: the selector entry the dispatch caves call with
 * the chosen option index (the item record's value byte, already
 * updated by the stock value editor, exactly as items 173 and 196
 * consume it). First selection writes the full default area (the
 * migration path); later selections update the active id and the
 * user-written flag. Both paths end in profiles_apply, whose saver
 * call persists everything.
 */
void profile_select(u32 chosen_id)
{
    if (chosen_id >= PROF_COUNT) {
        return;
    }
    if (!profile_area_valid()) {
        profiles_write_defaults(chosen_id);
    } else {
        SI(PROF_ACTIVE) = (u8)chosen_id;
        SI(PROF_FLAGS) = (u8)(SI(PROF_FLAGS) | PROF_FLAG_USER_WRITTEN);
    }
    profiles_apply();
}
