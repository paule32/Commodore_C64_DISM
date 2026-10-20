# Stage 442 – Mathematik / Fakten / Zahlen / Römische . . .

**Verbindliche Grundlage:** `d64_dism_asm_441.zip`.

## Einbindung

Das Blatt **„Römische . . .“** wurde als auswählbarer Eintrag unter
**Lernen → Mathe → Fakten → Zahlen** ergänzt. Ein einfacher Klick öffnet
rechts die zugehörige Lernseite. Die vorhandenen Einträge bleiben erhalten.

## Native Qt-Textdarstellung

Die Datei `roman_numerals_fact.py` enthält einen abgeleiteten
`QPlainTextEdit` (`RomanNumeralsFactWidget`), der `setReadOnly(True)`
verwendet. Es wird **kein Pixelbild** eingebettet.

Gestaltung entsprechend der gelieferten Referenz:

- Blaue, zentrierte Überschrift **RÖMISCHE ZAHLEN** (ins Deutsche übertragen).
- Zwei waagerechte Trennlinien als Textzeichen.
- Grundsymbole `I V X L C D M` und Werte `1 5 10 50 100 500 1000`.
- Dreispaltige, 20-zeilige Tabelle: `1..20`, `21..40`,
  `41..50`, `60`, `70`, `80`, `90`, `100`, `200`, `300`, `400`, `500`, `1000`.
- Tabstopps und `QTextCharFormat`/`QTextBlockFormat` für Formate und Spalten.
- Text bleibt markier- und kopierbar, aber nicht editierbar.
- Eigenständige Scrollbars der `QPlainTextEdit`-Seite. Kein doppelter Scrollbereich.
- Helle Papierfläche (auch beim dunklen Anwendungstheme) für optische Nähe zur Vorlage.

Das Logo aus der Referenz wurde bewusst nicht nachgezeichnet oder als Bild
übernommen.

## Geänderte Dateien

- `d64_dism.py` – Import, QStackedWidget-Seite, Navigationsknoten,
  Dark-/Light-Mode und `open_fact`-Dispatch.
- `roman_numerals_fact.py` – neuer QPlainTextEdit und reine Umrechnungsfunktion.
- `test_stage442_roman_numerals_fact.py` – fünf neue Tests.
- `STAGE442_MATHE_ROEMISCHE_ZAHLEN_QPLAINTEXT.md` – diese Dokumentation.

## Prüfungen

- Stage 442: 5 Tests bestanden.
- Stage 425 (Navigation): 4 Tests bestanden.
- Stage 426 (Fakten-Dock): 4 Tests bestanden.
- Stage 440 (Bildschirmfarben): 10 Tests bestanden.
- Stage 441 (dBASE-Compiler): 19 Tests bestanden.
- `python -m py_compile`: erfolgreich.

**Grenze:** In der Build-Umgebung ist PyQt5 nicht installiert; daher keine
visuelle Windows-Qt-Sichtprüfung und kein echter GUI-Starttest.
