# Stage 529 – Debug nur noch über die Windows-TreeList

Basis: `d64_dism_stage528.zip`.

## Änderung

- Den Top-Level-Tab `Debug` im Projekt-Einstellungen-`QTabWidget` entfernt.
- Haupt-Tabs sind wieder ausschließlich `Windows`, `AMIGA` und `C= 64`.
- Debug ist weiter über die **linke TreeList** in `Windows → 32-Bit → Debug` und `Windows → 64-Bit → Debug` erreichbar.
- Beide TreeList-Debug-Blätter bleiben synchron; beim Laden werden `.pro`-Werte ohne Änderungsmarkierung übernommen. Beim Bearbeiten wird wie bisher die Projektänderung markiert.
- `.pro`-Persistenz (`[Settings.Debug]`) und CES-Code im PE32-D64I-MSZIP-Loader wurden nicht verändert.
- Keine echte DWARF-Sektionserzeugung in dieser Stage.

## Tests

- `python test_stage527.py`: 3 Tests.
- `python test_stage528.py`: 2 aktualisierte TreeList-/Synchronisationstests.
- `python test_stage529.py`: 2 Tests für Entfernung des Top-Tabs und TreeList-Anbindung.
- GUI-Laufzeit und Windows-PE32-Laufzeit sind hier nicht nativ geprüft.
