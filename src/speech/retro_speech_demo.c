/* Demonstrates dynamic linking: this binary contains NO synthesizer source. */
#include "retro_speech.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc,char **argv) {
    const char *text="Hallo, ich bin dein Sprachcomputer.";
    const char *phonemes=NULL;
    const char *wav="retro_hallo.wav";
    int amiga=55, pitch=125, speed=100, expression=60, articulation=65, fluency=75;
    int play=1, backend=0, i;
    const char *container=NULL;
    for (i=1;i<argc;++i) {
        /* Left-to-right CLI: options after --preset override its defaults. */
        if (!strcmp(argv[i],"--preset") && i+1<argc) {
            const char *name=argv[++i];
            if (!strcmp(name,"c64")) {
                amiga=15;pitch=130;speed=105;expression=38;articulation=90;fluency=25;
            } else if (!strcmp(name,"hybrid")) {
                amiga=55;pitch=125;speed=100;expression=65;articulation=60;fluency=75;
            } else if (!strcmp(name,"amiga")) {
                amiga=85;pitch=125;speed=100;expression=80;articulation=35;fluency=100;
            } else {
                fprintf(stderr,"Unknown preset: %s (c64/hybrid/amiga)\n",name);
                return 2;
            }
        }
        else if (!strcmp(argv[i],"--backend") && i+1<argc) {
            const char *name=argv[++i];
            if (!strcmp(name,"piper")) backend=1;
            else if (!strcmp(name,"samples")) backend=2;
            else if (!strcmp(name,"retro")) backend=0;
            else {fprintf(stderr,"Unknown backend: %s\n",name);return 2;}
        }
        else if (!strcmp(argv[i],"--container") && i+1<argc) container=argv[++i];
        else if (!strcmp(argv[i],"--text") && i+1<argc) text=argv[++i];
        else if (!strcmp(argv[i],"--phonemes") && i+1<argc) phonemes=argv[++i];
        else if (!strcmp(argv[i],"--list-phonemes")) {
            int k;
            for (k=0; k<SpeechGetPhonemeCount(); ++k) {
                const char *token=SpeechGetPhonemeToken(k);
                if (token) printf("%s%s", token, (k+1)%10==0?"\n":" ");
            }
            putchar('\n');
            return 0;
        }
        else if (!strcmp(argv[i],"--wav") && i+1<argc) wav=argv[++i];
        else if (!strcmp(argv[i],"--mix") && i+1<argc) amiga=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--pitch") && i+1<argc) pitch=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--speed") && i+1<argc) speed=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--expression") && i+1<argc) expression=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--articulation") && i+1<argc) articulation=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--fluency") && i+1<argc) fluency=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--no-play")) play=0;
        else if (!strcmp(argv[i],"--help")) {
            puts("retro_speech_demo [--container speech.spc] [--backend retro|piper|samples] [--preset c64|hybrid|amiga] [--text TEXT|--phonemes TOKENS] [--list-phonemes] [--wav PATH] [--mix 0..100] [--pitch 70..260] [--speed 50..200] [--expression 0..100] [--articulation 0..100] [--fluency 0..100] [--no-play]");
            return 0;
        } else {fprintf(stderr,"Unknown option: %s\n",argv[i]);return 2;}
    }
    if (!SpeechInitialize(22050) || !SpeechSetMix(amiga) ||
        !SpeechSetPitch(pitch) || !SpeechSetSpeed(speed) ||
        !SpeechSetExpression(expression) || !SpeechSetArticulation(articulation) ||
        !SpeechSetFluency(fluency) || !SpeechSetBackend(backend)) {
        fprintf(stderr,"Setting error: %s\n",SpeechGetLastErrorText());return 1;
    }
    if (container && !SpeechLoadContainer(container)) {
        fprintf(stderr,"Container error: %s\n",SpeechGetLastErrorText());return 1;
    }
    if (!(phonemes?SpeechSavePhonemesWav(wav,phonemes):SpeechSaveWav(wav,text))) {
        fprintf(stderr,"WAV error: %s\n",SpeechGetLastErrorText());return 1;
    }
    printf("WAV: %s | %s: %s | Amiga: %d%% | pitch: %d Hz | speed: %d%% | expression: %d%% | articulation: %d%% | fluency: %d%%\n",
           wav, phonemes?"phonemes":"text", phonemes?phonemes:text,
           amiga,pitch,speed,expression,articulation,fluency);
    if (play && !(phonemes?SpeechSpeakPhonemes(phonemes):SpeechSpeak(text))) {
        fprintf(stderr,"Playback error: %s\n",SpeechGetLastErrorText());
        SpeechShutdown(); return 1;
    }
    SpeechShutdown(); return 0;
}
