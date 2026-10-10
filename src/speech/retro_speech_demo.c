/* Demonstrates dynamic linking: this binary contains NO synthesizer source. */
#include "retro_speech.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc,char **argv) {
    const char *text="Hallo, ich bin dein Sprachcomputer.";
    const char *wav="retro_hallo.wav";
    int amiga=55, pitch=125, speed=100, expression=60, articulation=65;
    int play=1, i;
    for (i=1;i<argc;++i) {
        /* Left-to-right CLI: options after --preset override its defaults. */
        if (!strcmp(argv[i],"--preset") && i+1<argc) {
            const char *name=argv[++i];
            if (!strcmp(name,"c64")) {
                amiga=15;pitch=130;speed=105;expression=38;articulation=90;
            } else if (!strcmp(name,"hybrid")) {
                amiga=55;pitch=125;speed=100;expression=65;articulation=65;
            } else if (!strcmp(name,"amiga")) {
                amiga=85;pitch=125;speed=100;expression=85;articulation=45;
            } else {
                fprintf(stderr,"Unknown preset: %s (c64/hybrid/amiga)\n",name);
                return 2;
            }
        }
        else if (!strcmp(argv[i],"--text") && i+1<argc) text=argv[++i];
        else if (!strcmp(argv[i],"--wav") && i+1<argc) wav=argv[++i];
        else if (!strcmp(argv[i],"--mix") && i+1<argc) amiga=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--pitch") && i+1<argc) pitch=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--speed") && i+1<argc) speed=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--expression") && i+1<argc) expression=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--articulation") && i+1<argc) articulation=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--no-play")) play=0;
        else if (!strcmp(argv[i],"--help")) {
            puts("retro_speech_demo [--preset c64|hybrid|amiga] [--text TEXT] [--wav PATH] [--mix 0..100] [--pitch 70..260] [--speed 50..200] [--expression 0..100] [--articulation 0..100] [--no-play]");
            return 0;
        } else {fprintf(stderr,"Unknown option: %s\n",argv[i]);return 2;}
    }
    if (!SpeechInitialize(22050) || !SpeechSetMix(amiga) ||
        !SpeechSetPitch(pitch) || !SpeechSetSpeed(speed) ||
        !SpeechSetExpression(expression) || !SpeechSetArticulation(articulation)) {
        fprintf(stderr,"Setting error: %s\n",SpeechGetLastErrorText());return 1;
    }
    if (!SpeechSaveWav(wav,text)) {
        fprintf(stderr,"WAV error: %s\n",SpeechGetLastErrorText());return 1;
    }
    printf("WAV: %s | text: %s | Amiga: %d%% | pitch: %d Hz | speed: %d%% | expression: %d%% | articulation: %d%%\n",
           wav,text,amiga,pitch,speed,expression,articulation);
    if (play && !SpeechSpeak(text)) {
        fprintf(stderr,"Playback error: %s\n",SpeechGetLastErrorText());
        SpeechShutdown(); return 1;
    }
    SpeechShutdown(); return 0;
}
