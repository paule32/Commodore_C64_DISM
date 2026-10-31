# Stage 508 – Ressourcen-Editor: Codepage bestimmt die STRINGTABLE-Hexansicht

Verbindliche Ausgangsbasis: `d64_dism_asm_507.zip`.

## Reproduzierter Fehler

Bei `RT_STRING`/`STRINGTABLE` erzwang `format_resource_hex()` in Stage 507
für **jede** Codepage UTF-16LE. Eine Änderung der ComboBox auf ASCII oder
UTF-8 änderte daher höchstens das Codepage-Metadatum, nicht die im Hex-Tab
sichtbaren Bytes. Die reale Windows-STRINGTABLE besteht aus 16
length-prefixed UTF-16LE-Strings; ihre Umwandlung in echte ASCII-Daten im
RES-/COFF-Format wäre dagegen ungültig.

## Änderung

- `d64_dism.py`: neuer Helfer `_resource_stringtable_text_preview()`.
  Er liest die 16 Längenfelder der RT_STRING-Ressource, dekodiert die
  zugehörigen UTF-16LE-Zeichenketten und erstellt eine **nur für den Viewer**
  geltende Byteansicht in der ausgewählten Codepage.
- Der Hex-Viewer zeigt bei **Unicode** die unveränderten Originalbytes samt
  `00`-Punkten (Stage 507).
- Bei **ASCII** erscheinen die Zeichen als einbyte-kodierter Text ohne die
  UTF-16LE-Nullbytes und ohne die strukturellen 16-Bit-Längenfelder.
- Bei **UTF-8** erscheinen echte UTF-8-Bytes (z. B. `ü` = `C3 BC`).
- Angezeigte Offsets beziehen sich weiterhin auf die **Original-Ressource**;
  jedes Textbyte wird der ursprünglichen UTF-16LE-Position zugeordnet. Die
  16-Byte-Zeilengrenzen der Originalressource bleiben so erhalten.
- Nicht in 7-Bit-ASCII repräsentierbare Zeichen werden **nur in der Vorschau**
  durch `?` (`3F`) ersetzt, mit einem Hinweis im Header; Originaldaten bleiben
  unverändert. Es findet **keine verlustbehaftete Speicherung** statt.
- Beschädigte/unvollständige Stringtabellen fallen auf die unveränderte
  Originalbyteansicht zurück.
- Die bereits vorhandenen Aktualisierungswege für Codepage-ComboBox, direktes
  Ändern von `#pragma code_page(...)` und Ressourcenauswahl nutzen alle
  `format_resource_hex()`; der neue Modus greift daher ohne separates Signal.

## Originalbeispiel (STRINGTABLE, 346 Bytes)

```text
Unicode:
00000150  61 00 62 00 65 00 6E 00 | 2E 00   a.b.e.n...  aben.

ASCII:
00000150  61 62 65 6E 2E                    aben.

UTF-8:
00000150  61 62 65 6E 2E                    aben.
```

Für `drückt h` an Offset 0x140 gilt in der UTF-8-Textvorschau:

```text
00000140  64 72 C3 BC 63 6B 74 20 | 68   drückt h
```

Bei ASCII steht dort `64 72 3F 63 6B 74 20 68` (`dr?ckt h`), da
`ü` nicht Teil des ASCII-Zeichensatzes ist.

## Auswirkungen auf andere Ressourcentypen

- `RT_RCDATA` und freie RC-Textdaten behalten die echte binäre Codepage-
  Neukodierung der Stages 504–506.
- `RT_DIALOG`, `RT_MENU`, `RT_VERSION` verwenden weiterhin ihre durch
  Windows vorgegebenen strukturellen UTF-16LE-Felder.
- Die `.res`-/COFF-Erzeugung, Ressourcenlänge und Speicherbytes bleiben
  gegenüber Stage 507 unverändert.

## Validierung

- Neue Regressionstests: `test_stage508_resource_hex_stringtable_preview.py`.
- Vollständiges 346-Byte-Beispiel einschließlich Originaloffset `0x150`
  reproduziert und für Unicode/ASCII/UTF-8 verglichen.
- Qt-unabhängige Widget-Methodentests: Codepage-ComboBox, Quelltext-`
  #pragma`-Änderung, Hex-Refresh, Byteidentität und Dateipersistenz.
- Python-Syntaxprüfung von `d64_dism.py` erfolgreich.
- Gezielte Stage-501–508-Regressionstests: 94 bestanden.
- Native PyQt5-Windows-GUI hier nicht verfügbar; visuelle Prüfung ausstehend.
