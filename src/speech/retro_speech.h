#ifndef D64_RETRO_SPEECH_H
#define D64_RETRO_SPEECH_H

#include <stdint.h>

#ifdef _WIN32
# ifdef RETRO_SPEECH_BUILD
#  define RS_API __declspec(dllexport)
# else
#  define RS_API __declspec(dllimport)
# endif
# define RS_CALL __stdcall
#else
# define RS_API
# define RS_CALL
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Windows PE32 stable C ABI: DWORD/int32 values and pointers; stdcall.
 * DLL exports both decorated (SpeechInitialize@4) and undecorated
 * (SpeechInitialize) names via the linker --add-stdcall-alias option.
 * All audio is signed 16-bit little-endian mono PCM. */
RS_API int32_t  RS_CALL SpeechInitialize(int32_t sample_rate);
RS_API int32_t  RS_CALL SpeechSetMix(int32_t amiga_percent); /* 0=C64, 100=Amiga */
RS_API int32_t  RS_CALL SpeechSetPitch(int32_t pitch_hz);   /* 70..260 */
RS_API int32_t  RS_CALL SpeechSetSpeed(int32_t percent);    /* 50..200 */
/* Stage 341 tuning knobs: percentages 0..100. Defaults: 60 / 65.
 * Expression controls pitch accents and sentence intonation;
 * articulation controls transitions and consonant definition. */
RS_API int32_t  RS_CALL SpeechSetExpression(int32_t percent);
RS_API int32_t  RS_CALL SpeechSetArticulation(int32_t percent);
/* Stage 354: connected speech/coarticulation, 0..100; default 75.
 * 0 is more segmented/retro, 100 smoother and more Amiga-oriented. */
RS_API int32_t  RS_CALL SpeechSetFluency(int32_t percent);
/* Stage 356: 0 = formant; 1 = offline Piper; 2 = SPC sample playback.
 * Stage 355: 0 = existing formant synthesizer; 1 = external offline Piper voice.
 * Piper is a separate, user-installed package; the 32-bit DLL launches the
 * Windows x64 CLI and replays/caches whole-sentence WAV files. */
RS_API int32_t  RS_CALL SpeechSetBackend(int32_t backend);
/* SPC sample backend: indexed on demand; supports PCM16 and IMA-ADPCM WAV,
 * optionally per-entry gzip (requires zlib1.dll on Windows).
 * --gzip is an on-disk storage option, not a playback codec.
 * SpeechLoadContainer uses an ANSI path on Windows, as SpeechSaveWav does.
 * Missing samples/error conditions are returned via SpeechGetLastErrorText.
 * SpeechRenderSample returns required PCM frames when pcm==NULL.
 * SpeechGetLastSampleRate reports rate of most recently decoded sample. */
RS_API int32_t  RS_CALL SpeechLoadContainer(const char *path);
RS_API int32_t  RS_CALL SpeechUnloadContainer(void);
RS_API int32_t  RS_CALL SpeechGetContainerEntryCount(void);
RS_API const char *RS_CALL SpeechGetContainerEntryName(int32_t index);
RS_API int32_t  RS_CALL SpeechGetLastSampleRate(void);
RS_API uint32_t RS_CALL SpeechRenderSample(const char *name, int16_t *pcm, uint32_t capacity);
/* Stage 353: enumerate the available phoneme/allophone tokens.
 * SpeechGetPhonemeToken returns a constant DLL-owned NUL-terminated string,
 * or NULL for an out-of-range index. Never free the returned pointer. */
RS_API int32_t  RS_CALL SpeechGetPhonemeCount(void);
RS_API const char *RS_CALL SpeechGetPhonemeToken(int32_t index);
RS_API int32_t  RS_CALL SpeechGetSampleRate(void);
RS_API int32_t  RS_CALL SpeechGetLastError(void);
RS_API const char *RS_CALL SpeechGetLastErrorText(void);

/* Output capacity is in 16-bit *samples*, not bytes.
 * With pcm==NULL, returns required sample count; otherwise the samples
 * actually written. Returns 0 on invalid input or insufficient buffer. */
RS_API uint32_t RS_CALL SpeechRenderText(const char *utf8, int16_t *pcm, uint32_t capacity);
RS_API uint32_t RS_CALL SpeechRenderPhonemes(const char *phonemes, int16_t *pcm, uint32_t capacity);

/* wav_path is a UTF-8 file path only on POSIX; on Windows it is the
 * current ANSI-codepage path (keep it ASCII for portable examples). */
RS_API int32_t  RS_CALL SpeechSaveWav(const char *wav_path, const char *utf8);
/* Stage 353: WAV output for space-separated phoneme tokens (no samples). */
RS_API int32_t  RS_CALL SpeechSavePhonemesWav(const char *wav_path, const char *phonemes);
/* Plays synchronously via waveOut on Windows; on other hosts returns error 5. */
RS_API int32_t  RS_CALL SpeechSpeak(const char *utf8);
/* dBase dynamic strings: code page Windows-1252, explicit byte length.
 * The function converts into UTF-8 before calling the synthesizer. */
RS_API int32_t  RS_CALL SpeechSpeakCP1252(const char *text, uint32_t length);
RS_API int32_t  RS_CALL SpeechSpeakPhonemes(const char *phonemes);
RS_API int32_t  RS_CALL SpeechStop(void);
RS_API void     RS_CALL SpeechShutdown(void);

#ifdef __cplusplus
}
#endif
#endif
