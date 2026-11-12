/* Original CE artwork row compositor; no decoded pixels are mutated. */
#include <stdint.h>
typedef uint16_t u16;
typedef uint32_t u32;
#define SEC(s) __attribute__((section(s),noinline))
#define AT(a) (*(volatile u32 *)(a))
#define FILL ((void (*)(int,int,int,int,u32))0x030632FB)
#define BLIT ((u32 (*)(int,int,int,int,u32,const u16*))0x0306333F)
#define KEYED ((void (*)(u32,int,int))0x03063A09)
static SEC(".text.contrast") int gain(int v,int max) {
    v=(118*v-9*max+50)/100;
    return v<0?0:v>max?max:v;
}
SEC(".text.contrast") u16 art_contrast(u16 v) {
    return (gain(v>>11,31)<<11)|(gain((v>>5)&63,63)<<5)|gain(v&31,31);
}
static SEC(".text.round") int inset(int row,int width,int height) {
    (void)width;
    int y=row<height/2?row:height-1-row;
    /* Radius 10; symmetry and conservative pixel-center mask. */
    static const unsigned char edge[10]={7,5,4,3,2,2,1,1,0,0};
    return y<0?width:y<10?edge[y]:0;
}
static SEC(".text.pixels") void art_pixels(u16 *out,const u16 *src,int width,int row,int h,int art_width) {
    int skip=inset(row,art_width,h),pad=(width-art_width)/2;
    u16 ground=*(volatile u16*)0x03004400;
    for(int i=0;i<width;i++)out[i]=(i<pad+skip||i>=pad+art_width-skip)?ground:art_contrast(src[i]);
}
void art_badge(u32 id);
SEC(".text.row") u32 art_row(int x,int y,int width,int height,u32 mode,const u16 *src) {
    u16 row[190];
    int target=AT(0x0302598C),top=AT(0x03025998);
    int left=AT(0x03025994),h=AT(0x03026CB8),w=AT(0x03026CB4);
    if (height!=1 || mode!=16 || width<=0 || width>190 ||
        !((target==144&&left==48&&top==36)||(target==190&&left==25&&top==8)) ||
        h<=0 || h>target || w<=0 || w>width || y<top || y>=top+h) {
        return BLIT(x,y,width,height,mode,src);
    }
    art_pixels(row,src,width,y-top,h,w);
    u32 result=BLIT((240-width)/2,top+(target-h)/2+y-top,width,1,mode,row);
    if(y==top+h-1 && AT(0x0304B4D4)<10) art_badge(AT(0x0304B4D4));
    return result;
}
SEC(".text.placeholder") void art_placeholder(void) {
    u16 ink=*(volatile u16*)0x030235B6;
    int hidden=*(volatile unsigned char*)0x0302348C;
    int side=hidden?190:144,x=hidden?25:48,top=hidden?8:36;
    for(int y=0;y<side;y++) {
        int n=inset(y,side,side);
        if(y<2||y>=side-2)FILL(x+n,top+y,x+side-1-n,top+y,ink);
        else {
            FILL(x+n,top+y,x+1+n,top+y,ink);
            FILL(x+side-2-n,top+y,x+side-1-n,top+y,ink);
        }
    }
    FILL(121,78,125,122,ink);
    FILL(125,78,139,83,ink);
    for(int y=0;y<10;y++) {
        int n=(y<2||y>7)?3:0;
        FILL(108+n,117+y,125-n,117+y,ink);
    }
    if(AT(0x0304B4D4)<10)art_badge(AT(0x0304B4D4));
}
static const char formats[10][4] __attribute__((section(".rodata.formats")))={"MP3","OPUS","AAC","WAV","OGG","APE","FLAC","ALAC","DFF","DSF"};
typedef struct {int16_t x0,y0,x1,y1;} Rect;
#define DRAW ((void (*)(Rect*,Rect*,const u16*,u32))0x03062CEF)
static SEC(".text.badge_fill") void badge_fill(int x,int y,u32 color) {
    for(int r=0;r<20;r++){
        int n=inset(r,40,20);FILL(x+n,y+r,x+39-n,y+r,color);
    }
}
SEC(".text.badge") void art_badge(u32 id) {
    if(id>=10)return;
    int hidden=*(volatile unsigned char*)0x0302348C;
    int x=hidden?171:148,y=hidden?174:156;
    u16 text[5];
    for(unsigned i=0;i<4;i++)text[i]=(unsigned char)formats[id][i];
    text[4]=0;
    u16 *ink=(u16*)0x0302385C,old=*ink;
    badge_fill(x,y,*(volatile u16*)0x030235B4);
    *ink=*(volatile u16*)0x030235B6;
    Rect r={x+4,y+2,x+35,y+17};DRAW(&r,&r,text,0);*ink=old;
}
