/* Stage 339: compact deterministic German retro formant synthesizer.
 * No speech samples, no platform TTS and no external DSP libraries.
 * MIT-style permission: see README for this newly authored module.
 */
#define _USE_MATH_DEFINES
#include "retro_speech.h"
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#include <mmsystem.h>
#endif

#define RS_PI 3.14159265358979323846
#define RS_MAX_PHONES 2048
#define RS_MAX_TEXT 8192
#define RS_MAX_SECONDS 90U

/* Formants in Hz; v=periodic source gain, n=frication gain, burst=plosive. */
typedef struct {
    const char *token;
    float f1, f2, f3;
    float v, n;
    int ms, burst;
} Phone;

static const Phone phones[] = {
    {"A", 800, 1250, 2850, 1, 0.02f, 135, 0},
    {"a", 750, 1350, 2700, 1, 0.02f, 90, 0},
    {"E", 520, 1850, 2600, 1, 0.02f, 125, 0},
    {"e", 580, 1700, 2500, 1, 0.02f, 88, 0},
    {"I", 380, 2150, 2950, 1, 0.02f, 80, 0},
    {"i", 290, 2350, 3200, 1, 0.02f, 145, 0},
    {"O", 540, 850, 2700, 1, 0.02f, 115, 0},
    {"o", 480, 950, 2650, 1, 0.02f, 100, 0},
    {"U", 400, 850, 2200, 1, 0.02f, 112, 0},
    {"u", 350, 900, 2200, 1, 0.02f, 80, 0},
    {"AE", 630, 1700, 2650, 1, 0.02f, 120, 0},
    {"OE", 480, 1500, 2500, 1, 0.02f, 125, 0},
    {"UE", 350, 1700, 2350, 1, 0.02f, 125, 0},
    {"@", 500, 1550, 2500, 0.75f, 0.03f, 80, 0},
    {"AI", 730, 1550, 2600, 1, 0.02f, 175, 0},
    {"AU", 700, 1200, 2600, 1, 0.02f, 170, 0},
    {"OI", 520, 1500, 2600, 1, 0.03f, 170, 0},
    {"H", 800, 1250, 2850, 0, 0.65f, 55, 0},
    {"L", 370, 1250, 2550, 0.8f, 0.02f, 85, 0},
    {"R", 430, 1300, 2200, 0.62f, 0.25f, 72, 0},
    {"M", 300, 1150, 2150, 0.8f, 0.015f, 90, 0},
    {"N", 310, 1400, 2300, 0.78f, 0.02f, 80, 0},
    {"NG", 320, 1450, 2300, 0.75f, 0.025f, 100, 0},
    {"J", 330, 2200, 3000, 0.8f, 0.03f, 75, 0},
    {"V", 450, 1350, 2400, 0.58f, 0.36f, 83, 0},
    {"Z", 500, 1600, 2900, 0.58f, 0.38f, 85, 0},
    {"F", 520, 1850, 3100, 0, 0.9f, 95, 0},
    {"S", 350, 3400, 5200, 0, 1.0f, 105, 0},
    {"SH", 450, 2300, 3800, 0, 0.95f, 118, 0},
    {"CH", 380, 2600, 3900, 0, 0.75f, 100, 0},
    {"X", 550, 1750, 2700, 0, 0.82f, 100, 0},
    {"B", 400, 1100, 2300, 0.40f, 0.45f, 65, 1},
    {"D", 450, 1700, 2750, 0.40f, 0.5f, 65, 1},
    {"G", 440, 1350, 2500, 0.40f, 0.5f, 70, 1},
    {"P", 450, 1700, 3000, 0, 0.85f, 70, 1},
    {"T", 400, 2250, 3400, 0, 0.9f, 70, 1},
    {"K", 500, 1900, 3000, 0, 0.9f, 76, 1},
    {"_", 500, 1500, 2500, 0, 0, 135, 0},
    {".", 500, 1500, 2500, 0, 0, 250, 0},
    {"?", 500, 1500, 2500, 0, 0, 260, 0},
    {"!", 500, 1500, 2500, 0, 0, 225, 0}
};
#define PHONE_COUNT (sizeof(phones)/sizeof(phones[0]))

static int g_rate = 22050;
static int g_mix = 55;
static int g_pitch = 125;
static int g_speed = 100;
static int g_expression = 60; /* 0=flat, 100=animated pitch */
static int g_articulation = 65; /* 0=soft transitions, 100=crisp consonants */
static int g_error = 0;
static volatile int g_stop = 0;

static int err(int e) { g_error = e; return 0; }
static const Phone *lookup(const char *name) {
    size_t i;
    for (i = 0; i < PHONE_COUNT; ++i)
        if (!strcmp(phones[i].token, name)) return &phones[i];
    return NULL;
}
typedef struct { const Phone *phone; int duration; int stress; } Segment;
typedef struct { Segment seg[RS_MAX_PHONES]; int n; } Utterance;
static int append(Utterance *u, const char *token) {
    const Phone *p = lookup(token);
    if (!p || u->n >= RS_MAX_PHONES) return 0;
    u->seg[u->n].phone = p;
    u->seg[u->n].duration = p->ms;
    u->seg[u->n].stress = 0;
    ++u->n;
    return 1;
}
static int append_list(Utterance *u, const char *list) {
    char token[20];
    while (*list) {
        int j = 0;
        while (*list == ' ') ++list;
        if (!*list) break;
        while (*list && *list != ' ' && j < (int)sizeof(token) - 1) token[j++] = *list++;
        token[j] = 0;
        if (*list && *list != ' ') return 0;
        if (!append(u, token)) return 0;
    }
    return 1;
}

/* Normalize German UTF-8 to ASCII plus single-byte umlaut markers.
 * Other Unicode codepoints become word separators; bytes are bounded. */
static int normalize(const char *src, char out[RS_MAX_TEXT]) {
    size_t n = 0, i;
    if (!src) return 0;
    for (i = 0; src[i]; ++i) {
        unsigned char ch = (unsigned char)src[i];
        if (n >= RS_MAX_TEXT - 1) return 0;
        if (ch < 128) out[n++] = (char)tolower(ch);
        else if (ch == 0xC3 && src[i + 1]) {
            unsigned char b = (unsigned char)src[++i];
            switch (b) {
              case 0xA4: case 0x84: out[n++] = '{'; break; /* ae */
              case 0xB6: case 0x96: out[n++] = '|'; break; /* oe */
              case 0xBC: case 0x9C: out[n++] = '}'; break; /* ue */
              case 0x9F: out[n++] = '~'; break; /* ss */
              default: out[n++] = ' '; break;
            }
        } else if (ch >= 0xC0 && ch < 0xF8) {
            int bytes = ch < 0xE0 ? 1 : ch < 0xF0 ? 2 : 3;
            while (bytes-- && src[i + 1] && ((unsigned char)src[i + 1] & 0xC0) == 0x80) ++i;
            out[n++] = ' ';
        } else if (ch >= 0x80) out[n++] = ' ';
    }
    out[n] = 0;
    return 1;
}

typedef struct { const char *word, *sequence; } Lexicon;
static const Lexicon lexicon[] = {
    {"hallo", "H A L O"},
    {"ich", "I CH"},
    {"bin", "B I N"},
    {"dein", "D AI N"},
    {"sprachcomputer", "SH P R A X K O M P J U T @ R"},
    {"computer", "K O M P J U T @ R"},
    {"welt", "V E L T"},
    {"guten", "G U T @ N"},
    {"tag", "T A G"},
    {"ein", "AI N"},
    {"eine", "AI N @"},
    {"ist", "I S T"},
    {"das", "D A S"},
    {"und", "U N T"},
    {"der", "D E R"},
    {"die", "D i"},
    {"du", "D U"},
    {"wir", "V i R"},
    {"spreche", "SH P R E CH @"},
    {"sprechen", "SH P R E CH @ N"},
    {"sprache", "SH P R A X @"},
    {"danke", "D A NG K @"},
    {"bitte", "B I T @"},
    {"ja", "J A"},
    {"nein", "N AI N"},
    {"test", "T E S T"},
    {"stimme", "SH T I M @"},
    {"roboter", "R O B O T @ R"},
    {"willkommen", "V I L K O M @ N"},
    {"morgen", "M O R G @ N"},
    {"heute", "H OI T @"},
    {"mein", "M AI N"},
    {"meine", "M AI N @"},
    {"zeit", "T S AI T"},
    {"stimmen", "SH T I M @ N"},
    {"synthesizer", "Z UE N T E Z AI Z @ R"},
    {"computerstimme", "K O M P J U T @ R SH T I M @"}
};

static int starts(const char *s, const char *p) {
    while (*p) if (*s++ != *p++) return 0;
    return 1;
}
static int is_vowel(const Phone *p) {
    const char *t = p->token;
    return (!strcmp(t,"A") || !strcmp(t,"a") ||
            !strcmp(t,"E") || !strcmp(t,"e") ||
            !strcmp(t,"I") || !strcmp(t,"i") ||
            !strcmp(t,"O") || !strcmp(t,"o") ||
            !strcmp(t,"U") || !strcmp(t,"u") ||
            !strcmp(t,"AE") || !strcmp(t,"OE") || !strcmp(t,"UE") ||
            !strcmp(t,"AI") || !strcmp(t,"AU") || !strcmp(t,"OI"));
}
static int reduced_word(const char *word) {
    static const char *const reduced[]={"ich","bin","dein","das","die",
        "der","ein","eine","und","du","wir","ist","ja"};
    size_t k;
    for (k=0;k<sizeof(reduced)/sizeof(reduced[0]);++k)
        if (!strcmp(word,reduced[k])) return 1;
    return 0;
}
/* Stress by vowel number, not by byte position. A word may contain more
 * than one grapheme for a vowel (ie, ei, au, ...). */
static void stress_word(Utterance *u, int begin, const char *word) {
    int k, vowel=0, target=0, position=-1;
    if (reduced_word(word)) return;
    if (!strcmp(word,"computer") || !strcmp(word,"roboter") ||
        !strcmp(word,"synthesizer") || !strcmp(word,"willkommen")) target=1;
    for (k=begin;k<u->n;++k) if (is_vowel(u->seg[k].phone)) {
        if (vowel==target) {position=k; break;}
        ++vowel;
    }
    if (position<0) {
        for (k=begin;k<u->n;++k)
            if (is_vowel(u->seg[k].phone)) {position=k;break;}
    }
    if (position>=0) {
        u->seg[position].stress=1;
        u->seg[position].duration+=18;
    }
}
static int translate_word(Utterance *u, const char *word) {
    size_t i, n;
    int begin=u->n;
    for (i=0; i<sizeof(lexicon)/sizeof(lexicon[0]); ++i)
        if (!strcmp(word, lexicon[i].word)) {
            if (!append_list(u, lexicon[i].sequence)) return 0;
            stress_word(u,begin,word);
            return 1;
        }
    n = strlen(word);
    for (i = 0; i < n;) {
        const char *s = word + i;
        const char *token = NULL;
        size_t count = 1;
        if (starts(s, "sch")) { token="SH"; count=3; }
        else if (starts(s, "ch")) { token=(i && (word[i-1]=='a' || word[i-1]=='o' || word[i-1]=='u')) ? "X" : "CH"; count=2; }
        else if (starts(s, "ei") || starts(s, "ai")) { token="AI"; count=2; }
        else if (starts(s, "au")) { token="AU"; count=2; }
        else if (starts(s, "eu") || (s[0]=='{' && s[1]=='u')) { token="OI"; count=2; }
        else if (starts(s, "ie")) { token="i"; count=2; }
        else if (starts(s, "ck")) { token="K"; count=2; }
        else if (starts(s, "pf")) { if (!append(u,"P")) return 0; token="F"; count=2; }
        else if (starts(s, "ph")) { token="F"; count=2; }
        else if (starts(s, "th")) { token="T"; count=2; }
        else if (starts(s, "er") && i+2==n) { token="@"; count=2; }
        else if (starts(s, "en") && i+2==n && n>3) {
            if (!append(u,"@")) return 0;
            token="N"; count=2;
        }
        else if (starts(s, "aa")) { token="a"; count=2; }
        else if (starts(s, "ee")) { token="e"; count=2; }
        else if (starts(s, "oo")) { token="o"; count=2; }
        else if (i>0 && *s=='h' && i+1<n && strchr("aeiou{|}",word[i-1])
                 && strchr("aeiou{|}",word[i+1])) {i+=1;continue;}
        else if (starts(s, "ng")) { token="NG"; count=2; }
        else if (starts(s, "qu")) { if (!append(u,"K")) return 0; token="V"; count=2; }
        else if (starts(s, "tz") || starts(s, "ts")) { if (!append(u,"T")) return 0; token="S"; count=2; }
        else if (i==0 && starts(s,"sp")) { token="SH"; count=1; }
        else if (i==0 && starts(s,"st")) { token="SH"; count=1; }
        else {
            switch (*s) {
                case 'a': token="A"; break; case 'e': token=(i==n-1) ? "@" : "E"; break;
                case 'i': token="I"; break; case 'o': token="O"; break;
                case 'u': token="U"; break; case '{': token="AE"; break;
                case '|': token="OE"; break; case '}': token="UE"; break;
                case '~': token="S"; break;
                case 'b': token="B"; break; case 'c': token="K"; break;
                case 'd': token="D"; break; case 'f': token="F"; break;
                case 'g': token="G"; break; case 'h': token="H"; break;
                case 'j': token="J"; break; case 'k': token="K"; break;
                case 'l': token="L"; break; case 'm': token="M"; break;
                case 'n': token="N"; break; case 'p': token="P"; break;
                case 'q': token="K"; break; case 'r': token="R"; break;
                case 's': token=(i+1<n && strchr("aeiou{|}",word[i+1])) ? "Z" : "S"; break;
                case 't': token="T"; break; case 'v': token="F"; break;
                case 'w': token="V"; break; case 'x':
                    if (!append(u,"K")) return 0;
                    token="S"; break;
                case 'y': token="UE"; break; case 'z':
                    if (!append(u,"T")) return 0;
                    token="S"; break;
                default: break;
            }
        }
        if (token && !append(u,token)) return 0;
        i += count;
    }
    stress_word(u,begin,word);
    return 1;
}
static int from_text(const char *text, Utterance *u) {
    char normalized[RS_MAX_TEXT];
    char word[RS_MAX_TEXT];
    size_t i = 0;
    if (!normalize(text,normalized)) return 0;
    u->n = 0;
    while (normalized[i]) {
        size_t j = 0;
        while (normalized[i] && (strchr("abcdefghijklmnopqrstuvwxyz{|}~", normalized[i]) != NULL)) {
            word[j++] = normalized[i++];
        }
        if (j) {
            word[j] = 0;
            if (!translate_word(u,word)) return 0;
            continue;
        }
        if (normalized[i] == '.' || normalized[i] == '!' || normalized[i] == '?') {
            char mark[2]={normalized[i],0};
            if (!append(u,mark)) return 0;
        } else if (normalized[i] == ',' || normalized[i] == ';' || normalized[i] == ':') {
            if (!append(u,"_")) return 0;
        } else if (normalized[i]==' ' && u->n && normalized[i+1] && normalized[i+1]!=' '
                   && u->seg[u->n-1].phone->v+u->seg[u->n-1].phone->n > 0) {
            /* A short inter-word pause helps the retro voice remain legible. */
            if (!append(u,"_")) return 0;
            u->seg[u->n-1].duration = 36;
        }
        ++i;
    }
    return u->n != 0;
}
static int from_phonemes(const char *str, Utterance *u) {
    char token[32];
    size_t i = 0;
    int n;
    if (!str) return 0;
    u->n = 0;
    while (str[i]) {
        while (str[i]==' ' || str[i]=='\t' || str[i]=='\n') ++i;
        if (!str[i]) break;
        n = 0;
        while (str[i] && str[i]!=' ' && str[i]!='\t' && str[i]!='\n') {
            if (n >= (int)sizeof(token)-1) return 0;
            token[n++] = str[i++];
        }
        token[n] = 0;
        if (!append(u,token)) return 0;
    }
    return u->n > 0;
}

static double clamp(double x, double lo, double hi) {
    return x < lo ? lo : (x > hi ? hi : x);
}
typedef struct { double z1, z2; } Resonator;
static double formant(Resonator *r, double input, double freq, double bw, int sample_rate) {
    double radius, a1, a2, result;
    freq = clamp(freq, 80, sample_rate * .47);
    radius = exp(-RS_PI * bw / (double)sample_rate);
    a1 = 2.0 * radius * cos(2.0 * RS_PI * freq / (double)sample_rate);
    a2 = -radius * radius;
    result = (1.0-radius) * input + a1*r->z1 + a2*r->z2;
    r->z2 = r->z1;
    r->z1 = result;
    return result;
}
static uint32_t noise_next(uint32_t *state) {
    uint32_t x=*state;
    x ^= x<<13; x ^= x>>17; x ^= x<<5;
    *state=x;
    return x;
}
static uint32_t size_of(const Utterance *u) {
    uint64_t sum=0;
    int i;
    for (i=0;i<u->n;++i) {
        int ms = u->seg[i].duration;
        if (ms < 1) ms=1;
        /* rounded to sample count, consistent with render loop */
        sum += (uint64_t)((double)g_rate * ms * 100.0 / (1000.0 * g_speed) + 0.5);
        if (sum > (uint64_t)g_rate * RS_MAX_SECONDS || sum > UINT32_MAX) return 0;
    }
    return (uint32_t)sum;
}
static int is_phrase_mark(const Phone *q) {
    return !strcmp(q->token,".") || !strcmp(q->token,"?") || !strcmp(q->token,"!");
}
static uint32_t samples_for(const Segment *s) {
    return (uint32_t)((double)g_rate*s->duration*100.0/(1000.0*g_speed)+0.5);
}
static double ease(double x) {
    x=clamp(x,0,1);
    return x*x*(3.0-2.0*x);
}
static uint32_t synth(const Utterance *u, int16_t *pcm, uint32_t capacity) {
    uint32_t need=size_of(u), out=0, rng=0xABC75319U;
    int p, phrase_end=0, phrase_kind=0;
    uint32_t phrase_total=1, phrase_elapsed=0;
    double phase=0, low_noise=0;
    double smoothed_pitch=(double)g_pitch;
    const double pitch_alpha=1.0-exp(-1.0/(0.013*g_rate));
    const double express=g_expression/100.0;
    const double articulate=g_articulation/100.0;
    const double transition_samples=(0.038-0.027*articulate)*g_rate;
    Resonator rs[3]={{0,0},{0,0},{0,0}};
    if (!need) { err(3); return 0; }
    if (!pcm) {g_error=0;return need;}
    if (capacity<need) {err(4);return 0;}
    g_stop=0;
    for (p=0;p<u->n;++p) {
        const Segment *seg=&u->seg[p];
        const Phone *q=seg->phone;
        const Phone *prev=p>0?u->seg[p-1].phone:q;
        const Phone *next=p+1<u->n?u->seg[p+1].phone:q;
        uint32_t len=samples_for(seg), i;
        double voiced_neighbours=(q->v>0.5 && prev->v>0.5);
        double voiced_next=(q->v>0.5 && next->v>0.5);
        if (p==0 || p>phrase_end) {
            int k;
            phrase_end=p;
            phrase_total=0;
            phrase_elapsed=0;
            phrase_kind=0;
            for (k=p;k<u->n;++k) {
                /* End punctuation is silence, not part of the pitch contour. */
                if (!is_phrase_mark(u->seg[k].phone))
                    phrase_total+=samples_for(&u->seg[k]);
                phrase_end=k;
                if (is_phrase_mark(u->seg[k].phone)) {
                    phrase_kind=u->seg[k].phone->token[0];
                    break;
                }
            }
            if (!phrase_total) phrase_total=1;
        }
        for (i=0;i<len;++i) {
            double t=(double)i/(double)(len?len:1);
            double blend=ease(i/transition_samples);
            double f1=prev->f1+(q->f1-prev->f1)*blend;
            double f2=prev->f2+(q->f2-prev->f2)*blend;
            double f3=prev->f3+(q->f3-prev->f3)*blend;
            double v=prev->v+(q->v-prev->v)*blend;
            double noisy=prev->n+(q->n-prev->n)*blend;
            double phrase_t=(double)phrase_elapsed/(double)phrase_total;
            double contour, accent, target_pitch, white, high, pulse;
            double input, wave, env, rough, c64, value;
            /* Question: rising F0 near the end. Statement: falling F0.
             * Lexically stressed vowels receive a smooth local pitch accent. */
            if (phrase_kind=='?')
                contour=0.035-0.065*phrase_t+0.25*ease((phrase_t-0.62)/0.32);
            else if (phrase_kind=='!')
                contour=0.13-0.20*phrase_t;
            else
                contour=0.065-0.18*phrase_t;
            accent=seg->stress ? 0.16*ease(t/0.27)*(1.0-ease((t-0.70)/0.29)) : 0.0;
            target_pitch=g_pitch*(1.0+express*(contour+accent+
                     0.013*sin(2.0*RS_PI*4.1*(double)out/g_rate)));
            smoothed_pitch+=pitch_alpha*(target_pitch-smoothed_pitch);
            phase+=smoothed_pitch/g_rate;
            if (phase>=1.0) phase-=1.0;
            pulse=phase<0.12?(1.0-phase/0.12):-0.061;
            white=(int32_t)noise_next(&rng)/2147483648.0;
            low_noise=.86*low_noise+.14*white;
            high=white-low_noise;
            /* Non-speech gaps are silent without carried formant excitation. */
            input=v*pulse*1.15+noisy*high*(0.40+0.36*articulate);
            if (q->burst) {
                if (t<.14) input=high*q->n*(0.92+0.34*articulate);
                else if (t<.30) input*=.35;
            }
            wave=.94*formant(&rs[0],input,f1,120,g_rate)
                +.53*formant(&rs[1],input,f2,180,g_rate)
                +.35*formant(&rs[2],input,f3,250,g_rate);
            wave+=(0.10+0.075*articulate)*noisy*high;
            /* Avoid a complete fade-out at boundaries of neighbouring vowels
             * and other voiced phonemes. Prevent clicks at word/phrase edges. */
            env=(voiced_neighbours?0.86+0.14*ease(i/(.007*g_rate)):
                 ease(i/(.005*g_rate)));
            env*=(voiced_next?0.86+0.14*ease((len-i)/(.009*g_rate)):
                  ease((len-i)/(.008*g_rate)));
            if (!q->v && !q->n) env*=0.0;
            rough=clamp(wave*env*0.82,-1,1);
            c64=floor(rough*48.0+0.5)/48.0;
            value=rough*(g_mix/100.0)+c64*(1.0-g_mix/100.0);
            /* Soft-limit strong impulses so improved articulation does not
             * force flat-topped saturation into the WAV. */
            value=1.35*value/(1.0+0.60*fabs(value));
            value=clamp(value,-0.98,0.98);
            pcm[out++]=(int16_t)(value*32767.0);
            ++phrase_elapsed;
        }
    }
    g_error=0;
    return out;
}

int32_t RS_CALL SpeechInitialize(int32_t sample_rate) {
    if (sample_rate<8000 || sample_rate>48000) return err(1);
    g_rate=sample_rate; g_stop=0; g_error=0; return 1;
}
int32_t RS_CALL SpeechSetMix(int32_t amiga_percent) {
    if (amiga_percent<0 || amiga_percent>100) return err(1);
    g_mix=amiga_percent; g_error=0; return 1;
}
int32_t RS_CALL SpeechSetPitch(int32_t pitch_hz) {
    if (pitch_hz<70 || pitch_hz>260) return err(1);
    g_pitch=pitch_hz; g_error=0; return 1;
}
int32_t RS_CALL SpeechSetSpeed(int32_t percent) {
    if (percent<50 || percent>200) return err(1);
    g_speed=percent; g_error=0; return 1;
}
int32_t RS_CALL SpeechSetExpression(int32_t percent) {
    if (percent<0 || percent>100) return err(1);
    g_expression=percent;g_error=0;return 1;
}
int32_t RS_CALL SpeechSetArticulation(int32_t percent) {
    if (percent<0 || percent>100) return err(1);
    g_articulation=percent;g_error=0;return 1;
}
int32_t RS_CALL SpeechGetSampleRate(void) {return g_rate;}
int32_t RS_CALL SpeechGetLastError(void) {return g_error;}
const char *RS_CALL SpeechGetLastErrorText(void) {
    switch(g_error) {
      case 0: return "OK";
      case 1: return "Invalid setting";
      case 2: return "Invalid text or phoneme";
      case 3: return "Invalid or excessively long audio";
      case 4: return "Output buffer too small";
      case 5: return "Audio playback unavailable";
      case 6: return "Unable to write WAV file";
      default: return "Unknown error";
    }
}
static uint32_t render(const char *s,int16_t *pcm,uint32_t cap,int direct) {
    Utterance *u=(Utterance*)malloc(sizeof(Utterance));
    uint32_t result;
    if (!u) {err(3); return 0;}
    if (!(direct ? from_phonemes(s,u) : from_text(s,u))) {
        free(u); err(2); return 0;
    }
    result=synth(u,pcm,cap);
    free(u);
    return result;
}
uint32_t RS_CALL SpeechRenderText(const char *text, int16_t *pcm, uint32_t cap) {
    return render(text,pcm,cap,0);
}
uint32_t RS_CALL SpeechRenderPhonemes(const char *text, int16_t *pcm, uint32_t cap) {
    return render(text,pcm,cap,1);
}
static void put_u16(FILE *f,uint32_t v) {
    fputc((int)(v&255),f); fputc((int)((v>>8)&255),f);
}
static void put_u32(FILE *f,uint32_t v) {
    put_u16(f,v&65535); put_u16(f,v>>16);
}
int32_t RS_CALL SpeechSaveWav(const char *wav_path,const char *text) {
    uint32_t n=SpeechRenderText(text,NULL,0), i;
    int16_t *samples;
    FILE *f;
    if (!n || !wav_path) return err(n?1:g_error);
    samples=(int16_t*)malloc((size_t)n*sizeof(int16_t));
    if (!samples) return err(3);
    if (SpeechRenderText(text,samples,n)!=n) {free(samples);return 0;}
    f=fopen(wav_path,"wb");
    if (!f) {free(samples);return err(6);}
    fwrite("RIFF",1,4,f); put_u32(f,36+n*2);
    fwrite("WAVEfmt ",1,8,f); put_u32(f,16); put_u16(f,1); put_u16(f,1);
    put_u32(f,(uint32_t)g_rate); put_u32(f,(uint32_t)g_rate*2); put_u16(f,2); put_u16(f,16);
    fwrite("data",1,4,f); put_u32(f,n*2);
    for (i=0;i<n;++i) put_u16(f,(uint16_t)samples[i]);
    free(samples);
    if (fclose(f)!=0) return err(6);
    g_error=0;
    return 1;
}
static int32_t speak(const char *s,int direct) {
#ifdef _WIN32
    HWAVEOUT device=NULL;
    WAVEFORMATEX format;
    WAVEHDR hdr;
    MMRESULT mm;
    uint32_t n=direct?SpeechRenderPhonemes(s,NULL,0):SpeechRenderText(s,NULL,0);
    int16_t *samples;
    if (!n) return 0;
    samples=(int16_t*)malloc((size_t)n*sizeof(int16_t));
    if (!samples) return err(3);
    if ((direct?SpeechRenderPhonemes(s,samples,n):SpeechRenderText(s,samples,n))!=n) {
        free(samples); return 0;
    }
    memset(&format,0,sizeof(format));
    format.wFormatTag=WAVE_FORMAT_PCM;
    format.nChannels=1; format.nSamplesPerSec=(DWORD)g_rate;
    format.wBitsPerSample=16; format.nBlockAlign=2;
    format.nAvgBytesPerSec=(DWORD)g_rate*2;
    mm=waveOutOpen(&device,WAVE_MAPPER,&format,0,0,CALLBACK_NULL);
    if (mm!=MMSYSERR_NOERROR) {free(samples);return err(5);}
    memset(&hdr,0,sizeof(hdr));
    hdr.lpData=(LPSTR)samples; hdr.dwBufferLength=n*2;
    mm=waveOutPrepareHeader(device,&hdr,sizeof(hdr));
    if (mm==MMSYSERR_NOERROR) mm=waveOutWrite(device,&hdr,sizeof(hdr));
    if (mm==MMSYSERR_NOERROR) {
        while (!(hdr.dwFlags&WHDR_DONE)) {
            if (g_stop) waveOutReset(device);
            Sleep(10);
        }
    } else waveOutReset(device);
    if (hdr.dwFlags&WHDR_PREPARED) waveOutUnprepareHeader(device,&hdr,sizeof(hdr));
    waveOutClose(device); free(samples);
    return mm==MMSYSERR_NOERROR ? (g_error=0,1) : err(5);
#else
    (void)s; (void)direct; return err(5);
#endif
}
int32_t RS_CALL SpeechSpeak(const char *text) {return speak(text,0);}
/* Stage 342: CP1252 dBase string slots -> UTF-8, no external converters.
 * Never trust a missing NUL terminator or the caller-provided length. */
int32_t RS_CALL SpeechSpeakCP1252(const char *text, uint32_t length) {
    static const uint16_t cp1252_special[32] = {
        0x20AC,0x0081,0x201A,0x0192,0x201E,0x2026,0x2020,0x2021,
        0x02C6,0x2030,0x0160,0x2039,0x0152,0x008D,0x017D,0x008F,
        0x0090,0x2018,0x2019,0x201C,0x201D,0x2022,0x2013,0x2014,
        0x02DC,0x2122,0x0161,0x203A,0x0153,0x009D,0x017E,0x0178
    };
    char *utf8;
    uint32_t i;
    size_t pos = 0;
    int32_t result;
    if (!text && length != 0) return err(1);
    if (length > RS_MAX_TEXT - 1) return err(1);
    utf8 = (char *)malloc((size_t)length * 3u + 1u);
    if (!utf8) return err(2);
    for (i = 0; i < length; ++i) {
        unsigned int uc = (unsigned char)text[i];
        if (uc >= 0x80 && uc <= 0x9F) uc = cp1252_special[uc - 0x80];
        if (uc < 0x80) utf8[pos++] = (char)uc;
        else if (uc < 0x800) {
            utf8[pos++] = (char)(0xC0 | (uc >> 6));
            utf8[pos++] = (char)(0x80 | (uc & 0x3F));
        } else {
            utf8[pos++] = (char)(0xE0 | (uc >> 12));
            utf8[pos++] = (char)(0x80 | ((uc >> 6) & 0x3F));
            utf8[pos++] = (char)(0x80 | (uc & 0x3F));
        }
    }
    utf8[pos] = 0;
    result = SpeechSpeak(utf8);
    free(utf8);
    return result;
}
int32_t RS_CALL SpeechSpeakPhonemes(const char *text) {return speak(text,1);}
int32_t RS_CALL SpeechStop(void) {g_stop=1; return 1;}
void RS_CALL SpeechShutdown(void) {g_stop=1;}
