/* Original CE metadata painter. SDK is a reference for field semantics. */
#include <stdint.h>
typedef uint16_t u16;
typedef uint32_t u32;
typedef struct { int16_t x0,y0,x1,y1; } Rect;
#define AT32(a) (*(volatile u32 *)(a))
#define TAG ((const u16 *)0x0304AF24)
#define FILE_NAME ((const u16 *)0x0304ADF4)
#define DRAW ((void (*)(Rect*,Rect*,const u16*,u32))0x03062CEF)
#define FILL ((void (*)(int,int,int,int,u32))0x030632FB)
#define FILE_SIZE ((u32 (*)(u32))0x030545D5)
#define SEC(n) __attribute__((section(n),noinline))

static SEC(".text.helper") u16 *ascii(u16 *d,const char *s) {
    while (*s) *d++=(unsigned char)*s++;
    *d=0;return d;
}
static SEC(".text.helper") u16 *number(u16 *d,u32 n) {
    char reverse[10];unsigned i=0;
    do {reverse[i++]=(char)('0'+n%10);n/=10;}while(n);
    do {*d++=reverse[--i];}while(i);
    *d=0;return d;
}
static SEC(".text.helper") void copy(u16 *out,const u16 *in) {
    unsigned n=0;while(n<127 && in[n]) {out[n]=in[n];n++;}out[n]=0;
}
static const char unknown[]="Unknown";
static const char *const formats[]={"MP3","OPUS","AAC","WAV","OGG","APE","FLAC","ALAC","DFF","DSF"};
static const char *const labels[]={"Title","Artist","Album","Format","Resolution","Bitrate","Size"};

SEC(".text.title") void player_title(u16 *out) {
    const u16 *title=TAG+0x60/2;
    copy(out,*title?title:FILE_NAME);
}

SEC(".text.info") int player_info(void) {
    u16 value[128],label[16];
    volatile u16 *ink=(volatile u16*)0x0302385C;
    u16 saved=*ink;
    u32 ground=*(volatile u16*)0x03004400;
    const u32 *codec=(const u32*)AT32(0x0304AD78);
    /* The painter owns this area; clear old rows and use the theme ink. */
    FILL(0,32,239,191,ground);
    *ink=*(volatile u16*)0x030235B6;
    for(unsigned row=0;row<7;row++) {
        u16 *p=value;value[0]=0;
        switch(row) {
        case 0:player_title(value);break;
        case 1:case 2: {
            const u16 *field=TAG+(row==1?0x15e:0x25c)/2;
            if(*field)copy(value,field);else ascii(value,unknown);
            break;
        }
        case 3: {
            u32 id=AT32(0x0304B4D4);ascii(value,id<10?formats[id]:unknown);break;
        }
        case 4:
            if(!codec || !codec[0x9c/4] || !codec[8/4]){ascii(value,unknown);break;}
            p=number(p,codec[0x9c/4]);p=ascii(p,"-bit / ");
            p=number(p,codec[8/4]/1000);
            if(codec[8/4]%1000){
                u32 fraction=codec[8/4]%1000;p=ascii(p,".");
                *p++='0'+fraction/100;*p++='0'+fraction/10%10;*p++='0'+fraction%10;
                while(p[-1]=='0')--p;
                *p=0;
            }
            ascii(p," kHz");break;
        case 5:
            if(codec && codec[12/4]) {p=number(p,codec[12/4]/1000);ascii(p," kbps");}
            else ascii(value,unknown);
            break;
        case 6: {
            u32 handle=AT32(0x03004458);
            if(handle==0xFFFFFFFFu){ascii(value,unknown);break;}
            /* Decimal megabytes, rounded to one decimal without overflow. */
            u32 bytes=FILE_SIZE(handle),tenths=bytes/100000+(bytes%100000>=50000);
            p=number(p,tenths/10);p=ascii(p,".");p=number(p,tenths%10);ascii(p," MB");break;
        }
        }
        int y=35+(int)row*22;
        Rect r={8,y,80,y+15};ascii(label,labels[row]);DRAW(&r,&r,label,0);
        r.x0=84;r.x1=231;DRAW(&r,&r,value,0);
    }
    *ink=saved;return 1;
}
