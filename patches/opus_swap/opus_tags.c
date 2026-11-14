/* Original CE OpusTags reader. Stream comments across Ogg page boundaries;
 * never allocate from comment lengths or read artwork into a tag buffer. */
#include <stdint.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define FN __attribute__((noinline))
#ifdef OPUS_TAGS_HOST
extern int ce_read(void *, u32, u32);
extern int ce_seek(u32, u32, u32);
extern u32 ce_size(u32);
extern int ce_kick(void);
#else
#define ce_read ((int (*)(void *,u32,u32))0x03058FA9)
#define ce_seek ((int (*)(u32,u32,u32))0x030594A1)
#define ce_size ((u32 (*)(u32))0x030545D5)
#define ce_kick ((int (*)(void))0x030611E1)
#endif
typedef struct {
    u32 handle, size, pos, serial, seq, packet_bytes;
    u16 segment_left, index, count;
    u8 laces[255], ended, failed, first;
} Stream;

static FN u32 le32(const u8 *p) {
    return (u32)p[0]|(u32)p[1]<<8|(u32)p[2]<<16|(u32)p[3]<<24;
}
static FN int exact(Stream *s, void *p, u32 n) {
    ce_kick();
    if (n>s->size-s->pos || ce_read(p,n,s->handle)!=(int)n) {
        s->failed=1;return 0;
    }
    s->pos+=n;return 1;
}
static FN int first_page(Stream *s,const u8 *h) {
    if (!(h[5]&2) || (h[5]&1))return 0;
    s->serial=le32(h+14);s->seq=le32(h+18);s->first=0;
    return 1;
}
static FN int page_sequence(Stream *s,const u8 *h) {
    if(s->first)return first_page(s,h);
    if(le32(h+14)!=s->serial || le32(h+18)!=++s->seq)return 0;
    return !!(h[5]&1)==(s->packet_bytes!=0);
}
static FN int page_header(const u8 *h) {
    return le32(h)==0x5367674f && !h[4];
}
static FN int page(Stream *s) {
    u8 h[27];
    if(!exact(s,h,27)||!page_header(h)||!page_sequence(s,h))return 0;
    s->index=0;s->count=h[26];
    return s->count && exact(s,s->laces,s->count);
}
static FN int segment(Stream *s) {
    if (s->index==s->count && !page(s))return 0;
    s->segment_left=s->laces[s->index++];
    s->ended=s->segment_left<255;
    return 1;
}
static FN int skip(Stream *s,u32 n) {
    ce_kick();
    if(n>s->size-s->pos)return 0;
    s->pos+=n;ce_seek(s->pos,0,s->handle);return 1;
}
static FN int transfer(Stream *s,u8 *out,u32 n) {
    while (n) {
        if (!s->segment_left) {
            if (s->ended || !segment(s))return 0;
            if (!s->segment_left)return 0;
        }
        u32 k=n<s->segment_left?n:s->segment_left;
        if (out) {if (!exact(s,out,k))return 0;out+=k;}
        else if(!skip(s,k))return 0;
        s->segment_left-=k;n-=k;s->packet_bytes+=k;
    }
    return 1;
}
static FN int next_packet(Stream *s) {
    while (s->segment_left || !s->ended) {
        if (!s->segment_left && !segment(s))return 0;
        if (!transfer(s,0,s->segment_left))return 0;
    }
    s->ended=0;s->packet_bytes=0;
    return segment(s);
}
static FN int word(Stream *s,u32 *value) {
    u8 p[4];if (!transfer(s,p,4))return 0;
    *value=le32(p);return 1;
}
static FN int equal(const u8 *a,const char *b,u32 n) {
    u32 i=0;while (i<n && b[i]) {
        u8 c=a[i];if (c>='a'&&c<='z')c-=32;
        if(c!=(u8)b[i])return 0;++i;
    }
    return i==n && !b[i];
}
static FN u16 *field(u8 *record,const u8 *key,u32 n) {
    if(equal(key,"TITLE",n))return (u16 *)(record+0x60);
    if(equal(key,"ARTIST",n))return (u16 *)(record+0x15e);
    return 0;
}
static FN u16 *field_album(u8 *record,const u8 *key,u32 n) {
    if(equal(key,"ALBUM",n))return (u16 *)(record+0x25c);
    if(equal(key,"GENRE",n))return (u16 *)(record+0x35a);
    return field(record,key,n);
}
static FN u32 lead(u32 c) {
    if(c>=0xc2&&c<=0xdf)return 1;
    if(c>=0xe0&&c<=0xef)return 2;
    if(c>=0xf0&&c<=0xf4)return 3;
    return 0;
}
static FN int valid_point(u32 c,u32 need) {
    u32 min=need==1?128:need==2?2048:65536;
    return c>=min && c<=0x10ffff && !(c>=0xd800&&c<=0xdfff);
}
static FN u32 codepoint(const u8 *p,u32 n,u32 *used) {
        u32 i=1,c=p[0],need;
        *used=1;
        if(c<128)return c;
        need=lead(c);if(!need)return 0xfffd;
        u32 total=need;c&=(1u<<(6-need))-1;
        if(need>n-i)return 0;
        while(need && (p[i]&0xc0)==0x80){c=c<<6|(p[i++]&63);--need;}
        *used=i;
        if(need || !valid_point(c,total)) {
            return 0xfffd;
        }
        return c;
}
static FN u32 store_point(u16 *out,u32 c) {
    if(c>65535){c-=65536;out[0]=0xd800+(c>>10);out[1]=0xdc00+(c&1023);return 2;}
    out[0]=c;return 1;
}
static FN void utf16(u16 *out,const u8 *p,u32 n) {
    u32 i=0,j=0;
    while(i<n && j<126) {
        u32 used,c=codepoint(p+i,n-i,&used);i+=used;if(!c)break;
        j+=store_point(out+j,c);
    }
    out[j]=0;
}
static FN int value(Stream *s,u16 *dest,u32 length) {
    u8 data[508];
    if(dest && !*dest) {
        u32 n=length<sizeof(data)?length:sizeof(data);
        if(!transfer(s,data,n))return 0;utf16(dest,data,n);length-=n;
    }
    return transfer(s,0,length);
}
static FN int comment(Stream *s,u8 *record,u32 length) {
    u8 key[24];u32 used=0;u16 *dest=0;
    while(length && used<sizeof(key)) {
        u8 c;if(!transfer(s,&c,1))return 0;--length;
        if(c=='='){dest=field_album(record,key,used);break;}key[used++]=c;
    }
    return value(s,dest,length);
}
static FN int headers(Stream *s) {
    u8 h[19];
    if(!page(s)||!segment(s)||!transfer(s,h,19))return 0;
    if(!equal(h,"OPUSHEAD",8)||h[8]>15||!h[9])return 0;
    return next_packet(s)&&transfer(s,h,8)&&equal(h,"OPUSTAGS",8);
}
static FN int tags(Stream *s,u8 *record) {
    u32 n,count;
    if(!word(s,&n)||!transfer(s,0,n)||!word(s,&count))return 0;
    if(count>s->size/4)return 0;
    while(count--)if(!word(s,&n)||!comment(s,record,n))return 0;
    return !s->failed;
}
int opus_tags(u32 handle,u8 *record) {
    Stream s;
    u8 *p=(u8 *)&s;for(u32 i=0;i<sizeof(s);i++)p[i]=0;
    s.handle=handle;s.size=ce_size(handle);s.first=1;
    ce_seek(0,0,handle);
    return headers(&s)&&tags(&s,record);
}
