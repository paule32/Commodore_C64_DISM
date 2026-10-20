# Stage 404 – C64-Sprites als originale VIC-II-Rohdaten

**Ausgangsbasis:** `d64_dism_asm_403.zip` (alle anderen Komponenten unverändert).

## Problem und Korrektur

Bis Stage 403 war im Sprite-Builder `.c64sprite` das voreingestellte
Speicherformat. Diese Datei enthält JSON mit `data_hex` sowie Palette,
Farben, Modus und Skalierungsflags. Der C64 kann diese JSON-Datei nicht
als Hardware-Sprite verwenden.

Ab Stage 404 ist **`.spr`** das voreingestellte Dateiformat:

- `Neues Sprite` und `Speichern unter` erzeugen standardmäßig `.spr`.
- `.spr`, `.sprite` und `.bin` werden als **reine Binärdaten** geschrieben und
  eingelesen, niemals als JSON oder als Text-Hexliste.
- Ein Hardware-Sprite besteht aus **63 Bytes Bilddaten**. Die typische
  Dateidarstellung mit **64 Bytes pro Sprite** enthält ein zusätzliches
  Ausrichtungsbyte (dessen Wert beim Laden/Speichern erhalten bleibt).
- Rohdateien mit 63 oder 64 Bytes pro Sprite werden unterstützt; neue
  Dateien verwenden **64 Bytes pro Sprite**. Mehrere Sprites werden
  unmittelbar aneinandergereiht: 8 Sprites = 512 Bytes.
- Es werden **keine** zwei PRG-Ladeadressbytes vorangestellt. Für
  BASIC-`LOAD ...,8,1` bereitet der bestehende Stage-402-Weg aus `.spr`
  bei der VICE-Übertragung eine eigene Datei mit `$3000`-Header vor.
- Bereits existierende `.c64sprite`-JSON-Projekte sind weiterhin **lesbar**.
  Beim Speichern dieser Altdateien wird `Speichern unter` mit `.spr`
  vorgeschlagen. Das JSON-Original bleibt unverändert. Die neue `.spr`
  wird nach erfolgreichem Speichern unter `C= 64 Sprites` eingetragen.
- Neue ungespeicherte Projektblätter heißen `Sprite_1.spr`, `Sprite_2.spr` usw.
  Die Projektdatei speichert nur die Dateiverknüpfungen wie zuvor.

## VIC-II-Einschränkung

C64-Sprite-Rohdaten enthalten **keine** Farbeinstellungen, kein
HiRes-/Multicolor-Flag, keine Paletten-RGB-Werte und keine Spriteskalierung.
Die Werkzeuge zum Malen mit den 16 auswählbaren C64-Farben funktionieren
unverändert, aber nach dem Laden einer `.spr` werden Modus und
Farbregister auf die Editor-Vorgaben zurückgesetzt. Auf dem C64 müssen
`$D01C` (Multicolor), `$D025`, `$D026`, `$D027` bis `$D02E` usw.
beim Anzeigen durch BASIC/Assembler gesetzt werden. Das ist eine
Eigenschaft des originalen Hardwareformats und kein Datenverlust der Bitmap.

## Prüfungen

`test_stage404_sprite_native_storage.py` deckt Standardendung,
64-Byte-Binärspeicherung, Roundtrip 63/64, JSON-Migrationspfad und
Verweigerung des JSON-Exports ab. Bestehende Tests für Pixelcodecs,
Farbregister, Projektbaum und VICE-Dateistaging sind ebenfalls relevant.
Ein interaktiver Windows-/PyQt5-Test ist weiterhin erforderlich.
