/* Original CE row blitters. SDK consulted for draw-mode semantics only. */
#include <stdint.h>
#define FN __attribute__((noinline,used))
#define CTX ((volatile uint8_t *)0x030238B8)
#define TEXT ((volatile uint16_t *)0x0302385C)
#define WIN ((void (*)(unsigned,unsigned,unsigned,unsigned))0x03063F11)
FN int eligible(unsigned x,unsigned y,unsigned right,unsigned bottom) {
    return *(volatile uint16_t *)CTX==0 && *(volatile uint32_t *)(CTX+20)==0 &&
           x<=right && y<=bottom && right<240 && bottom<320;
}
FN uint16_t *row_at(unsigned x,unsigned y) {
    return (uint16_t *)(y<240 ? 0x030065A8+480*y+2*x : 0x0306F224+480*(y-240)+2*x);
}
FN void finish_rect(unsigned x,unsigned y) {
    *(volatile uint32_t *)(CTX+12)=1;
    *(volatile uint16_t *)(CTX+32)=x;
    *(volatile uint16_t *)(CTX+34)=y;
}
FN int fast_fill(unsigned x,unsigned y,unsigned right,unsigned bottom,unsigned color) {
    if(!eligible(x,y,right,bottom))return 0;
    WIN(x,y,right,bottom);
    for(unsigned r=y;r<=bottom;r++) {
        uint16_t *p=row_at(x,r);
        for(unsigned c=x;c<=right;c++)*p++=color;
    }
    finish_rect(x,bottom>=240 && bottom<319 ? bottom+1:y);return 1;
}
FN void opaque_rows(unsigned x,unsigned y,unsigned w,unsigned h,const uint16_t *src) {
    WIN(x,y,x+w-1,y+h-1);
    for(unsigned r=0;r<h;r++) {
        uint16_t *dst=row_at(x,y+r);
        for(unsigned c=0;c<w;c++)*dst++=*src++;
    }
    unsigned bottom=y+h-1;
    finish_rect(x,bottom>=240 && bottom<319 ? bottom+1:y);
}
FN void finish_sparse(unsigned x,unsigned lasty,unsigned firsty,unsigned extra) {
    WIN(x,firsty,x+extra,lasty+extra);
    WIN(x,lasty,x+extra,lasty+extra);
    finish_rect(x+extra,lasty+(extra==0 && lasty>=240 && lasty<319));
}
struct ink_trace { unsigned x,y,firsty,landed; };
FN void mono_line(unsigned x,unsigned y,unsigned w,unsigned bits,struct ink_trace *t) {
    unsigned mode=TEXT[2];
    uint16_t *p=row_at(x,y);
    for(unsigned c=0;c<w;c++) {
        unsigned on=(bits & (0x8000>>c))!=0;
        if(on || !(mode&1) || (mode&2)) {
            p[c]=TEXT[(on ^ ((mode>>1)&1))?0:1];
            if(!t->landed)t->firsty=y;
            t->x=x+c;t->y=y;t->landed=1;
        }
    }
}
FN void mono_rows(unsigned x,unsigned y,unsigned w,unsigned h,const uint16_t *src) {
    struct ink_trace t;t.landed=0;
    for(unsigned r=0;r<h;r++)mono_line(x,y+r,w,*src++,&t);
    if(t.landed)finish_sparse(t.x,t.y,t.firsty,0);
}
FN int fast_bitmap(unsigned x,unsigned y,unsigned w,unsigned h,unsigned mode,const uint16_t *src) {
    if(!w || !h || w>240 || h>320 || !eligible(x,y,x+w-1,y+h-1))return 0;
    if(mode==16)opaque_rows(x,y,w,h,src);
    else if(mode==1 && w<=16)mono_rows(x,y,w,h,src);
    else return 0;
    return 1;
}
__attribute__((optimize("no-if-conversion","no-if-conversion2")))
FN void finish_keyed(unsigned x,unsigned y,unsigned firsty,unsigned flags) {
    WIN(x,firsty,x+1,y+1);WIN(x,y,x+1,y+1);
    if(flags&1) *(volatile uint32_t *)(CTX+12)=1;
    if(flags&2) *(volatile uint16_t *)(CTX+32)=x+1;
}
FN void keyed_rows(unsigned x,unsigned y,unsigned right,unsigned bottom,const uint16_t *src,unsigned key) {
    unsigned lastx=0,lasty=0,landed=0,firsty=0,lastdraw=0;
    for(unsigned r=y;r<=bottom;r++) {
        uint16_t *p=row_at(x,r);
        for(unsigned c=x;c<=right;c++) {
            unsigned v=*src++;
            lastdraw=key==2 ? (v!=0xF800) : (v!=0xF800 && (key==1 || v!=0));
            if(lastdraw) {
                p[c-x]=key==2?*(volatile uint16_t *)0x030235B6:v;
                if(!landed)firsty=r;
                lastx=c;lasty=r;landed=1;
            }
        }
    }
    if(key==1 || key==2) finish_keyed(right,bottom,y,landed | (lastdraw<<1));
    else if(landed) finish_sparse(lastx,lasty,firsty,1);
}
FN int fast_keyed(unsigned x,unsigned y,unsigned right,unsigned bottom,unsigned mode,const uint16_t *src,unsigned key) {
    /* Stock keyed windows use x+1/y+1; avoid their edge clamp quirks. */
    if(mode!=16 || right>=239 || bottom>=319 || !eligible(x,y,right,bottom))return 0;
    keyed_rows(x,y,right,bottom,src,key);return 1;
}
FN int fast_flash(unsigned x,unsigned y,unsigned w,unsigned h,unsigned offset) {
    if(x || y || w!=240 || h!=320 || !eligible(0,0,239,319))return 0;
    unsigned source=*(volatile uint32_t *)0x0302328C;
    typedef void (*read_fn)(unsigned,void *,unsigned);
    read_fn read=(read_fn)0x030640A7;
    WIN(0,0,239,319);
    read(source+offset,row_at(0,0),240*240*2);
    read(source+offset+240*240*2,row_at(0,240),240*80*2);
    WIN(0,318,239,319);finish_rect(0,318);return 1;
}

FN int fast_clear(unsigned color) {
    if(TEXT[4]!=240 || TEXT[5]!=320)return 0;
    return fast_fill(0,0,239,319,color);
}
