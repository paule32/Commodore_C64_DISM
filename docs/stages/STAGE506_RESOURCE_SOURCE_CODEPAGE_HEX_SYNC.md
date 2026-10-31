[Deutsch](STAGE506_RESOURCE_SOURCE_CODEPAGE_HEX_SYNC.md) | [English](STAGE506_RESOURCE_SOURCE_CODEPAGE_HEX_SYNC.en.md)

# Stage 506 – RC-Codepage im Quelltext und Hex-Viewer synchronisieren

**Verbindliche Basis:** `d64_dism_asm_505.zip`.

## Fehlerursache

Die Methode `WindowsResourceEditorWidget._source_changed()` markierte den RC-Quelltext bislang nur als geändert. Wird `#pragma code_page(1200)`, `#pragma code_page(65001)` oder `#pragma code_page(20127)` im Quellcode von Hand geändert, wurden die Ressourcen nicht neu kompiliert und weder die Hex-Bytes noch die ComboBox im Tab **Eigenschaften** aktualisiert. Die Stage-505-Korrektur griff dagegen nur beim direkten ComboBox-Wechsel.

## Änderung

- `textChanged` startet einen einmaligen, 180 ms entprellten Vorschau-Timer.
- `_refresh_source_preview()` kompiliert den **aktuellen, ungespeicherten** RC-Quelltext im Speicher. Die Ressource wird anhand von Typ, ID und Sprache wieder ausgewählt.
- Hex-Bytes und Textspalte werden nach der *neuen* Codepage dargestellt. Bei gleicher Struktur wird die vorhandene Ressourcenauswahl beibehalten; Längenangaben werden aktualisiert.
- `_sync_codepage_combo()` setzt den im Quelltext gültigen Codepage-Wert auch im Eigenschaften-Tab. ComboBox-Signale werden dabei blockiert, damit keine Rückkopplung entsteht.
- Das Öffnen der Tabs **Eigenschaften** oder **Hex** erzwingt den Abgleich sofort; man muss nicht auf den Timer warten und auch nicht manuell auf „Ressourcen neu einlesen“ klicken.
- Unvollständige oder nicht kodierbare RC-Änderungen belassen die zuletzt gültigen Ressourcendaten im Viewer und liefern eine Statusmeldung. Die Quelltexteingabe des Benutzers bleibt unverändert.
- Eine noch nicht gespeicherte neue RC-Datei kann ebenfalls aus dem Editorinhalt in eine Vorschau kompiliert werden, ohne eine Datei anzulegen.
- Beim Öffnen, Neuanlegen und regulären Kompilieren werden Vorschau-Cache und Timer konsistent zurückgesetzt.

## Kodierungsregeln

Für frei kodierbare Texte in `RCDATA` oder `DLGINCLUDE` werden die Bytes entsprechend `#pragma code_page(...)` tatsächlich geändert: ASCII (20127), UTF-8 (65001), Unicode/UTF-16LE (1200). Ein `WSTRING` bleibt explizit UTF-16LE. `STRINGTABLE`, `DIALOG`, `MENU` und `VERSIONINFO` enthalten gemäß Microsofts binärem Ressourcendateiformat UTF-16LE-Strukturfelder – dort bleibt die physische Kodierung unverändert; die gewählte Codepage wirkt nur als Metadatum. Externe Binärdateien werden nicht konvertiert. Klassische `.res`-Dateien enthalten selbst kein CodePage-Feld.

## Tests

- `python -m py_compile d64_dism.py`: erfolgreich.
- `test_stage506_resource_source_codepage_hex_sync.py`: manuelle Quelltextänderung, mehrmalige Wechsel, Hex-Bytes, ComboBox, Unicode- und UTF-8-Text, ungültiges ASCII, geschützte Windows-Strukturen, ungespeicherte RC-Vorschau.
- Gesamter gezielter Stage-393/457/501–506-Regressionssatz: **100 Tests und 7 Subtests bestanden**.
- Ein echter Windows-PyQt5-Fenstertest ist weiterhin offen, weil PyQt5 in der aktuellen Testumgebung nicht installiert ist.
