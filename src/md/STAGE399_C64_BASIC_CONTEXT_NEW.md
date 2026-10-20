# Stage 399 – Neues BASIC Programm im C64-Projektkontextmenü

Verbindliche Ausgangsbasis: `d64_dism_asm_398.zip`.

## Bedienung

Im Dock **Projekt-Informationen** auf **BASIC - Programme → Commodore C= 64** rechtsklicken.
Der neue erste Kontextmenüeintrag lautet **Neues BASIC Programm**. Die folgenden
Einträge **C64 BASIC-Programm hinzufügen …** und **Knoten öffnen/schließen**
bleiben bestehen.

Die Aktion verwendet `_new_unsaved_c64_source_document('basic',
use_template=True, under_c64_target=True)`. Sie öffnet das C64-BASIC-Template
im Editor, legt das neue Blatt **direkt unter Commodore C= 64** an und setzt
das bereits vorhandene Flag `_is_new_c64_project_file`. Der Quelltext wird
noch nicht auf die Festplatte geschrieben. Erst `Speichern` fragt über den
bereits vorhandenen `Speichern unter`-Dialog nach Name und Zielverzeichnis.

Nach dem Speichern wird die Datei wie bisher über `Category.c64` in der
Projektdatei persistiert. `.bas`-/`.basic`-Dateien dieses Unterknotens erhalten
auch nach erneutem Laden den C64-Quelldateityp und können über den Projektbaum
geöffnet werden. Die bisherigen Aufrufe über Datei → Neu bleiben weiterhin
unverändert unter dem allgemeinen BASIC-Hauptknoten.

## Implementierung

Nur `d64_dism.py` ist gegenüber Stage 398 geändert. Hinzugefügt wurde
`test_stage399_c64_basic_context.py` (5 Tests). Die übrigen Dateien stammen
unverändert aus dem Basisarchiv.

## Prüfungen

- `python -m py_compile d64_dism.py`: bestanden.
- 5 Tests von Stage 399 und 6 Tests von Stage 394: bestanden.
- 46 Tests aus Stages 393, 395, 396, 397 und 398: bestanden.
- Interaktiver Windows-/PyQt5-UI-Lauf: nicht ausgeführt (PyQt5 nicht verfügbar).
