# speechConvert.py – PCM-WAV, IMA-ADPCM und indexierter Sprachcontainer

`python speechConvert.py --help` zeigt alle Optionen. Benötigt **Python 3.9+**, keine Python-Fremdpakete.  Die Standardkodierung ist **IMA-ADPCM** (Microsoft WAV-Format-Tag `0x0011`, 4 Bit pro Sample). Für `--convert mp3` und `--convert ogg` wird **VLC** über `vlc.exe` gestartet.

## Beispiele

```powershell
# 200 ms Stille entfernen; WAV in IMA-ADPCM schreiben (Standard)
python speechConvert.py du.wav --strip -ow du_adpcm.wav

# 10 ms Stille beibehalten
python speechConvert.py du.wav -s --keep-ms 10 -ow du_adpcm.wav

# WAV unverändert (PCM) nach dem Kürzen ausgeben
python speechConvert.py du.wav -s -c pcm -ow du_pcm.wav

# Eintrag hinzufügen / überschreiben
python speechConvert.py du.wav -s -oc german_speech.spc -a DU

# Einen weiteren Eintrag aus der WAV-Datei mit ihrem Basisnamen hinzufügen
python speechConvert.py hallo.wav -s -oc german_speech.spc

# Eintrag löschen
python speechConvert.py -oc german_speech.spc -d DU

# Auflisten und CRC prüfen
python speechConvert.py -oc german_speech.spc --list --verify

# Eine Batchdatei abarbeiten
python speechConvert.py '@sprach_batch.txt' -oc german_speech.spc

# MP3 mit VLC erzeugen (VLC muss installiert sein)
python speechConvert.py du.wav -s -c mp3 --vlc 'C:\Program Files\VideoLAN\VLC\vlc.exe'

# MP3 in Sprachcontainer übernehmen
python speechConvert.py du.wav -s -c mp3 -oc german_speech.spc -a DU
```

`-ow` steht ausdrücklich für eine WAV-Ausgabedatei: erlaubt sind `ima-adpcm` und `pcm`. Bei MP3/Ogg ohne Container erzeugt das Programm automatisch eine Datei mit `.mp3` beziehungsweise `.ogg`.

## Batchdatei (UTF-8, optional UTF-8 BOM)

Format einer Zeile: `<WAV> [S] <A|D>`. `S` bedeutet `--strip`, ist optional. `A` fügt hinzu/ersetzt, `D` löscht den Eintrag, der dem WAV-Dateistamm entspricht; die zu löschende WAV-Datei muss nicht existieren. Zeilen, die mit `#` oder `;` beginnen, werden ignoriert. Pfade mit Leerzeichen müssen **in Anführungszeichen** stehen.

```text
"du.wav" S A
"ich.wav" S A
"hallo welt.wav" A
"alter_eintrag.wav" D
```

Relative Eingabepfade sind relativ zur Batchdatei. Ein Schalter `-s` auf der Kommandozeile kürzt **alle** A-Einträge, unabhängig vom jeweiligen `S`.

## Das `.spc`-Dateiformat, Version 1

**Little Endian, keine zusätzliche Kompression**, schnelle Suche über das am Dateiende liegende Indexverzeichnis. Vollständige PCM-/ADPCM-WAV-Dateien bzw. MP3-/Ogg-Daten sind die Payloads. Die Runtime kann über Offset und Länge unmittelbar zum Datensatz springen. Einträge werden bei Änderungen atomar in einen neuen Container kopiert, der ursprüngliche Container bleibt bei Fehlern erhalten.

Dateiheader (32 Byte):

| Offset | Typ | Feld |
|--:|---|---|
| 0 | 8 Byte | Magic `SPCHV1\0\0` |
| 8 | uint16 | Version `1` |
| 10 | uint16 | Flags `0` |
| 12 | uint32 | Anzahl Einträge |
| 16 | uint64 | Verzeichnis-Offset |
| 24 | uint64 | Verzeichnis-Größe |

Jeder Eintrag im Verzeichnis hat 36 feste Bytes, gefolgt vom UTF-8-Namen ohne Nullterminator:

| Rel. Offset | Typ | Feld |
|--:|---|---|
| 0 | uint16 | Byte-Länge des UTF-8-Namens |
| 2 | uint8 | Codec: 1=PCM-WAV, 2=IMA-ADPCM-WAV, 3=MP3, 4=Ogg |
| 3 | uint8 | Kanalzahl |
| 4 | uint32 | Sample-Rate |
| 8 | uint64 | Payload-Offset |
| 16 | uint64 | Payload-Größe |
| 24 | uint64 | Frame-Zahl der ursprünglichen PCM-Aufnahme |
| 32 | uint32 | CRC32 der Payload |
| 36 | variable | UTF-8-Name |

Laufzeit: Die Stage-356-C-Runtime besitzt bereits einen nativen SPC-Containerleser und einen PCM16-/IMA-ADPCM-Decoder. Die Python-Vorschau ab Stage 359 nutzt einen eigenen Decoder. Das Containerformat bleibt unverändert.

## Hinweise und Grenzen

* `--strip` entfernt **nur exakt stille PCM-Frames am Ende**, keine leisen Ausklänge und keine 0-Bytes aus der Mitte der WAV-Datei. Für 8-Bit-PCM ist Stille `0x80`, für höhere Wortbreiten `0x00` je Sample.
* IMA-ADPCM-WAV erzeugt WAV mit 256-Byte-Monoblöcken und `fact`-Chunk mit der tatsächlichen Sample-Anzahl; Stereo-/Mehrkanal-Eingaben werden dafür zu Mono gemischt.
* IMA-ADPCM ist verlustbehaftet, braucht aber keine zusätzlichen Decoder-Bibliotheken beim **Erstellen**. Bei der **Wiedergabe** des SPC-Containers muss deine Runtime den gewählten Codec unterstützen.
* VLC wird für MP3 und Ogg benötigt. VLC-Unterstützung hängt von deiner Installation/den enthaltenen Encodern ab; das kann erst unter Windows mit deiner `vlc.exe` getestet werden.
* Neue Einträge mit gleichem Namen überschreiben alte Einträge unabhängig von Groß-/Kleinschreibung.
* Die Batchdatei wird vor der Containeränderung vollständig auf Syntaxfehler geprüft.

## Stage 356: Optionales --gzip / -gz

```powershell
python speechConvert.py du.wav -s -a DU -oc sprache.spc --gzip
python speechConvert.py '@sprach_batch_beispiel.txt' -oc sprache.spc -gz
python speechConvert.py -oc sprache.spc --list --verify
```

`--gzip` gilt **ausschließlich für `--output-container`**; eine mit `--output-wav` erzeugte WAV wird **nicht** gzip-komprimiert, sondern bleibt eine Standard-WAV. Zuerst erfolgt die gewählte Konvertierung (standardmäßig IMA-ADPCM), dann gzip (Level 9), danach wird die endgültige Payload in den Container geschrieben.

SPC1 bleibt in der Struktur unverändert: Im Eintragsfeld `codec` signalisiert Bit 7 (`0x80`) gzip. Die unteren 7 Bit bleiben der reguläre Codec (1=PCM-WAV, 2=IMA-WAV, 3=MP3, 4=Ogg). CRC32 wird über die komprimierten Bytes berechnet. `--verify` prüft neben CRC32 auch die GZIP-Integrität und begrenzt die Entpackung auf 64 MiB. Einträge ohne gzip behalten die gleiche Kodierung wie zuvor.

Die neue C-Runtime `speech/spc_reader.c` unterstützt gepackte und ungepackte PCM16-/IMA-WAV-Payloads. GZIP benötigt zur Laufzeit zlib (Windows: **32-Bit `zlib1.dll`** für eine PE32-Runtime). Die Speicherung von MP3/Ogg wird im Tool weiterhin unterstützt, aber die C-Runtime kann diese nicht ohne weitere Decoder abspielen.

## Stage 357: Sprachwahl `--lang`/`-l`, Container-Merge `--merge`/`-m`

```powershell
# Datei 2 an Datei 1 anhaengen; bei gleichen Eintragsnamen Datei 1 behalten
python speechConvert.py -m deutsch.spc englisch.spc --verify

# Alle Quellen unveraendert lassen, in neue Datei schreiben
python speechConvert.py -m deutsch.spc englisch.spc -oc gesamt.spc --verify

# Bei Namenskonflikt stattdessen Eintrag aus Datei 2 nehmen
python speechConvert.py -m deutsch.spc englisch.spc --on-conflict replace

# Fertige deutsche Aufnahme mit Piper und automatisch gewaehltetem Modell
python speechConvert.py --text "Guten Tag" -l de_DE -ow tag.wav

# Englische Aufnahme mit en_US-amy-medium
python speechConvert.py --text "Hello world" -l en_US -ow hello.wav

# Andere Stimmen aus dem offiziellen Katalog nennen
python speechConvert.py --list-voices
```

Piper wird ueber das ONNX-Modell auf die Sprache festgelegt. `--lang` wirkt daher bei `--text`, nicht bei bereits existierenden WAV-Samples. Fuer die Textsynthese muss `piper.exe` plus `.onnx` und `.onnx.json` lokal installiert sein. Mit `--voice`, `--quality`, `--model-dir`, `--model` und `--piper` kann die Auswahl verfeinert werden. Die Standardstimmen sind `de_DE-thorsten-high` und `en_US-amy-medium`. Die komplette Beschreibung und Beispiele fuer weitere Stimmen stehen in `STAGE357_SPEECHCONVERT_LANG_MERGE.md`.

## Stage 358: Windows-Fehler `0xC0000409` beim Piper-Start

`3221226505` entspricht `0xC0000409` (Fail Fast). Das ist ein Absturz des gestarteten Piper-Prozesses und kein `gzip`-/SPC-Fehler. Bei Piper 1.2.0 sind vergleichbare Windows-Abstürze bekannt.

Neu: `--piper-backend auto|exe|python` und `--piper-python PYTHON`. `auto` ist Standard; es nutzt `piper.exe`, probiert aber bei einer fehlenden EXE oder genau diesem NTSTATUS das Python-Backend. Alle anderen Fehler bleiben sichtbar. Das Python-Backend kann auch erzwungen werden:

```powershell
python -m pip install --upgrade piper-tts
python speechConvert.py --text "Guten Morgen" -l de_DE --voice kerstin --quality low -a GUTENMORGEN -gz -oc samples/deu/deutsch.spc --piper-backend python
```

Der Python-Interpreter muss `piper-tts` installiert haben. Beide Backend-Varianten verwenden die **gleichen lokal installierten** `.onnx` und `.onnx.json` Dateien. Modell-Laufzeitprobleme können auch in der Python-Variante auftreten; eine native Windows-Bestätigung steht aus. Weitere Details in `STAGE358_PIPER_WINDOWS_FAILFAST.md`.

## Stage 359: `--test EINTRAG` - Sprachsample aus dem SPC-Container anhoeren

```powershell
# Gesprochenes Wort GUTENMORGEN aus dem Container abspielen
python speechConvert.py -oc samples/deu/deutsch.spc --test GUTENMORGEN

# Container auflisten und pruefen
python speechConvert.py -oc samples/deu/deutsch.spc --list --verify

# Listung und Vorschau kombinieren
python speechConvert.py -oc samples/deu/deutsch.spc --list --test GUTENMORGEN

# MP3/Ogg-Eintrag bei Bedarf mit VLC abspielen
python speechConvert.py -oc samples/deu/deutsch.spc --test EINTRAG --vlc 'C:\Program Files\VideoLAN\VLC\vlc.exe'
```

`--test` sucht den Eintragsnamen ohne Unterscheidung der Gross-/Kleinschreibung,
laedt nur den ausgewaehlten Datensatz, prueft CRC32 und entpackt gegebenenfalls
GZIP. Anschliessend wird PCM oder IMA-ADPCM in 16-Bit-Mono-WAV umgewandelt und
unter Windows ueber die Python-Standardbibliothek `winsound` synchron abgespielt.
Dafuer wird kein VLC benoetigt; MP3/Ogg dagegen werden ueber VLC abgespielt.

`--test` aendert den Container nicht und kann nicht mit schreibenden Operationen
kombiniert werden. `--list` und `--verify` bleiben erlaubt.
Ein fehlerhafter GZIP-Strom, eine ungueltige CRC32, defekte ADPCM-Bloecke
oder ein fehlender Eintrag erzeugen eine klare Fehlermeldung.

Eine echte Windows-Audiowiedergabe wurde lokal noch nicht getestet.
