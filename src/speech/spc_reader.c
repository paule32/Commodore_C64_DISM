/* Stage 356 - SPC1 index, CRC32, optional GZIP, PCM16 / IMA-ADPCM WAV.
 * Embedded in retro_speech.c to retain one-translation-unit DLL builds.
 * Optional zlib is loaded at runtime ONLY for gzip payloads. In MSYS2
 * place zlib1.dll alongside retro_speech.dll if gzip entries are used.
 */
#include "spc_reader.h"
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif
#define SPC_MAX_COUNT 100000U
#define SPC_MAX_PAYLOAD (64U*1024U*1024U)
#define SPC_MAX_FRAMES (120U*48000U)
#define SPC_GZIP 0x80
#define SPC_HEADER_SIZE 32U
#define SPC_ENTRY_SIZE 36U

typedef struct {
    char name[256];
    uint8_t codec, channels;
    uint32_t rate, frames, crc;
    uint64_t offset, size;
} SpcItem;
struct RS_Spc {
    FILE *file;
    SpcItem *items;
    uint32_t count;
};
static const char *spc_status = "OK";
static int spc_fail(const char *message) { spc_status=message; return 0; }
const char *rs_spc_error(void) {return spc_status;}
static uint16_t spc_u16(const unsigned char *p) {return (uint16_t)(p[0]|((uint16_t)p[1]<<8));}
static uint32_t spc_u32(const unsigned char *p) {return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static uint64_t spc_u64(const unsigned char *p) {return (uint64_t)spc_u32(p)|((uint64_t)spc_u32(p+4)<<32);}
static int spc_read(FILE *f, unsigned char *p, size_t n) {return fread(p,1,n,f)==n;}
static int spc_seek(FILE *f,uint64_t offset) {
    if (offset > LONG_MAX) return 0;
    return fseek(f,(long)offset,SEEK_SET)==0;
}
static uint32_t spc_crc32(const unsigned char *data,size_t length) {
    uint32_t crc=~(uint32_t)0;
    size_t j;
    for (j=0;j<length;++j) {
        unsigned int i;
        crc ^= data[j];
        for (i=0;i<8;i++) crc=(crc>>1)^((crc&1)?0xEDB88320U:0U);
    }
    return ~crc;
}
static int spc_name_equal(const char *a,const char *b) {
    while (*a&&*b) {
        unsigned char x=(unsigned char)*a++, y=(unsigned char)*b++;
        if (x>='A'&&x<='Z')x=(unsigned char)(x+32);
        if (y>='A'&&y<='Z')y=(unsigned char)(y+32);
        if (x!=y)return 0;
    }
    return !*a&&!*b;
}
void rs_spc_close(RS_Spc *s) {
    if (!s)return;
    if(s->file) fclose(s->file);
    free(s->items);
    free(s);
}
RS_Spc *rs_spc_open(const char *path) {
    RS_Spc *s=NULL;
    unsigned char h[SPC_HEADER_SIZE], e[SPC_ENTRY_SIZE];
    uint64_t filesize, index_off, index_bytes, cursor;
    uint32_t i,count;
    if(!path||!*path){spc_fail("Missing container path");return NULL;}
    s=(RS_Spc*)calloc(1,sizeof(*s));
    if(!s){spc_fail("Out of memory");return NULL;}
    s->file=fopen(path,"rb");
    if(!s->file){spc_fail("Cannot open container");goto fail;}
    if(fseek(s->file,0,SEEK_END)||ftell(s->file)<0){spc_fail("Cannot seek container");goto fail;}
    filesize=(uint64_t)ftell(s->file);
    if(filesize<SPC_HEADER_SIZE||!spc_seek(s->file,0)||!spc_read(s->file,h,sizeof(h))) {
        spc_fail("Invalid container header");goto fail;
    }
    if(memcmp(h,"SPCHV1\0\0",8)||spc_u16(h+8)!=1||spc_u16(h+10)!=0){
        spc_fail("Unsupported SPC container version/flags");goto fail;
    }
    count=spc_u32(h+12);index_off=spc_u64(h+16);index_bytes=spc_u64(h+24);
    if(count>SPC_MAX_COUNT||index_off<SPC_HEADER_SIZE||index_off>filesize||
       index_bytes>filesize-index_off||index_off+index_bytes!=filesize||
       index_bytes<(uint64_t)count*(SPC_ENTRY_SIZE+1)) {
        spc_fail("Damaged SPC index");goto fail;
    }
    s->items=(SpcItem*)calloc(count?count:1,sizeof(SpcItem));
    if(!s->items){spc_fail("Out of memory");goto fail;}
    s->count=count;
    if(!spc_seek(s->file,index_off)){spc_fail("Cannot read SPC index");goto fail;}
    cursor=index_off;
    for(i=0;i<count;i++) {
        SpcItem *item=&s->items[i];
        uint16_t name_len;
        uint32_t j;
        uint64_t frames;
        if(index_off+index_bytes-cursor<SPC_ENTRY_SIZE || !spc_read(s->file,e,sizeof(e))) {
            spc_fail("Truncated SPC index entry");goto fail;
        }
        cursor+=SPC_ENTRY_SIZE;
        name_len=spc_u16(e);
        item->codec=e[2];item->channels=e[3];item->rate=spc_u32(e+4);
        item->offset=spc_u64(e+8);item->size=spc_u64(e+16);
        frames=spc_u64(e+24);item->crc=spc_u32(e+32);
        if(!name_len||name_len>255||name_len>index_off+index_bytes-cursor||
           (item->codec&127)<1||(item->codec&127)>4||
           item->channels<1||item->channels>8||item->rate<8000||item->rate>192000||
           frames>SPC_MAX_FRAMES||item->size>SPC_MAX_PAYLOAD||
           item->offset<SPC_HEADER_SIZE||item->offset>index_off||
           item->size>index_off-item->offset) {
            spc_fail("Invalid SPC entry metadata");goto fail;
        }
        item->frames=(uint32_t)frames;
        if(!spc_read(s->file,(unsigned char*)item->name,name_len)){
            spc_fail("Truncated SPC entry name");goto fail;
        }
        cursor+=name_len;
        item->name[name_len]=0;
        if(strlen(item->name)!=name_len){spc_fail("Invalid entry name");goto fail;}
        for(j=0;j<i;j++)if(spc_name_equal(item->name,s->items[j].name)){
            spc_fail("Duplicate SPC entry name");goto fail;
        }
    }
    if(cursor!=filesize){spc_fail("Trailing SPC index bytes");goto fail;}
    spc_status="OK";
    return s;
fail:
    rs_spc_close(s);return NULL;
}
int rs_spc_entry_count(const RS_Spc *s){return s?(int)s->count:0;}
const char *rs_spc_entry_name(const RS_Spc *s,int index){
    return s && index>=0&&(uint32_t)index<s->count?s->items[index].name:NULL;
}

/* z_stream layout is the public zlib C ABI, reproduced to avoid a compile-time
 * dependency on zlib.h. The shared library is loaded only for gzip entries. */
typedef struct {
    unsigned char *next_in;
    unsigned int avail_in;
    unsigned long total_in;
    unsigned char *next_out;
    unsigned int avail_out;
    unsigned long total_out;
    char *msg;
    void *state;
    void *(*zalloc)(void*,unsigned int,unsigned int);
    void (*zfree)(void*,void*);
    void *opaque;
    int data_type;
    unsigned long adler;
    unsigned long reserved;
} SpcZStream;
typedef const char *(*SpcZVersion)(void);
typedef int (*SpcZInit)(SpcZStream*,int,const char*,int);
typedef int (*SpcZInflate)(SpcZStream*,int);
typedef int (*SpcZEnd)(SpcZStream*);
static int spc_gunzip(const unsigned char *packed,size_t packed_size,unsigned char **out,size_t *out_size){
    SpcZVersion zv;
    SpcZInit init;
    SpcZInflate inflate_fn;
    SpcZEnd end;
    SpcZStream stream;
    unsigned char *buf=NULL;
    size_t alloc;
    int result, ok=0;
#ifdef _WIN32
    HMODULE zlib=LoadLibraryA("zlib1.dll");
#define SPC_ZFUNC(name) ((void*)GetProcAddress(zlib, name))
#else
    void *zlib=dlopen("libz.so.1",RTLD_LAZY|RTLD_LOCAL);
    if(!zlib) zlib=dlopen("libz.so",RTLD_LAZY|RTLD_LOCAL);
#define SPC_ZFUNC(name) dlsym(zlib, name)
#endif
    if(!zlib)return spc_fail("gzip requires zlib1.dll (Windows) or libz.so (Linux)");
    /* memcpy avoids ISO C warnings for object-pointer -> function-pointer casts. */
    {
        void *sym;
        sym=SPC_ZFUNC("zlibVersion"); memcpy(&zv,&sym,sizeof(zv));
        sym=SPC_ZFUNC("inflateInit2_");memcpy(&init,&sym,sizeof(init));
        sym=SPC_ZFUNC("inflate");memcpy(&inflate_fn,&sym,sizeof(inflate_fn));
        sym=SPC_ZFUNC("inflateEnd");memcpy(&end,&sym,sizeof(end));
    }
    if(!zv||!init||!inflate_fn||!end||packed_size>SPC_MAX_PAYLOAD||packed_size>UINT_MAX){
        spc_fail("Invalid zlib or oversized gzip payload");goto cleanup;
    }
    alloc=packed_size*2+1024;
    if(alloc<4096)alloc=4096;
    if(alloc>SPC_MAX_PAYLOAD)alloc=SPC_MAX_PAYLOAD;
    buf=(unsigned char*)malloc(alloc);
    if(!buf){spc_fail("Out of memory");goto cleanup;}
    memset(&stream,0,sizeof(stream));
    stream.next_in=(unsigned char*)packed;
    stream.avail_in=(unsigned int)packed_size;
    if(init(&stream,31,zv(),(int)sizeof(stream))!=0){spc_fail("Cannot initialize gzip decoder");goto cleanup;}
    for(;;) {
        if(stream.total_out>=alloc){
            unsigned char *grown;
            size_t newer;
            if(alloc>=SPC_MAX_PAYLOAD){spc_fail("gzip expands beyond 64 MiB limit");break;}
            newer=alloc*2;
            if(newer>SPC_MAX_PAYLOAD)newer=SPC_MAX_PAYLOAD;
            grown=(unsigned char*)realloc(buf,newer);
            if(!grown){spc_fail("Out of memory");break;}
            buf=grown;alloc=newer;
        }
        stream.next_out=buf+stream.total_out;
        stream.avail_out=(unsigned int)(alloc-stream.total_out);
        result=inflate_fn(&stream,0); /* Z_NO_FLUSH */
        if(result==1){ /* Z_STREAM_END */
            if(stream.avail_in!=0){spc_fail("Unexpected bytes after gzip stream");break;}
            *out=buf;*out_size=(size_t)stream.total_out;buf=NULL;ok=1;break;
        }
        if(result!=0){spc_fail("Invalid gzip stream / CRC");break;}
        if(stream.avail_in==0 && stream.avail_out>0){spc_fail("Truncated gzip stream");break;}
    }
    end(&stream);
cleanup:
    free(buf);
#ifdef _WIN32
    FreeLibrary(zlib);
#else
    dlclose(zlib);
#endif
#undef SPC_ZFUNC
    return ok;
}

static const int spc_step[89]={
    7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,
    73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,
    408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,
    1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,
    5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,
    20350,22385,24623,26846,32767
};
static const int spc_index_delta[8]={-1,-1,-1,-1,2,4,6,8};
static int16_t spc_nibble(int code,int *predictor,int *step_index) {
    int step=spc_step[*step_index];
    int change=step>>3;
    if(code&1)change+=step>>2;
    if(code&2)change+=step>>1;
    if(code&4)change+=step;
    *predictor+=(code&8)?-change:change;
    if(*predictor>32767)*predictor=32767;
    if(*predictor< -32768)*predictor= -32768;
    *step_index+=spc_index_delta[code&7];
    if(*step_index<0)*step_index=0;
    if(*step_index>88)*step_index=88;
    return (int16_t)*predictor;
}
static int spc_wave_decode(const unsigned char *wav,size_t n,int codec,
                          uint32_t frames_expected,uint32_t rate_expected,
                          int16_t **pcm,uint32_t *frames,uint32_t *rate) {
    size_t pos=12, data_off=0, data_n=0;
    unsigned int tag=0,channels=0,bits=0,align=0,block_frames=0, sample_rate=0;
    uint32_t fact_frames=0;
    int got_fmt=0,got_fact=0,got_data=0;
    int16_t *output;
    uint32_t samples, produced=0;
    if(n<44||memcmp(wav,"RIFF",4)||memcmp(wav+8,"WAVE",4)||
       (uint64_t)spc_u32(wav+4)+8U>n)return spc_fail("Invalid RIFF/WAVE header");
    while(pos+8<=n){
        const unsigned char *p=wav+pos;
        uint32_t size=spc_u32(p+4);
        pos+=8;
        if(size>n-pos)return spc_fail("Truncated WAV chunk");
        if(!memcmp(p,"fmt ",4)){
            if(size<16)return spc_fail("Missing WAVE format fields");
            tag=spc_u16(wav+pos);channels=spc_u16(wav+pos+2);
            sample_rate=spc_u32(wav+pos+4);align=spc_u16(wav+pos+12);bits=spc_u16(wav+pos+14);
            if(tag==17 && size>=20)block_frames=spc_u16(wav+pos+18);
            got_fmt=1;
        }else if(!memcmp(p,"fact",4)){
            if(size<4)return spc_fail("Short WAV fact chunk");
            fact_frames=spc_u32(wav+pos);got_fact=1;
        }else if(!memcmp(p,"data",4)){
            data_off=pos;data_n=size;got_data=1;
        }
        pos+=size+(size&1);
    }
    if(!got_fmt||!got_data||channels!=1||sample_rate!=rate_expected||
       sample_rate<8000||sample_rate>192000)return spc_fail("Unsupported WAV channels/rate");
    if((codec==1&&(tag!=1||bits!=16||align!=2))||
       (codec==2&&(tag!=17||bits!=4||align<8||block_frames!=1+(align-4)*2||!got_fact)))
        return spc_fail("Unsupported WAV codec or block format");
    if(codec==1){
        if(data_n%2)return spc_fail("Odd PCM byte count");
        samples=(uint32_t)(data_n/2);
    }else{
        if(data_n%align)return spc_fail("Truncated IMA-ADPCM block");
        if((uint64_t)(data_n/align)*block_frames<fact_frames)return spc_fail("Short IMA-ADPCM data");
        samples=fact_frames;
    }
    if(samples>SPC_MAX_FRAMES||samples!=frames_expected||
       (codec==2&&samples!=fact_frames))return spc_fail("PCM frame count mismatch");
    output=(int16_t*)malloc((size_t)(samples?samples:1)*sizeof(int16_t));
    if(!output)return spc_fail("Out of memory");
    if(codec==1){
        uint32_t j;
        for(j=0;j<samples;j++)output[j]=(int16_t)spc_u16(wav+data_off+(size_t)j*2);
    }else{
        size_t block;
        for(block=0;block<data_n;block+=align){
            const unsigned char *p=wav+data_off+block;
            int predictor=(int16_t)spc_u16(p);
            int index=p[2];
            size_t j;
            if(index>88||p[3]){free(output);return spc_fail("Invalid IMA-ADPCM block header");}
            if(produced<samples)output[produced++]=(int16_t)predictor;
            for(j=4;j<align&&produced<samples;j++){
                output[produced++]=spc_nibble(p[j]&15,&predictor,&index);
                if(produced<samples)output[produced++]=spc_nibble(p[j]>>4,&predictor,&index);
            }
        }
        if(produced!=samples){free(output);return spc_fail("Incomplete IMA-ADPCM decoding");}
    }
    *pcm=output;*frames=samples;*rate=sample_rate;
    spc_status="OK";
    return 1;
}
int rs_spc_decode(RS_Spc *s,const char *name,int16_t **pcm,uint32_t *frames,uint32_t *rate){
    const SpcItem *item=NULL;
    unsigned char *packed=NULL,*decoded=NULL;
    size_t decoded_n=0;
    uint32_t i;
    int ok=0;
    if(!s||!name||!*name||!pcm||!frames||!rate)return spc_fail("Invalid sample request");
    *pcm=NULL;*frames=0;*rate=0;
    for(i=0;i<s->count;i++)if(spc_name_equal(s->items[i].name,name)){
        item=&s->items[i];break;
    }
    if(!item)return spc_fail("Sample name missing in SPC container");
    if((item->codec&127)>2)return spc_fail("MP3/Ogg sample needs an external decoder");
    if(!spc_seek(s->file,item->offset))return spc_fail("Cannot seek sample data");
    packed=(unsigned char*)malloc((size_t)(item->size?item->size:1));
    if(!packed)return spc_fail("Out of memory");
    if(!spc_read(s->file,packed,(size_t)item->size)||
       spc_crc32(packed,(size_t)item->size)!=item->crc){
        spc_fail("SPC payload CRC32 mismatch");goto cleanup;
    }
    if(item->codec&SPC_GZIP){
        if(!spc_gunzip(packed,(size_t)item->size,&decoded,&decoded_n))goto cleanup;
    }else{
        decoded=packed;decoded_n=(size_t)item->size;packed=NULL;
    }
    ok=spc_wave_decode(decoded,decoded_n,item->codec&127,
                       item->frames,item->rate,pcm,frames,rate);
cleanup:
    free(decoded);free(packed);
    return ok;
}
