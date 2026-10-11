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

## Stage 353 – 40 zusätzliche Phonem- und Allophonvarianten

Stage 352 enthielt 41 Tokens, inklusive vier Pausen-/Satzzeichen.
Stage 353 erweitert die Synthesizer-Tabelle um **genau 40 neue Laute**
(81 Tokens insgesamt). Einige davon sind separate Phoneme in anderen
Sprachen; etliche sind **Lautvarianten/Allophone**, nicht 40 zusätzliche
bedeutungsunterscheidende deutsche Phoneme.

### Neue Tokens (ASCII, Groß-/Kleinschreibung beachten)

| Kategorie | Tokens | Anzahl |
| --- | --- | ---: |
| Lange Vokale | `A: E: I: O: U: AE: OE: UE:` | 8 |
| Kurze/laxe Vokale | `A0 E0 I0 O0 U0 OE0 UE0` | 7 |
| Nasalvokal-Annäherungen | `AN EN ON UN` | 4 |
| R-Varianten/vokalisches R | `RY RX ER` | 3 |
| Silbische Nasale | `M= N= NG=` | 3 |
| Affrikaten | `TS TSH DSH PF` | 4 |
| Reibelaute | `ZH SHH SS` | 3 |
| Zusätzliche Fremdsprachenlaute | `TH DH WW NY` | 4 |
| Behauchte/velare Varianten | `PH THP KH GH` | 4 |
| **Zusammen** | | **40** |

Alle 40 Einträge besitzen individuell definierte Formantfrequenzen,
Stimm-/Rauschanteile und Lautdauern. Nasalierte und behauchte Varianten
sind eine **formantbasierte Retro-Annäherung**, keine phonetisch präzise
Sprachaufnahme. Direkte Lauteinträge sind über `SpeechRenderPhonemes`
und `SpeechSpeakPhonemes` verfügbar.

Die automatische deutsche Textumsetzung erkennt jetzt zusätzlich die
kombinierten Laute `tsch` (`TSH`), `dsch` (`DSH`), `pf` (`PF`),
`ts`/`tz` (`TS`), `ie` (`I:`), `aa`/`ee`/`oo` und Dehnungs-`h`;
wo passend werden `ER`, `N=` oder kurze Vokalvarianten verwendet.
Die Text-zu-Laut-Regeln bleiben heuristisch und bilden nicht alle
regionalen Varianten und Fremdwörter korrekt ab.

### Neue optionale DLL-Exporte

Die bestehende ABI bleibt erhalten. Neu sind diese
`__stdcall`-Exporte (auch ohne @N-Alias fuer den eigenen PE32-Linker):

```c
int32_t SpeechGetPhonemeCount(void);                /* Ergebnis: 81 */
const char *SpeechGetPhonemeToken(int32_t index);    /* Index 0..80 */
int32_t SpeechSavePhonemesWav(const char *path,
                             const char *phoneme_sequence);
```

Der zurückgegebene Token-Zeiger gehört der DLL; er darf nicht freigegeben
werden. Ungültige Indizes liefern `NULL` und Fehler 1.

### Testen unter MSYS2 MINGW32

```bash
cd speech
python build_pe32.py
./bin/retro_speech_demo.exe --list-phonemes
./bin/retro_speech_demo.exe --no-play --phonemes "PF A0 N @ _ DSH U0 NG @ L" --wav phoneme_test.wav
./bin/retro_speech_demo.exe --text "Deutsch, schön und grün!"
```

Der DLL-Build benötigt kein `mingw32-make`. Der PE32-Build und die
Windows-waveOut-Wiedergabe müssen weiterhin unter Windows getestet
werden. Ein Host-Linux-Build mit strikten Warnungsflags sowie
WAV-/Dynamiktests sind im Stage353-Test enthalten.

## Stage 354 – Wortschatz und flüssigere Amiga-orientierte Aussprache

Stage 354 entfernt die 36-ms-Pausen zwischen normalen Wörtern und verbessert
Lautübergänge sowie die harmonische Stimmanregung. Das deutsche
Aussprachewörterbuch umfasst nun **199 eindeutige Einträge** (ohne WAV-Samples).

Neue additive DLL-Funktion:

```c
int32_t SpeechSetFluency(int32_t percent); /* 0..100, Default 75 */
```

Die Demo akzeptiert `--fluency 0..100`; Presets `c64/hybrid/amiga`
verwenden 25/75/100. Für eine weichere Retro-Stimme:

```sh
python speech/build_pe32.py
speech/bin/retro_speech_demo.exe --preset amiga --fluency 100 \
   --text "Guten Morgen. Willkommen beim Amiga."
```

Neue dBase-Befehle: `SET SPEECH FLUENCY n`, `SET SPEECH ARTICULATION n`,
`SET SPEECH EXPRESSION n`. Bei `SET SPEECH MODE AMIGA` wird `FLUENCY=100`
automatisch eingestellt. Zum Linken muss die neue `retro_speech.dll` neben
der PE32-Anwendung vorhanden sein. Es ist weiterhin eine experimentelle,
synthetische Retro-Stimme und **keine echte Amiga-Narrator-Emulation**.

## Stage 355: Fertige deutsche Offline-Stimme mit Piper/Thorsten

Ab Stage 355 kann die PE32-Runtime optional statt der bisherigen Formantsynthese
**Piper TTS** mit der deutschen **Thorsten-Voice** verwenden. Der neue Betriebsmodus
ist ausdrücklich kein Phonem-WAV-Schnipsel-System: Piper erzeugt vollständige,
zusammenhängende deutsche Sätze, die als fertige WAV-Dateien gespeichert und
bei der nächsten wortgleichen Anfrage aus dem Cache abgespielt werden.

Das Paket wird **nicht** zusammen mit den d64_dism-Quellen ausgeliefert. Es umfasst
- die externe Windows-x64-Piper-Laufzeit mit allen zugehörigen DLLs/Daten;
- ein deutsches ONNX-Sprachmodell (empfohlen: `de_DE-thorsten-high`, ca. 114 MB);
- seine zugehörige `*.onnx.json` und die Lizenz-/Modellkarte.

Die ältere Piper-Binary `rhasspy/piper` 2023.11.14-2 ist MIT-lizenziert;
Thorsten-Voice-Datensätze sind laut Model Card CC0. Bei anderweitigen
Versionen müssen deren eigene Lizenzen separat berücksichtigt werden.

### Einrichtung unter Windows 11 x64

In der Projektwurzel (einmalig Internet erforderlich):

```console
python speech/install_piper_voice.py --quality high
```

Das Skript lädt die externe Piper-Windows-Laufzeit und das deutsche Modell
in `speech/piper/`. Es benötigt während der Installation Python, danach beim
Abspielen **kein Python**. Wer die Downloads selbst durchgeführt hat, kann
die Dateien manuell in ein Verzeichnis mit `piper.exe` und dem Modell legen.
**Das komplette Piper-Paket** muss zusammenbleiben, einschließlich der
mitgelieferten DLLs und `espeak-ng-data`-Dateien.

Für ein vom Projekt ausgegebenes Form1.exe sollte das Verzeichnis `piper/`
**neben Form1.exe** liegen. Alternative: die Umgebungsvariable
`D64_PIPER_HOME` auf den Ordner mit `piper.exe` setzen. In der Demo unter
`speech/bin/` wird außerdem das benachbarte `speech/piper/` erkannt.

### dBase-Syntax

```dbase
SET SPEECH MODE PIPER
SET SPEECH ON
SAY "Guten Morgen! Ich bin dein deutscher Sprachcomputer."
SET SPEECH MODE AMIGA
SAY "Zurück zur bisherigen Retro-Stimme."
SET SPEECH OFF
```

`SET SPEECH MODE SAMPLES` ist ein Alias für `PIPER`, da der Modus vollständige
WAV-Samples aus dem vorbereiteten Modell erzeugt und wiederverwendet.
`SET SPEECH MODE C64`, `HYBRID` und `AMIGA` schalten zurück auf die originale
Phonem-/Formantsynthese.

### DLL-Export / Demo

- `SpeechSetBackend(0)` aktiviert die vorhandene Formantsynthese;
- `SpeechSetBackend(1)` verwendet das installierte Piper-Sprachmodell;
- `SpeechSpeak()` und `SpeechSpeakCP1252()` verwenden den ausgewählten Modus;
- `SpeechSaveWav()` erstellt in Piper-Modus eine WAV aus dem kompletten Text;
- `SpeechRenderText()` / `SpeechRenderPhonemes()` bleiben weiterhin die
  bestehenden Formant-/Phonem-PCM-APIs, auch im Piper-Modus.

Demo nach Neuaufbau mit `python speech/build_pe32.py` in MINGW32:

```console
speech/bin/retro_speech_demo.exe --backend piper --text "Guten Morgen!" --wav hallo.wav --no-play
speech/bin/retro_speech_demo.exe --backend piper --text "Guten Morgen!" --wav hallo.wav
```

Der Cache liegt unter `%LOCALAPPDATA%/d64_dism_speech_cache/` (ersatzweise
TEMP) und bewahrt zusammengehörige Satz-WAVs auf; ein bereits bekannter Satz
benötigt dadurch keinen erneuten Modelllauf. Nach Modellwechsel kann man
veraltete WAVs dort manuell löschen.

### Grenzen

- Windows 11 **x64** erforderlich für die angebotene Piper-Windows-amd64-Binary;
  der aufrufende dBase-Prozess bzw. `retro_speech.dll` darf trotzdem PE32 sein.
- Nur Windows-Piper ist implementiert; die Linux-C99-Tests prüfen die
  neue API, nicht die native Windows-Wiedergabe.
- Die Piper-WAV-Erzeugung und WinMM-Wiedergabe sind derzeit **synchron**.
  Bei GUI-Aufrufen muss ein Worker-Thread verwendet werden, um das
  Hauptfenster nicht zu blockieren; eine zweite Anfrage darf außerdem nicht
  parallel dieselbe Instanz unkoordiniert verwenden.
- Piper benötigt beim ersten Satz Modelllade- und Berechnungszeit. Ein
  weiterer Aufruf desselben Satzes wird über den Cache schneller.
- Wenn Piper oder die Modelldatei fehlen, liefert die Sprach-DLL Fehler 7,
  bei einem fehlgeschlagenen Piper-Aufruf Fehler 8. Es erfolgt **kein
  stillschweigender Rückfall auf die schlecht verständliche Stimme**.
- Die frei einstellbaren bisherigen Formantregler `MIX`, `ARTICULATION`,
  `PITCH`, `FLUENCY` usw. ändern den Piper-Modellklang nicht unmittelbar.

## Stage 356: SPC1-Sprachcontainer und IMA-ADPCM

Die Sprach-DLL kann nun direkt einen `.spc`-Container von `speechConvert.py` lesen.
Mit `SET SPEECH MODE SAMPLES` wird **Backend 2 (Sample-Container)** gewählt,
während `SET SPEECH MODE PIPER` Backend 1 beibehält. Die gewünschten Wörter
müssen im Container hinterlegt sein (ansonsten Fehlercode 9). Der Container
wird über `D64_SPEECH_CONTAINER`, `speech.spc` im Arbeitsverzeichnis oder
neben der EXE gefunden. Anwendungsprogramme können `SpeechLoadContainer(path)`
aufrufen. Weitere Exporte: `SpeechUnloadContainer`, `SpeechRenderSample`,
`SpeechGetLastSampleRate`, `SpeechGetContainerEntryCount`,
`SpeechGetContainerEntryName`.

`--gzip/-gz` speichert WAV-Payloads optional zusätzlich komprimiert; die
Kennzeichnung erfolgt pro Container-Eintrag im Codec-Byte (`0x80`). Dafür
muss im 32-Bit-Windows-Prozess eine passende `zlib1.dll` verfügbar sein.
Ungepackte Einträge benötigen keine zlib-DLL. WAV-PCM16 und Mono-IMA-ADPCM
werden ohne externe Audio-Decoder verarbeitet. MP3 und Ogg sind im nativen
Containerleser derzeit nur als nicht abspielbare Einträge erkennbar.
Details: `STAGE356_SPC_GZIP_NATIVE_DECODER.md`.
