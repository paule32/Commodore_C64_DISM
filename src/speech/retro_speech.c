/* Stage 339: compact deterministic German retro formant synthesizer.
 * No speech samples, no platform TTS and no external DSP libraries.
 * MIT-style permission: see README for this newly authored module.
 */
#define _USE_MATH_DEFINES
#include "retro_speech.h"
#include "spc_reader.c" /* Stage 356: portable indexed SPC decoder, single-TU build */
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <wchar.h>
#endif
#ifdef _WIN32
#include <windows.h>
#include <mmsystem.h>
#endif

static int32_t g_speech_backend = 0; /* 0 = formant, 1 = Piper, 2 = SPC samples */
static RS_Spc *g_speech_container = NULL;
static uint32_t g_sample_rate = 0;

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
    {"_", 500, 1500, 2500, 0, 0, 105, 0},
    {".", 500, 1500, 2500, 0, 0, 250, 0},
    {"?", 500, 1500, 2500, 0, 0, 260, 0},
    {"!", 500, 1500, 2500, 0, 0, 225, 0},
    /* Stage 353: 40 new, individually parameterized phonetic variants.
     * These are not all separate German phonemes; some are allophones,
     * syllabic consonants or loanword/foreign-language sounds. */
    /*  1.. 8  Long tense oral vowels (colon = sustained vowel). */
    {"A:",  820, 1270, 2780, 1.00f, 0.012f, 190, 0},
    {"E:",  420, 2100, 2900, 1.00f, 0.009f, 185, 0},
    {"I:",  270, 2420, 3180, 1.00f, 0.008f, 185, 0},
    {"O:",  460,  870, 2650, 1.00f, 0.010f, 185, 0},
    {"U:",  315,  760, 2180, 1.00f, 0.010f, 190, 0},
    {"AE:", 540, 1830, 2750, 1.00f, 0.012f, 185, 0},
    {"OE:", 370, 1580, 2530, 1.00f, 0.012f, 185, 0},
    {"UE:", 315, 1820, 2530, 1.00f, 0.012f, 185, 0},
    /*  9..15  Short, lax vowel realizations. */
    {"A0",  760, 1420, 2660, 0.94f, 0.028f,  78, 0},
    {"E0",  620, 1790, 2630, 0.92f, 0.026f,  75, 0},
    {"I0",  450, 1990, 2770, 0.92f, 0.027f,  74, 0},
    {"O0",  580,  995, 2580, 0.94f, 0.025f,  80, 0},
    {"U0",  425, 1040, 2240, 0.92f, 0.028f,  78, 0},
    {"OE0", 555, 1560, 2490, 0.92f, 0.028f,  82, 0},
    {"UE0", 440, 1760, 2450, 0.91f, 0.030f,  82, 0},
    /* 16..19  Approximate nasalized vowels for names and loanwords. */
    {"AN",  655, 1150, 2430, 0.86f, 0.070f, 145, 0},
    {"EN",  540, 1430, 2470, 0.86f, 0.072f, 145, 0},
    {"ON",  480,  900, 2280, 0.86f, 0.071f, 145, 0},
    {"UN",  400, 1500, 2410, 0.86f, 0.072f, 145, 0},
    /* 20..22  Rhotic variants including reduced German -er. */
    {"RY",  405, 1320, 2130, 0.65f, 0.230f,  85, 0},
    {"RX",  485, 1700, 2480, 0.18f, 0.720f,  82, 0},
    {"ER",  540, 1420, 2480, 0.78f, 0.035f,  95, 0},
    /* 23..25  Syllabic nasal allophones. */
    {"M=",  295, 1060, 2150, 0.78f, 0.015f, 115, 0},
    {"N=",  315, 1440, 2400, 0.78f, 0.018f, 115, 0},
    {"NG=", 330, 1420, 2340, 0.76f, 0.024f, 118, 0},
    /* 26..29  Affricates treated as one timed segment. */
    {"TS",  390, 3190, 4700, 0.04f, 0.970f, 114, 1},
    {"TSH", 440, 2300, 3700, 0.04f, 0.940f, 121, 1},
    {"DSH", 475, 2040, 3300, 0.39f, 0.680f, 122, 1},
    {"PF",  510, 1820, 3080, 0.02f, 0.925f, 118, 1},
    /* 30..32  Distinct sibilant/frication variants. */
    {"ZH",  475, 2250, 3670, 0.48f, 0.575f, 103, 0},
    {"SHH", 445, 2440, 3920, 0.00f, 0.980f, 160, 0},
    {"SS",  355, 3510, 5080, 0.00f, 1.000f, 150, 0},
    /* 33..36  Loanword/foreign-language consonants. */
    {"TH",  520, 2050, 3100, 0.00f, 0.760f, 104, 0},
    {"DH",  475, 1740, 2790, 0.50f, 0.400f,  98, 0},
    {"WW",  380, 1020, 2300, 0.75f, 0.025f, 100, 0},
    {"NY",  320, 1850, 2860, 0.76f, 0.025f, 110, 0},
    /* 37..40  Aspirated and velar-fricative realizations. */
    {"PH",  430, 1640, 2890, 0.00f, 0.910f,  96, 1},
    {"THP", 400, 2270, 3490, 0.00f, 0.950f,  94, 1},
    {"KH",  485, 1770, 2870, 0.00f, 0.930f, 103, 1},
    {"GH",  455, 1480, 2630, 0.48f, 0.580f, 108, 0}
};
#define PHONE_COUNT (sizeof(phones)/sizeof(phones[0]))

static int g_rate = 22050;
static int g_mix = 55;
static int g_pitch = 125;
static int g_speed = 100;
static int g_expression = 60; /* 0=flat, 100=animated pitch */
static int g_articulation = 65; /* 0=soft transitions, 100=crisp consonants */
static int g_fluency = 75; /* 0=legacy-like articulated, 100=connected, Amiga-oriented */
static int g_error = 0;
static volatile int g_stop = 0;

static int err(int e) { g_error = e; return 0; }
static const Phone *lookup(const char *name) {
    size_t i;
    for (i = 0; i < PHONE_COUNT; ++i)
        if (!strcmp(phones[i].token, name)) return &phones[i];
    return NULL;
}
typedef struct { const Phone *phone; int duration; int stress; int word_start; } Segment;
typedef struct { Segment seg[RS_MAX_PHONES]; int n; } Utterance;
static int append(Utterance *u, const char *token) {
    const Phone *p = lookup(token);
    if (!p || u->n >= RS_MAX_PHONES) return 0;
    u->seg[u->n].phone = p;
    u->seg[u->n].duration = p->ms;
    u->seg[u->n].stress = 0;
    u->seg[u->n].word_start = 0;
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
    {"ich", "I0 CH"},
    {"bin", "B I0 N"},
    {"dein", "D AI N"},
    {"welt", "V E0 L T"},
    {"guten", "G U: T N="},
    {"tag", "T A G"},
    {"ein", "AI N"},
    {"eine", "AI N @"},
    {"das", "D A S"},
    {"und", "U N T"},
    {"der", "D E: R"},
    {"die", "D I:"},
    {"du", "D U:"},
    {"wir", "V I: R"},
    {"spreche", "SH P R E CH @"},
    {"sprache", "SH P R A: X @"},
    {"danke", "D A NG K @"},
    {"ja", "J A"},
    {"nein", "N AI N"},
    {"test", "T E S T"},
    {"willkommen", "V I L K O M @ N"},
    {"mein", "M AI N"},
    {"meine", "M AI N @"},
    {"zeit", "TS AI T"},
    {"synthesizer", "Z UE N T E Z AI Z @ R"},
    {"computerstimme", "K O M P J U T @ R SH T I0 M @"},
    {"{hnlich", "AE: N L I0 CH"},
    {"schule", "SH U: L @"},
    {"sch|n", "SH OE: N"},
    {"gr}n", "G R UE: N"},
    {"tisch", "T I0 SH"},
    {"katze", "K A0 TS @"},
    {"pfanne", "PF A0 N @"},
    {"deutsch", "D OI TSH"},
    {"dschungel", "DSH U0 NG @ L"},
    {"sehr", "Z E: R"},
    {"mehr", "M E: R"},
    {"sehen", "Z E: N="},
    /* Stage 354: common German connected-speech vocabulary; expressions are
     * sequences of existing phone tokens, not recordings of whole words. */
    {"hallo", "H A L O"}, /* retained historical reading */
    {"gutenabend", "G U: T N= A: B N T"},
    {"abend", "A: B N T"},
    {"gute", "G U: T @"},
    {"guter", "G U: T ER"},
    {"gutes", "G U: T @ S"},
    {"liebe", "L I: B @"},
    {"lieber", "L I: B ER"},
    {"lieben", "L I: B N="},
    {"freund", "F R OI N T"},
    {"freunde", "F R OI N D @"},
    {"freundlich", "F R OI N T L I0 CH"},
    {"sch|nen", "SH OE: N N="},
    {"wunderbar", "V U0 N D ER B A: R"},
    {"prima", "P R I: M A:"},
    {"super", "Z U: P ER"},
    {"toll", "T O0 L"},
    {"gut", "G U: T"},
    {"schlecht", "SH L E0 CH T"},
    {"richtig", "R I0 CH T I0 CH"},
    {"falsch", "F A0 L SH"},
    {"dann", "D A0 N"},
    {"wenn", "V E0 N"},
    {"weil", "V AI L"},
    {"aber", "A: B ER"},
    {"auch", "AU X"},
    {"nicht", "N I0 CH T"},
    {"noch", "N O0 X"},
    {"schon", "SH O: N"},
    {"jetzt", "J E0 TS T"},
    {"gleich", "G L AI CH"},
    {"hier", "H I: ER"},
    {"dort", "D O: R T"},
    {"heute", "H OI T @"}, /* stable */
    {"gestern", "G E0 S T ER N"},
    {"morgen", "M O: R G N="}, /* updated long vowel */
    {"sp{ter", "SH P AE: T ER"},
    {"fr}her", "F R UE: ER"},
    {"immer", "I0 M ER"},
    {"manchmal", "M A0 N CH M A: L"},
    {"wieder", "V I: D ER"},
    {"weiter", "V AI T ER"},
    {"fertig", "F E0 R T I0 CH"},
    {"bitte", "B I0 T @"}, /* common */
    {"dankesch|n", "D A0 NG K @ SH OE: N"},
    {"entschuldigung", "E0 N T SH U0 L D I0 G U0 NG"},
    {"auf", "AU F"},
    {"aus", "AU S"},
    {"mit", "M I0 T"},
    {"ohne", "O: N @"},
    {"f}r", "F UE: R"},
    {"von", "F O0 N"},
    {"zu", "TS U:"},
    {"zum", "TS U0 M"},
    {"zur", "TS U: ER"},
    {"im", "I0 M"},
    {"am", "A0 M"},
    {"an", "A0 N"},
    {"in", "I0 N"},
    {"ist", "I0 S T"}, /* no independent pause between short words */
    {"sind", "Z I0 N T"},
    {"war", "V A: R"},
    {"wird", "V I0 R T"},
    {"werden", "V E: R D N="},
    {"haben", "H A: B N="},
    {"habe", "H A: B @"},
    {"hast", "H A0 S T"},
    {"hat", "H A0 T"},
    {"kann", "K A0 N"},
    {"k|nnen", "K OE0 N N="},
    {"muss", "M U0 S"},
    {"m}ssen", "M UE0 S N="},
    {"m|chte", "M OE0 CH T @"},
    {"m|chten", "M OE0 CH T N="},
    {"will", "V I0 L"},
    {"wollen", "V O0 L N="},
    {"soll", "Z O0 L"},
    {"sollen", "Z O0 L N="},
    {"machen", "M A0 X N="},
    {"gemacht", "G @ M A0 X T"},
    {"arbeiten", "A: R B AI T N="},
    {"arbeit", "A: R B AI T"},
    {"lesen", "L E: Z N="},
    {"schreiben", "SH R AI B N="},
    {"h|ren", "H OE: R N="},
    {"sagen", "Z A: G N="},
    {"sprechen", "SH P R E0 CH N="},
    {"gesprochen", "G @ SH P R O0 X N="},
    {"lernen", "L E0 R N N="},
    {"wissen", "V I0 S N="},
    {"verstehen", "F ER SH T E: N="},
    {"verstand", "F ER SH T A0 N T"},
    {"fragen", "F R A: G N="},
    {"frage", "F R A: G @"},
    {"antwort", "A0 N T V O0 R T"},
    {"antworten", "A0 N T V O0 R T N="},
    {"verbindung", "F ER B I0 N D U0 NG"},
    {"sprachausgabe", "SH P R A: X AU S G A: B @"},
    {"sprachcomputer", "SH P R A: X K O0 M P J U: T ER"},
    {"sprachsynthese", "SH P R A: X Z UE0 N T E: Z @"},
    {"sprachsynthesizer", "SH P R A: X Z UE0 N T E: Z AI Z ER"},
    {"synthese", "Z UE0 N T E: Z @"},
    {"aussprache", "AU S SH P R A: X @"},
    {"stimme", "SH T I0 M @"},
    {"stimmen", "SH T I0 M N="},
    {"klang", "K L A0 NG"},
    {"laut", "L AU T"},
    {"laute", "L AU T @"},
    {"leise", "L AI Z @"},
    {"lautst{rke", "L AU T SH T AE R K @"},
    {"tempo", "T E0 M P O:"},
    {"langsam", "L A0 NG Z A: M"},
    {"schnell", "SH N E0 L"},
    {"fl}ssig", "F L UE0 S I0 CH"},
    {"deutlich", "D OI T L I0 CH"},
    {"deutsche", "D OI T SH @"},
    {"deutschland", "D OI T SH L A0 N T"},
    {"amiga", "A: M I: G A:"},
    {"commodore", "K O0 M O0 D O: R"},
    {"computer", "K O0 M P J U: T ER"},
    {"programm", "P R O: G R A0 M"},
    {"programme", "P R O: G R A0 M @"},
    {"programmieren", "P R O: G R A0 M I: R N="},
    {"compiler", "K O0 M P AI L ER"},
    {"datei", "D A: T AI"},
    {"dateien", "D A: T AI @ N"},
    {"daten", "D A: T N="},
    {"datenbank", "D A: T N= B A0 NG K"},
    {"fenster", "F E0 N S T ER"},
    {"bildschirm", "B I0 L T SH I0 R M"},
    {"tastatur", "T A0 S T A: T U: R"},
    {"maus", "M AU S"},
    {"men}", "M E0 N UE:"},
    {"editor", "E0 D I: T O: R"},
    {"projekt", "P R O: J E0 K T"},
    {"einstellungen", "AI N SH T E0 L U0 NG N="},
    {"starten", "SH T A: R T N="},
    {"start", "SH T A: R T"},
    {"stoppen", "SH T O0 P N="},
    {"beenden", "B @ E0 N D N="},
    {"laden", "L A: D N="},
    {"speichern", "SH P AI CH ER N"},
    {"ge|ffnet", "G @ OE0 F N @ T"},
    {"geschlossen", "G @ SH L O0 S N="},
    {"fertiggestellt", "F E0 R T I0 CH G @ SH T E0 L T"},
    {"fehler", "F E: L ER"},
    {"warnung", "V A: R N U0 NG"},
    {"hinweis", "H I0 N V AI S"},
    {"erfolg", "ER F O0 L K"},
    {"funktion", "F U0 NG K TS J O: N"},
    {"funktionen", "F U0 NG K TS J O: N N="},
    {"windows", "V I0 N D O: S"},
    {"system", "Z UE0 S T E: M"},
    {"technologie", "T E0 X N O0 L O: G I:"},
    {"mensch", "M E0 N SH"},
    {"menschen", "M E0 N SH N="},
    {"maschine", "M A: SH I: N @"},
    {"roboter", "R O: B O: T ER"},
    {"k}nstlich", "K UE0 N S T L I0 CH"},
    {"intelligenz", "I0 N T E0 L I0 G E0 N TS"},
    {"gutenmorgen", "G U: T N= M O: R G N="}
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
            !strcmp(t,"AI") || !strcmp(t,"AU") || !strcmp(t,"OI") ||
            !strcmp(t,"A:") || !strcmp(t,"E:") || !strcmp(t,"I:") ||
            !strcmp(t,"O:") || !strcmp(t,"U:") || !strcmp(t,"AE:") ||
            !strcmp(t,"OE:") || !strcmp(t,"UE:") ||
            !strcmp(t,"A0") || !strcmp(t,"E0") || !strcmp(t,"I0") ||
            !strcmp(t,"O0") || !strcmp(t,"U0") || !strcmp(t,"OE0") ||
            !strcmp(t,"UE0") || !strcmp(t,"AN") || !strcmp(t,"EN") ||
            !strcmp(t,"ON") || !strcmp(t,"UN") || !strcmp(t,"ER"));
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
        u->seg[position].duration+=12;
    }
}
static int translate_word(Utterance *u, const char *word) {
    size_t i, n;
    int begin=u->n;
    for (i=0; i<sizeof(lexicon)/sizeof(lexicon[0]); ++i)
        if (!strcmp(word, lexicon[i].word)) {
            if (!append_list(u, lexicon[i].sequence)) return 0;
            stress_word(u,begin,word);
            if (begin < u->n) u->seg[begin].word_start = 1;
            return 1;
        }
    n = strlen(word);
    for (i = 0; i < n;) {
        const char *s = word + i;
        const char *token = NULL;
        size_t count = 1;
        if (starts(s, "dsch")) { token="DSH"; count=4; }
        else if (starts(s, "tsch")) { token="TSH"; count=4; }
        else if (starts(s, "sch")) { token="SH"; count=3; }
        else if (starts(s, "ch")) { token=(i && (word[i-1]=='a' || word[i-1]=='o' || word[i-1]=='u')) ? "X" : "CH"; count=2; }
        else if (starts(s, "ei") || starts(s, "ai")) { token="AI"; count=2; }
        else if (starts(s, "au")) { token="AU"; count=2; }
        else if (starts(s, "eu") || (s[0]=='{' && s[1]=='u')) { token="OI"; count=2; }
        else if (starts(s, "ie")) { token="I:"; count=2; }
        else if (starts(s, "ck")) { token="K"; count=2; }
        else if (starts(s, "pf")) { token="PF"; count=2; }
        else if (starts(s, "ph")) { token="F"; count=2; }
        else if (starts(s, "th")) { token="T"; count=2; }
        else if (starts(s, "er") && i+2==n) { token="ER"; count=2; }
        else if (starts(s, "en") && i+2==n && n>3) {
            /* Reduced final -en, often syllabic /n/ after consonants. */
            if (i>0 && !strchr("aeiou{|}", word[i-1])) {
                token="N=";
            } else {
                if (!append(u,"@")) return 0;
                token="N";
            }
            count=2;
        }
        else if (starts(s, "aa")) { token="A:"; count=2; }
        else if (starts(s, "ee")) { token="E:"; count=2; }
        else if (starts(s, "oo")) { token="O:"; count=2; }
        else if (i+1<n && s[1]=='h' && strchr("aeiou{|}",s[0]) &&
                 (i+2==n || !strchr("aeiou{|}",s[2]))) {
            switch (s[0]) {
                case 'a': token="A:"; break;
                case 'e': token="E:"; break;
                case 'i': token="I:"; break;
                case 'o': token="O:"; break;
                case 'u': token="U:"; break;
                case '{': token="AE:"; break;
                case '|': token="OE:"; break;
                case '}': token="UE:"; break;
                default: break;
            }
            count=2;
        }
        else if (starts(s, "ng")) { token="NG"; count=2; }
        else if (starts(s, "qu")) { if (!append(u,"K")) return 0; token="V"; count=2; }
        else if (starts(s, "tz") || starts(s, "ts")) { token="TS"; count=2; }
        else if (i==0 && starts(s,"sp")) { token="SH"; count=1; }
        else if (i==0 && starts(s,"st")) { token="SH"; count=1; }
        else {
            switch (*s) {
                case 'a': token="A0"; break; case 'e': token=(i==n-1) ? "@" : "E0"; break;
                case 'i': token="I0"; break; case 'o': token="O0"; break;
                case 'u': token="U0"; break; case '{': token="AE"; break;
                case '|': token="OE0"; break; case '}': token="UE0"; break;
                case '~': token="SS"; break;
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
    if (begin < u->n) u->seg[begin].word_start = 1;
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
        }
        /* Stage 354: normal whitespace is a word boundary, NOT silence.
         * The following word_start marker allows prosodic articulation
         * without the repeated 36 ms gaps that made phrases choppy. */
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
    const double fluency=g_fluency/100.0;
    const double transition_samples=(0.034-0.021*articulate+0.016*fluency)*g_rate;
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
            double incoming=1.0-ease(i/transition_samples);
            double outgoing=0.0;
            double f1, f2, f3, v, noisy;
            if (next->v+next->n>0.0 && q->v+q->n>0.0 && len>3)
                outgoing=ease(((double)i-((double)len-transition_samples)) /
                              transition_samples) * (0.24+0.21*fluency);
            /* Coarticulation operates on both ends of a segment, blending
             * formant trajectories before the NEXT segment begins. Stage 353
             * only moved the spectrum after the previous segment ended. */
            if (prev->v+prev->n==0.0) incoming=0.0;
            if (q->v+q->n==0.0) {incoming=0.0; outgoing=0.0;}
            f1=q->f1+incoming*(prev->f1-q->f1)+outgoing*(next->f1-q->f1);
            f2=q->f2+incoming*(prev->f2-q->f2)+outgoing*(next->f2-q->f2);
            f3=q->f3+incoming*(prev->f3-q->f3)+outgoing*(next->f3-q->f3);
            v=q->v+incoming*(prev->v-q->v)+outgoing*(next->v-q->v);
            noisy=q->n+incoming*(prev->n-q->n)+outgoing*(next->n-q->n);
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
            accent=seg->stress ? (0.11-0.035*fluency)*ease(t/0.24)*
                            (1.0-ease((t-0.68)/0.28)) : 0.0;
            target_pitch=g_pitch*(1.0+express*(contour+accent+
                     0.013*sin(2.0*RS_PI*4.1*(double)out/g_rate)));
            smoothed_pitch+=pitch_alpha*(target_pitch-smoothed_pitch);
            phase+=smoothed_pitch/g_rate;
            if (phase>=1.0) phase-=1.0;
            pulse=phase<0.12?(1.0-phase/0.12):-0.061;
            pulse=(1.0-0.48*fluency)*pulse+0.48*fluency*(
                     0.60*sin(2.0*RS_PI*phase)+
                     0.28*sin(4.0*RS_PI*phase)+
                     0.12*sin(6.0*RS_PI*phase));
            white=(int32_t)noise_next(&rng)/2147483648.0;
            low_noise=.86*low_noise+.14*white;
            high=white-low_noise;
            /* Non-speech gaps are silent without carried formant excitation. */
            input=v*pulse*1.15+noisy*high*(0.40+0.36*articulate);
            if (q->burst) {
                if (t<.10) input=high*q->n*(0.80+0.30*articulate);
                else if (t<.19) input*=.55;
            }
            wave=.94*formant(&rs[0],input,f1,120,g_rate)
                +.53*formant(&rs[1],input,f2,180,g_rate)
                +.35*formant(&rs[2],input,f3,250,g_rate);
            wave+=(0.10+0.075*articulate)*noisy*high;
            /* Avoid a complete fade-out at boundaries of neighbouring vowels
             * and other voiced phonemes. Prevent clicks at word/phrase edges. */
            env=1.0;
            if (prev->v+prev->n==0.0)
                env*=ease(i/(.007*g_rate));
            else if (seg->word_start && fluency<0.50)
                env*=0.96+0.04*ease(i/(.006*g_rate));
            if (next->v+next->n==0.0)
                env*=ease((len-i)/(.010*g_rate));
            if (q->v+q->n==0.0) env=0.0;
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
int32_t RS_CALL SpeechSetFluency(int32_t percent) {
    if (percent<0 || percent>100) return err(1);
    g_fluency=percent;g_error=0;return 1;
}
int32_t RS_CALL SpeechSetBackend(int32_t backend) {
    if (backend != 0 && backend != 1 && backend != 2) return err(1);
    g_speech_backend=backend; g_error=0; return 1;
}
int32_t RS_CALL SpeechGetPhonemeCount(void) {return (int32_t)PHONE_COUNT;}
const char *RS_CALL SpeechGetPhonemeToken(int32_t index) {
    if (index<0 || (size_t)index>=PHONE_COUNT) {err(1);return NULL;}
    g_error=0;
    return phones[index].token;
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
      case 7: return "Piper offline voice package is missing or invalid";
      case 8: return "Piper speech generation failed or timed out";
      case 9: return rs_spc_error();
      default: return "Unknown error";
    }
}

/* Stage 356: name-indexed SPC sample backend. Load explicitly via
 * SpeechLoadContainer() or lazily from D64_SPEECH_CONTAINER / speech.spc.
 * Missing words deliberately return an error: silently falling back to the
 * synthesizer would make the sample voice inconsistent. */
int32_t RS_CALL SpeechLoadContainer(const char *path) {
    RS_Spc *next=rs_spc_open(path);
    if(!next)return err(9);
    rs_spc_close(g_speech_container);
    g_speech_container=next;
    g_sample_rate=0;
    g_error=0;return 1;
}
int32_t RS_CALL SpeechUnloadContainer(void) {
    rs_spc_close(g_speech_container);
    g_speech_container=NULL;
    g_sample_rate=0;g_error=0;return 1;
}
int32_t RS_CALL SpeechGetContainerEntryCount(void) {
    return rs_spc_entry_count(g_speech_container);
}
const char *RS_CALL SpeechGetContainerEntryName(int32_t index) {
    return rs_spc_entry_name(g_speech_container,index);
}
int32_t RS_CALL SpeechGetLastSampleRate(void) {return (int32_t)g_sample_rate;}
static int rs_ensure_container(void) {
    const char *explicit_path;
    if(g_speech_container)return 1;
    explicit_path=getenv("D64_SPEECH_CONTAINER");
    if(explicit_path&&*explicit_path)return SpeechLoadContainer(explicit_path);
    if(SpeechLoadContainer("speech.spc"))return 1;
#ifdef _WIN32
    {
        char path[MAX_PATH];
        char *slash;
        DWORD n=GetModuleFileNameA(NULL,path,(DWORD)sizeof(path));
        if(n&&n<sizeof(path)){
            slash=strrchr(path,'\\');
            if(!slash)slash=strrchr(path,'/');
            if(slash && (size_t)(slash-path)+strlen("\\speech.spc")<sizeof(path)) {
                strcpy(slash+1,"speech.spc");
                if(SpeechLoadContainer(path))return 1;
            }
        }
    }
#endif
    return err(9);
}
uint32_t RS_CALL SpeechRenderSample(const char *name,int16_t *pcm,uint32_t capacity){
    int16_t *decoded=NULL;
    uint32_t frames=0,rate=0;
    if(!rs_ensure_container())return 0;
    if(!rs_spc_decode(g_speech_container,name,&decoded,&frames,&rate))return err(9);
    g_sample_rate=rate;
    if(pcm){
        if(capacity<frames){free(decoded);return err(4);}
        memcpy(pcm,decoded,(size_t)frames*2);
    }
    free(decoded);g_error=0;
    return frames;
}
static int rs_samples_text(const char *text,int16_t **out,uint32_t *out_frames,uint32_t *out_rate) {
    const unsigned char *p=(const unsigned char*)text;
    int16_t *joined=NULL;
    uint32_t filled=0,rate=0;
    size_t words=0;
    if(!text||!*text||strlen(text)>RS_MAX_TEXT)return err(2);
    if(!rs_ensure_container())return 0;
    while(*p){
        char key[256];
        size_t k=0;
        int16_t *part=NULL;
        uint32_t n=0,r=0,gap=0,new_size;
        while(*p && !((*p>='a'&&*p<='z')||(*p>='A'&&*p<='Z')||
                       (*p>='0'&&*p<='9')||(*p>=128)))++p;
        if(!*p)break;
        while(*p && ((*p>='a'&&*p<='z')||(*p>='A'&&*p<='Z')||
                      (*p>='0'&&*p<='9')||(*p>=128))) {
            if(k>=sizeof(key)-1){free(joined);return err(2);}
            key[k++]=(char)*p++;
        }
        key[k]=0;
        if(!rs_spc_decode(g_speech_container,key,&part,&n,&r)){
            free(joined);return err(9);
        }
        if(!rate)rate=r;
        if(rate!=r){free(part);free(joined);return err(9);}
        gap=words?rate/40:0; /* 25ms between words, no synthetic syllable splits */
        if(n>SPC_MAX_FRAMES||filled>SPC_MAX_FRAMES-gap||n>SPC_MAX_FRAMES-filled-gap){
            free(part);free(joined);return err(3);
        }
        new_size=filled+gap+n;
        {
            int16_t *grown=(int16_t*)realloc(joined,(size_t)(new_size?new_size:1)*2);
            if(!grown){free(part);free(joined);return err(3);}
            joined=grown;
        }
        if(gap){memset(joined+filled,0,(size_t)gap*2);filled+=gap;}
        /* A short linear fade removes clicks from hard-cut sample boundaries. */
        {
            uint32_t i,fade=rate/200; /* 5 ms */
            if(fade>n/2)fade=n/2;
            for(i=0;i<fade;i++){
                part[i]=(int16_t)((int32_t)part[i]*i/(fade?fade:1));
                part[n-1-i]=(int16_t)((int32_t)part[n-1-i]*i/(fade?fade:1));
            }
        }
        memcpy(joined+filled,part,(size_t)n*2);
        filled+=n;words++;free(part);
    }
    if(!words){free(joined);return err(2);}
    *out=joined;*out_frames=filled;*out_rate=rate;
    g_sample_rate=rate;g_error=0;return 1;
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

/* Stage 355: Optional Windows Piper bridge; no additional DSP library or
 * Python interpreter is needed at runtime.  Piper and the model are NOT
 * distributed with the project and must be installed independently.
 * Generated WAVs are cached in the user's LOCALAPPDATA/TEMP directory.
 * The formant implementation is left intact as backend 0. */
#ifdef _WIN32
#define RS_PIPER_PATH 4096
static int rs_file_exists_w(const wchar_t *path) {
    DWORD flags=GetFileAttributesW(path);
    return flags != INVALID_FILE_ATTRIBUTES && !(flags & FILE_ATTRIBUTE_DIRECTORY);
}
static int rs_dir_exists_w(const wchar_t *path) {
    DWORD flags=GetFileAttributesW(path);
    return flags != INVALID_FILE_ATTRIBUTES && (flags & FILE_ATTRIBUTE_DIRECTORY);
}
static int rs_valid_wav_w(const wchar_t *path) {
    HANDLE handle;
    char header[12];
    DWORD nread=0;
    DWORD size;
    if (!rs_file_exists_w(path)) return 0;
    handle=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,
                       OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if (handle==INVALID_HANDLE_VALUE) return 0;
    size=GetFileSize(handle,NULL);
    if (size<44 || size==INVALID_FILE_SIZE ||
        !ReadFile(handle,header,sizeof(header),&nread,NULL) || nread!=sizeof(header)) {
        CloseHandle(handle);return 0;
    }
    CloseHandle(handle);
    return memcmp(header,"RIFF",4)==0 && memcmp(header+8,"WAVE",4)==0;
}
static int rs_join_w(wchar_t *out, size_t cap, const wchar_t *base, const wchar_t *name) {
    size_t n=wcslen(base), m=wcslen(name);
    if (n+m+2 >= cap) return 0;
    wcscpy(out,base);
    if (n && base[n-1]!=L'\\' && base[n-1]!=L'/') wcscat(out,L"\\");
    wcscat(out,name); return 1;
}
static int rs_find_piper(wchar_t *home, size_t cap, wchar_t *exe,
                          wchar_t *model) {
    wchar_t base[RS_PIPER_PATH], probe[RS_PIPER_PATH], candidate[RS_PIPER_PATH];
    DWORD length=GetEnvironmentVariableW(L"D64_PIPER_HOME",base,RS_PIPER_PATH);
    unsigned int i;
    if (length && length<RS_PIPER_PATH) {
        if (!rs_join_w(exe,cap,base,L"piper.exe") || !rs_file_exists_w(exe)) return 0;
        wcscpy(home,base);
    } else {
        length=GetModuleFileNameW(NULL,base,RS_PIPER_PATH);
        if (!length || length>=RS_PIPER_PATH) return 0;
        while (length && base[length-1]!=L'\\' && base[length-1]!=L'/') --length;
        base[length]=0;
        for (i=0;i<4;++i) {
            const wchar_t *subdir=i==0?L"piper":i==1?L"speech\\piper":
                                  i==2?L"..\\piper":L"..\\speech\\piper";
            if (!rs_join_w(probe,RS_PIPER_PATH,base,subdir)) continue;
            if (!rs_join_w(candidate,RS_PIPER_PATH,probe,L"piper.exe")) continue;
            if (rs_file_exists_w(candidate)) {
                wcscpy(home,probe); wcscpy(exe,candidate); break;
            }
        }
        if (i==4) return 0;
    }
    /* Prefer the highest-quality voice, accept smaller installed variants. */
    for (i=0;i<3;++i) {
        const wchar_t *file=i==0?L"de_DE-thorsten-high.onnx":
                            i==1?L"de_DE-thorsten-medium.onnx":
                                 L"de_DE-thorsten-low.onnx";
        if (!rs_join_w(model,cap,home,file)) return 0;
        if (rs_file_exists_w(model)) {
            wchar_t config[RS_PIPER_PATH];
            if (swprintf(config,RS_PIPER_PATH,L"%ls.json",model)>0 &&
                rs_file_exists_w(config)) return 1;
        }
    }
    return 0;
}
static unsigned long long rs_hash_text(const char *text,const wchar_t *model) {
    /* FNV-1a: hash both the utterance and the selected model path. */
    unsigned long long hash=14695981039346656037ULL;
    const unsigned char *p=(const unsigned char *)text;
    const wchar_t *m=model;
    while (*p) {hash^=*p++;hash*=1099511628211ULL;}
    while (*m) {hash^=(unsigned int)(*m++);hash*=1099511628211ULL;}
    return hash;
}
static int rs_piper_cache_path(wchar_t *out,size_t cap,
                               const char *text,const wchar_t *model) {
    wchar_t root[RS_PIPER_PATH],folder[RS_PIPER_PATH];
    DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",root,RS_PIPER_PATH);
    if (!n || n>=RS_PIPER_PATH) {
        n=GetTempPathW(RS_PIPER_PATH,root);
        if (!n || n>=RS_PIPER_PATH) return 0;
    }
    if (!rs_join_w(folder,RS_PIPER_PATH,root,L"d64_dism_speech_cache")) return 0;
    if (!rs_dir_exists_w(folder)) CreateDirectoryW(folder,NULL);
    if (!rs_dir_exists_w(folder)) return 0;
    {
        wchar_t name[80];
        unsigned long long hash=rs_hash_text(text,model);
        if (swprintf(name,80,L"piper_%08lx%08lx.wav",
                     (unsigned long)(hash>>32),(unsigned long)(hash&0xffffffffULL))<=0) return 0;
        return rs_join_w(out,cap,folder,name);
    }
}
static int rs_piper_generate(const char *text,wchar_t *result,size_t cap) {
    wchar_t home[RS_PIPER_PATH],exe[RS_PIPER_PATH],model[RS_PIPER_PATH];
    wchar_t command[RS_PIPER_PATH*3],tmp[RS_PIPER_PATH],temp_dir[RS_PIPER_PATH];
    wchar_t tmp_wav[RS_PIPER_PATH];
    SECURITY_ATTRIBUTES sa;
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    HANDLE child_stdin_read=NULL,child_stdin_write=NULL,devnull=INVALID_HANDLE_VALUE;
    DWORD written=0,exit_code=1,wait_result;
    BOOL started;
    size_t n;
    if (!text || !*text || strlen(text)>=RS_MAX_TEXT) return err(2);
    if (!rs_find_piper(home,RS_PIPER_PATH,exe,model)) return err(7);
    if (!rs_piper_cache_path(result,cap,text,model)) return err(6);
    if (rs_valid_wav_w(result)) return 1; /* complete sentence reuse */
    if (!GetTempPathW(RS_PIPER_PATH,temp_dir)) return err(6);
    if (!GetTempFileNameW(temp_dir,L"d64",0,tmp)) return err(6);
    wcscpy(tmp_wav,tmp);
    n=wcslen(tmp_wav);
    if (n>4) wcscpy(tmp_wav+n-4,L".wav");
    DeleteFileW(tmp);
    ZeroMemory(&sa,sizeof(sa)); sa.nLength=sizeof(sa);sa.bInheritHandle=TRUE;
    if (!CreatePipe(&child_stdin_read,&child_stdin_write,&sa,0)) return err(8);
    SetHandleInformation(child_stdin_write,HANDLE_FLAG_INHERIT,0);
    devnull=CreateFileW(L"NUL",GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,
                        &sa,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if (devnull==INVALID_HANDLE_VALUE) {
        CloseHandle(child_stdin_read);CloseHandle(child_stdin_write);return err(8);
    }
    ZeroMemory(&si,sizeof(si)); si.cb=sizeof(si);
    si.dwFlags=STARTF_USESTDHANDLES;
    si.hStdInput=child_stdin_read;
    si.hStdOutput=devnull;si.hStdError=devnull;
    ZeroMemory(&pi,sizeof(pi));
    if (swprintf(command,RS_PIPER_PATH*3,L"\"%ls\" --model \"%ls\" --output_file \"%ls\"",
                 exe,model,tmp_wav)<=0) {
        CloseHandle(child_stdin_read);CloseHandle(child_stdin_write);
        CloseHandle(devnull);return err(8);
    }
    started=CreateProcessW(exe,command,NULL,NULL,TRUE,CREATE_NO_WINDOW,
                           NULL,home,&si,&pi);
    CloseHandle(child_stdin_read);
    CloseHandle(devnull);
    if (!started) {CloseHandle(child_stdin_write);return err(8);}
    WriteFile(child_stdin_write,text,(DWORD)strlen(text),&written,NULL);
    WriteFile(child_stdin_write,"\n",1,&written,NULL);
    CloseHandle(child_stdin_write);
    wait_result=WaitForSingleObject(pi.hProcess,120000);
    if (wait_result==WAIT_TIMEOUT) TerminateProcess(pi.hProcess,1);
    if (wait_result==WAIT_OBJECT_0) GetExitCodeProcess(pi.hProcess,&exit_code);
    CloseHandle(pi.hThread);CloseHandle(pi.hProcess);
    if (wait_result!=WAIT_OBJECT_0 || exit_code!=0 || !rs_valid_wav_w(tmp_wav)) {
        DeleteFileW(tmp_wav);return err(8);
    }
    if (!MoveFileExW(tmp_wav,result,MOVEFILE_REPLACE_EXISTING|MOVEFILE_COPY_ALLOWED)) {
        DeleteFileW(tmp_wav);return err(6);
    }
    g_error=0;return 1;
}
static int32_t rs_piper_speak(const char *text) {
    wchar_t wav[RS_PIPER_PATH];
    if (!rs_piper_generate(text,wav,RS_PIPER_PATH)) return 0;
    if (!PlaySoundW(wav,NULL,SND_FILENAME|SND_SYNC|SND_NODEFAULT)) return err(5);
    g_error=0;return 1;
}
static int32_t rs_piper_save(const char *path,const char *text) {
    wchar_t wav[RS_PIPER_PATH],dest[RS_PIPER_PATH];
    if (!path || !*path) return err(1);
    if (!rs_piper_generate(text,wav,RS_PIPER_PATH)) return 0;
    if (!MultiByteToWideChar(CP_ACP,0,path,-1,dest,RS_PIPER_PATH)) return err(1);
    if (!CopyFileW(wav,dest,FALSE)) return err(6);
    g_error=0;return 1;
}
#endif /* _WIN32 */

static int32_t save_wav_impl(const char *wav_path,const char *text,int direct) {
    uint32_t n=direct?SpeechRenderPhonemes(text,NULL,0):SpeechRenderText(text,NULL,0), i;
    int16_t *samples;
    FILE *f;
    if (!n || !wav_path) return err(n?1:g_error);
    samples=(int16_t*)malloc((size_t)n*sizeof(int16_t));
    if (!samples) return err(3);
    if ((direct?SpeechRenderPhonemes(text,samples,n):SpeechRenderText(text,samples,n))!=n) {
        free(samples);return 0;
    }
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

static int32_t rs_save_sample_sentence(const char *path,const char *text){
    int16_t *pcm=NULL;
    uint32_t frames=0,rate=0,i;
    FILE *file;
    if(!path||!*path)return err(1);
    if(!rs_samples_text(text,&pcm,&frames,&rate))return 0;
    file=fopen(path,"wb");
    if(!file){free(pcm);return err(6);}
    fwrite("RIFF",1,4,file);put_u32(file,36+frames*2);
    fwrite("WAVEfmt ",1,8,file);put_u32(file,16);put_u16(file,1);put_u16(file,1);
    put_u32(file,rate);put_u32(file,rate*2);put_u16(file,2);put_u16(file,16);
    fwrite("data",1,4,file);put_u32(file,frames*2);
    for(i=0;i<frames;i++)put_u16(file,(uint16_t)pcm[i]);
    free(pcm);
    if(fclose(file)!=0)return err(6);
    g_error=0;return 1;
}

int32_t RS_CALL SpeechSaveWav(const char *wav_path,const char *text) {
    if (g_speech_backend == 2) return rs_save_sample_sentence(wav_path,text);
    if (g_speech_backend == 1) {
#ifdef _WIN32
        return rs_piper_save(wav_path,text);
#else
        (void)wav_path; (void)text; return err(7);
#endif
    }
    return save_wav_impl(wav_path,text,0);
}
int32_t RS_CALL SpeechSavePhonemesWav(const char *wav_path,const char *phonemes) {
    return save_wav_impl(wav_path,phonemes,1);
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

#ifdef _WIN32
static int32_t rs_play_sample_text(const char *text){
    int16_t *pcm=NULL;
    uint32_t frames=0,rate=0;
    HWAVEOUT device=NULL;
    WAVEFORMATEX fmt;
    WAVEHDR hdr;
    MMRESULT mm;
    if(!rs_samples_text(text,&pcm,&frames,&rate))return 0;
    memset(&fmt,0,sizeof(fmt));
    fmt.wFormatTag=WAVE_FORMAT_PCM;fmt.nChannels=1;fmt.nSamplesPerSec=rate;
    fmt.wBitsPerSample=16;fmt.nBlockAlign=2;fmt.nAvgBytesPerSec=rate*2;
    mm=waveOutOpen(&device,WAVE_MAPPER,&fmt,0,0,CALLBACK_NULL);
    if(mm!=MMSYSERR_NOERROR){free(pcm);return err(5);}
    memset(&hdr,0,sizeof(hdr));hdr.lpData=(LPSTR)pcm;hdr.dwBufferLength=frames*2;
    mm=waveOutPrepareHeader(device,&hdr,sizeof(hdr));
    if(mm==MMSYSERR_NOERROR)mm=waveOutWrite(device,&hdr,sizeof(hdr));
    if(mm==MMSYSERR_NOERROR){
        while(!(hdr.dwFlags&WHDR_DONE)){
            if(g_stop)waveOutReset(device);
            Sleep(10);
        }
    }else waveOutReset(device);
    if(hdr.dwFlags&WHDR_PREPARED)waveOutUnprepareHeader(device,&hdr,sizeof(hdr));
    waveOutClose(device);free(pcm);
    return mm==MMSYSERR_NOERROR?(g_error=0,1):err(5);
}
#endif

int32_t RS_CALL SpeechSpeak(const char *text) {
    if (g_speech_backend == 2) {
#ifdef _WIN32
        return rs_play_sample_text(text);
#else
        (void)text;return err(5);
#endif
    }
    if (g_speech_backend == 1) {
#ifdef _WIN32
        return rs_piper_speak(text);
#else
        (void)text; return err(7);
#endif
    }
    return speak(text,0);
}
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
void RS_CALL SpeechShutdown(void) {g_stop=1;SpeechUnloadContainer();}
