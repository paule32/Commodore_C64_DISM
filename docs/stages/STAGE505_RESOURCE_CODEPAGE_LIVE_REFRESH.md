[Deutsch](STAGE505_RESOURCE_CODEPAGE_LIVE_REFRESH.md) | [English](STAGE505_RESOURCE_CODEPAGE_LIVE_REFRESH.en.md)

# Stage 505 – Ressourcen-Editor: sofortiges Aktualisieren nach Codepage-Wechsel

**Verbindliche Basis:** `d64_dism_asm_504.zip`.

## Fehlerursache

Nach dem Umschalten der ComboBox `Eigenschaften → Codepage` wurde zwar aus dem `.rc`-Quelltext ein neuer `ResourceCompilation`-Eintrag erzeugt, die Anzeige im Hex-Viewer aber nur indirekt über `QTreeWidget.itemSelectionChanged` aktualisiert. Dieses Signal ist beim Neuerstellen des Baums und anschließender erneuter Auswahl desselben Eintrags nicht zuverlässig. Gleichzeitig konnte das vollständige Neuerstellen der Eigenschaften während `QComboBox.currentIndexChanged` die gerade benutzte ComboBox ersetzen.

## Änderungen

- Die Umkodierung von RC-Rohtext (`RCDATA` / `DLGINCLUDE`) erzeugt beim Wechsel von Unicode (UTF-16LE), UTF-8 oder ASCII sofort eine neue interne Bytefolge. `#pragma code_page(...)` wird im derzeitigen ungespeicherten Editorinhalt angepasst und die RC-Datei ausschließlich **im Speicher** kompiliert.
- Bei unveränderter Ressourcenstruktur werden Größenangaben in der Resource-Baumansicht direkt aktualisiert. Die aktive Eigenschaften-ComboBox bleibt bestehen; Hex-Textspalte und Hex-Bytes werden sofort aus den neu kompilierten Bytes gezeichnet, ohne auf die erneute Auswahlnachricht zu warten.
- Bei strukturellen Änderungen werden Baum und Eigenschaften sicher nach Ende des aktiven ComboBox-Signals wiederaufgebaut.
- Beim normalen Neuanlegen des Ressourcenbaums wird die Anzeige des ausgewählten Eintrags immer explizit synchronisiert (auch ohne `itemSelectionChanged`).
- Bei Kompilierungs-/Kodierungsfehlern (z. B. `Grüße` als ASCII) werden RC-Quelltext, Änderungszustand und ComboBox auf die vorherige gültige Einstellung zurückgesetzt. Die alten Binärdaten bleiben unverändert, und eine Fehlermeldung erscheint in der Statuszeile.
- Die gewählte Codepage wird nach erfolgreichem Umschalten im `.rc`-Quelltext geführt und bei explizitem Speichern übernommen. Bei RES-/COFF-Export entstehen entsprechend neu kompilierte RCDATA-Bytes.

## Formatgrenzen

Die Unicode-Felder von `STRINGTABLE`, `DIALOG`, `MENU` und `VERSIONINFO` sind laut Windows-Ressourcenformat fest als UTF-16LE definiert: Die Kombobox ändert hier die Metadaten und die Anzeige-Kennzeichnung, **nicht** die vorgeschriebene binäre Kodierung. Bereits binär eingebundene Dateien bleiben unverändert. Die `.res`-Codepage-ComboBox bleibt wegen fehlender Codepage-Speicherung im klassischen RES-Header gesperrt.

## Tests

- `python -m py_compile d64_dism.py` erfolgreich.
- `test_stage505_resource_codepage_live_refresh.py` prüft den GUI-Callback mit simuliertem gefülltem Ressourcenbaum, tatsächlichen erzeugten RC-Daten, Live-Hextext und Ressourcenlänge für mehrere aufeinanderfolgende Umschaltungen; außerdem UTF-8, UTF-16LE, fehlgeschlagene ASCII-Konvertierung samt Rollback und Windows-STRINGTABLE-Ausnahme.
- Gemeinsam mit Stage 393, 457 und 501–504: **93 Tests, 7 Subtests erfolgreich**.
- Native Qt5-Fensterdarstellung konnte mangels PyQt5 in dieser Umgebung nicht ausgeführt werden und muss unter Windows visuell bestätigt werden.
