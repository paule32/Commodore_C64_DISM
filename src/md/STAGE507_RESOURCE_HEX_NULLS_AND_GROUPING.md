# Stage 507 – Ressourcen-Hex-Viewer: Nullbytes und 8+8-Trennung

Verbindliche Basis: `d64_dism_asm_506.zip`.

## Ziel

- Die 16 Hexbytes pro Zeile bleiben vollständig und unverändert.
- Genau zwischen Byte 8 und Byte 9 einer vollständig gefüllten Zeile wird ` | ` angezeigt.
- In der Unicode-/UTF-16LE-Byte-Textansicht werden die Originalbytes einzeln dargestellt. Insbesondere erscheint jedes `00`-Byte als Punkt `.`. Das bisherige Zusammenfassen von `64 00` zu nur `d` würde das Nullbyte verstecken.
- Eine zusätzliche Spalte `Unicode-Text (dekodiert)` erhält die lesbare UTF-16LE-Ansicht, auch für Zeichen außerhalb von ASCII, ohne die binären Daten zu verändern.
- Für ASCII und UTF-8 bleibt die codepagegerechte Dekodierung in der Textspalte erhalten, einschließlich über Zeilengrenzen hinweg geteilter UTF-8-Folgen.
- Die Darstellung greift bei allen vorhandenen Aufrufen von `format_resource_hex`, also sowohl bei Wechsel der Resource als auch nach Codepage-/RC-Quellcode-Aktualisierung.

## Beispiel (Offset 0x140)

```text
00000140  64 00 72 00 FC 00 63 00 | 6B 00 74 00 20 00 68 00   d.r.ü.c.k.t. .h.  drückt h
```

## Technische Umsetzung

- `d64_dism.py`: Funktion `format_resource_hex()` aktualisiert.
- Neue gezielte Tests: `test_stage507_resource_hex_nulls_groups.py`.
- Der frühere Test `test_hex_utf16_shows_letters_not_nul_dots` in Stage 504 wurde auf die nun ausdrücklich gewünschte sichtbare Nullbyte-Darstellung umgestellt.

Die Änderungen betreffen ausschließlich die Hex-Ansicht. Die Codepage-Kodierung der RES-/COFF-Daten und die Windows-Ressourcenstruktur bleiben unverändert.

## Validierung

- Python-Syntaxprüfung für `d64_dism.py`.
- Tests Stage 501–507: 86 bestanden.
- Native PyQt5-Anzeige unter Windows hier nicht ausgeführt.
