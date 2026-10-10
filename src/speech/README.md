# d64 Retro Speech / Stage 339

Eigenstaendige, kleine deutsche Sprachengine mit phonembasierter Formantsynthese.
Zielklang: **Retro-Hybrid** aus C64/SAM-artiger Rauheit (Mix=0) und geglaetteten
Amiga/Narrator-artigen Lautuebergaengen (Mix=100). **Keine Emulation** der
Original-Chips oder der proprietaeren Original-Sprachalgorithmen.

Kein WAV-Archiv: Wellenformen werden jedes Mal mathematisch aus Sprachsegmenten
erzeugt. Nur die Demo schreibt *eine* neue WAV-Datei zum Probehoeren.

## Windows 10 PE32 / MSYS2 MINGW32

Aus einer **MINGW32**-Shell (32-Bit `gcc`, nicht MINGW64):

```
python speech/build_pe32.py
speech/bin/retro_speech_demo.exe
speech/bin/retro_speech_demo.exe --text "Guten Tag, ich bin dein Sprachcomputer" --mix 75
```

Build ohne Make; die beiden Artefakte werden getrennt gelinkt:
- `speech/bin/retro_speech.dll`: x86-PE32-C-Runtime mit WinMM-`waveOut`.
- `speech/bin/libretro_speech.dll.a`: **Importbibliothek**, keine statisch gelinkte Engine.
- `speech/bin/retro_speech_demo.exe`: bindet nur die importierten DLL-Symbole.

Bei `--no-play` schreibt die Demo ausschliesslich `retro_hallo.wav`.
Auf Linux kann die Synthese und WAV-Ausgabe mit `gcc` getestet werden; Audio-
Wiedergabe (`SpeechSpeak`) ist auf Windows beschraenkt.

## DLL-Schnittstelle

In `retro_speech.h` deklariert, 32-Bit `__stdcall`, per
`-Wl,--add-stdcall-alias` mit **beiden Exportnamen**:
`SpeechInitialize@4` (dekoriert, MinGW32) und `SpeechInitialize`
(undekoriert, d64_dism-PE32-Import). Die Importbibliothek `libretro_speech.dll.a`
enthaelt damit die fuer `__declspec(dllimport)` benoetigten dekorierten Symbole.

| Export | Zweck |
| --- | --- |
| `SpeechInitialize(22050)` | PCM-Sample-Rate 8000..48000 |
| `SpeechSetMix(55)` | Amiga-Anteil 0..100 %; Rest C64 |
| `SpeechSetPitch(125)` | Grundfrequenz 70..260 Hz |
| `SpeechSetSpeed(100)` | Sprechtempo 50..200 % |
| `SpeechRenderText(text,pcm,capacity)` | PCM-Render; Null-PCM fragt Laenge ab |
| `SpeechRenderPhonemes(tokens,pcm,capacity)` | direkte Lautfolge |
| `SpeechSpeak(text)` | synchrone Windows-waveOut-Ausgabe |
| `SpeechSpeakPhonemes(tokens)` | direkte Lautfolge abspielen |
| `SpeechSaveWav(path,text)` | neue WAV-Datei erzeugen |
| `SpeechStop()` | Abbruchsignal fuer aktive Windows-Wiedergabe |
| `SpeechShutdown()` | Engine stoppen |
| `SpeechGetLastError()` | Fehlernummer |
| `SpeechGetLastErrorText()` | Fehlertext (statischer C-String) |

`SpeechRenderText(...,NULL,0)` liefert die Anzahl benoetigter **int16**-Samples;
`SpeechRenderText(...,buffer,samples)` schreibt sie. Zwei-Aufruf-Protokoll,
keine plattformuebergreifenden Allokatorprobleme.

Phonem-Tokens (durch Leerzeichen getrennt, **case-sensitive**):

```
H A L O _ I CH _ B I N _ D AI N _ SH P R A X K O M P J U T @ R .
```

`_` = kurze Pause, `.` = Satzpause. Vokale `A a E e I i O o U u`,
Umlaute `AE OE UE`, Diphthonge `AI AU OI`, Schwa `@`.
Andere Konsonanten siehe `phones` in `retro_speech.c`.

## Aktuelle Grenzen

- Deutsch-Lexikon und Graphemregeln sind eine **erste experimentelle Stufe**,
  keine vollstaendige deutsche Silbifizierung oder prosodische Analyse.
- Die Stimme ist absichtlich deutlich synthetisch; Stimmqualitaet ist noch
  nicht unter Windows gegen echte Lautsprecher validiert.
- Windows-Ausgabe ist **synchron**: `SpeechSpeak` blockiert bis zum Ende.
  Bei GUI-Anwendungen auf einen Worker-Thread verlagern, damit die Oberflaeche
  bedienbar bleibt.
- API ist nicht gleichzeitig aus mehreren Threads fuer unterschiedliche
  Einstellungen nutzbar; Instanz-Handles und thread-sichere Konfiguration
  gehoeren zu einer spaeteren Stage.
- Direkte dBase-Importdeklarationen und `SAY`-Syntax sind **noch nicht**
  implementiert; dieser Stage liefert die selbststaendige DLL und Demo.
- Neue Quelltexte wurden fuer dieses Projekt verfasst, es werden keine
  originalen SAM-/Narrator-Dateien eingebunden.


## Stage 340: Linkerfehler in MINGW32 behoben

Wenn Stage 339 bei `retro_speech_demo.exe` die Fehlermeldung
`undefined reference to _imp__SpeechInitialize@4` meldet, muss die
DLL **und die Importbibliothek** neu erstellt werden.
Das vorherige `--kill-at` hat den `@N`-Teil aus der DLL und aus der
automatisch erstellten Importbibliothek entfernt. Stage 340 verwendet
`--add-stdcall-alias` und behaelt beide Namensvarianten.

Aus der MSYS2-**MINGW32**-Shell im Verzeichnis `speech` ausfuehren:

```bash
python build_pe32.py
objdump -p bin/retro_speech.dll | grep SpeechInitialize
nm -g bin/libretro_speech.dll.a | grep SpeechInitialize
objdump -p bin/retro_speech_demo.exe | grep retro_speech.dll
./bin/retro_speech_demo.exe --no-play --wav test_hallo.wav
```

Erwartet: DLL-Exports `SpeechInitialize` und `SpeechInitialize@4`,
Importbibliothek mit einem `__imp__SpeechInitialize@4`-Symbol,
Demo-Import von `retro_speech.dll`. Der `--no-play`-Test erzeugt
`test_hallo.wav` ohne dass ein Audiogeraet benoetigt wird.
Beide PE32-Artefakte wurden in einer reinen Linux-Umgebung noch nicht
nativ unter Windows getestet.

## Stage 341 – Phonetik- und Prosodie-Finetuning

Die Stage fuehrt **kein KI-Modelltraining** durch, sondern verbessert die eigene
mathematische Formantsynthese und ihre regelbasierte deutsche Textanalyse.

**Neu an der DLL-C-ABI (PE32 `__stdcall`):**

- `int32_t SpeechSetExpression(int32_t percent)` – `0..100`, Vorgabe `60`.
  Regelt die Staerke von Satzintonation und Wortbetonung. `0` liefert eine
  nahezu gleichmaessige Tonhoehe, `100` einen staerkeren Verlauf.
- `int32_t SpeechSetArticulation(int32_t percent)` – `0..100`, Vorgabe `65`.
  Steuert die Dauer von Lautuebergaengen und die Klarheit von Reibe- und
  Verschlusslauten: kleinere Werte = weicher, groessere = praegnanter.

Beide Setter liefern `1` bei Erfolg, `0` bei ungueltigem Wert und setzen dann
`SpeechGetLastError()` auf `1`. Die vorhandenen Exporte bleiben unveraendert.
Auch diese neuen Funktionen werden mit dem Stage-340-Linkerparameter
`--add-stdcall-alias` jeweils dekoriert und undekoriert exportiert.

**Weitere technische Anpassungen:**

- Wortbetonung auf geeigneten Vokalsegmenten; haeufige Funktionswoerter
  bleiben schwach betont.
- Unterschiedliche Tonhoehenkurven fuer Aussagesatz, Frage und Ausruf;
  Satzpausen beeinflussen nicht mehr die Laenge der Tonhoehenkurve.
- Glaettung von Grundfrequenz und Formanten; weniger abrupte Lautgrenzen
  bei aufeinanderfolgenden stimmhaften Lauten.
- Zusaetzliche Aussprache- und Wortregeln fuer `ck`, `pf`, `ph`, `th`,
  `aa`, `ee`, `oo`, Endungen `-er`, `-en` und weitere deutsche Woerter.
- Sanftes Pegellimit gegen starke Spitzen im PCM-Signal.
- Direkte Phonemfolgen unterstuetzen jetzt `?` (Frage) und `!` (Ausruf)
  als Alternativen zur bestehenden Punkt-Satzpause.

### Beispielprofile (Demo)

Unter **MSYS2 MINGW32** zuerst neu erstellen:

```bash
cd speech
python build_pe32.py
```

Danach aus dem Verzeichnis `speech` ausfuehren:

```bash
./bin/retro_speech_demo.exe --preset hybrid --text "Hallo, ich bin dein Sprachcomputer."
./bin/retro_speech_demo.exe --preset c64   --wav c64.wav --no-play
./bin/retro_speech_demo.exe --preset amiga --wav amiga.wav --no-play
```

Die Presets initialisieren die Werte `mix/pitch/speed/expression/articulation`:

| Profil | Mix (% Amiga) | Pitch | Speed | Expression | Articulation |
| --- | ---: | ---: | ---: | ---: | ---: |
| c64 | 15 | 130 | 105 | 38 | 90 |
| hybrid | 55 | 125 | 100 | 65 | 65 |
| amiga | 85 | 125 | 100 | 85 | 45 |

Nach `--preset` angegebene Optionen ueberschreiben das jeweilige Profil:

```bash
./bin/retro_speech_demo.exe --preset hybrid --expression 90 --articulation 55
```

Die Bezeichnungen C64 und Amiga sind **Klangziele**, keine Originalemulation.
Die Qualitaet bleibt experimentell; insbesondere Betonungswoerterbuch,
Silbenstruktur und natuerliche Sprachuebergaenge sind noch ausbaubar.
Die Sprachengine ist weiterhin nicht thread-safe; `SpeechSpeak()` blockiert
bis zur Beendigung. Direkte dBase-Aufrufe sind noch nicht implementiert.

Tests: `python -m unittest test_stage341_speech_finetune test_stage339_retro_speech test_stage340_speech_pe32_imports -v`
