/* Original CE USB display. The UAC descriptors carry PCM, never file tags. */
#include <stdint.h>
#define PART(n) __attribute__((section(".text." #n),used,noinline))
extern const uint16_t usb_lines[][24];
PART(usb_card) void usb_card(void) {
    typedef void (*text_fn)(const int16_t *, const int16_t *, const uint16_t *, unsigned);
    const text_fn text=(text_fn)0x03062CEF;
    for(unsigned i=0;i<3;i++) {
        int16_t rect[4]={0, (int16_t)(132+22*i),239,(int16_t)(147+22*i)};
        text(rect,rect,usb_lines[i],2);
    }
}
__attribute__((section(".rodata.usb_lines"),used))
const uint16_t usb_lines[][24]={u"USB Audio",u"16-bit / 48 kHz",u"PCM: 1536 kbps stereo"};
