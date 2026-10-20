# Stage 394 — C64-Neuprogramme, Umbenennen und Hex-Fokus

**Verbindliche Ausgangsbasis:** `d64_dism_asm_393.zip`

## 1. Hex-Viewer

Bei erfolgreicher Assemblierung werden weiterhin die realen Ausgabebytes in den
Hex-Puffer geladen. `show_assembled_hex_bytes()` erzwingt jedoch keinen Wechsel
zum Hex-Tab mehr. Der aktive Assembler-/BASIC-Editor und dessen Eingabefokus
bleiben unverändert, solange der Benutzer nicht selbst den Tab auswählt.

## 2. Datei → Neu → C= 64 m68k

- **BASIC - Programm:** In-Memory-Vorlage mit Zeilennummern. Neues, ungespeichertes
  Blatt unmittelbar unter **BASIC - Programme**.
- **Assembler Programm:** In-Memory-Vorlage für MOS6510 mit `.org`, `.entry`,
  `start:`/`rts`. Neues, ungespeichertes Blatt unter
  **Assembler-Programme → Commodore C= 64**.
- Das neue Blatt und sein Dokument besitzen ein explizites **Neu-Flag**
  (`Qt.UserRole + 307` und `_is_new_c64_project_file`). `document.path` ist
  bis zum ersten erfolgreichen Speichern `None`. Die Vorlagen werden nicht
  heimlich im Projektverzeichnis angelegt.
- Erstes `Strg+S` oder `Speichern` → **Speichern unter** mit Datei- und
  Verzeichniswahl sowie typenabhängigen Dateiendungen. Bestehende Dateien
  dürfen durch den Erst-Speichervorgang nicht überschrieben werden.
- Nach erfolgreichem Schreiben werden Blattname und Pfad aktualisiert,
  das Neu-Flag entfernt und der Eintrag in der bestehenden Projekt-INI
  gespeichert. Ein fehlgeschlagener/abgebrochener Speichervorgang ändert
  weder Flag noch Dateipfad.
- Beim Schließen einer noch ungespeicherten Vorlage wird auch bei ansonsten
  unverändertem Template Speichern/Verwerfen/Abbrechen angeboten. Ein
  verworfenes Dokument entfernt das noch nicht persistierte Blatt.

## 3. Projekt-Informationen → Umbenennen

Kontextmenü **Umbenennen** für Quelltextblätter unter BASIC (einschließlich
Commodore C= 64) und Assembler-Programme (einschließlich C64-Zweig).

Der vorhandene Stage-338-Umbenennen-Dialog wird wiederverwendet, in **Dark
Mode und Light Mode**. Geprüft werden der vorgeschlagene Dateiname, die
Erweiterung, Dateiexistenz inkl. case-insensitiver Namenskollisionen,
Schreibberechtigung und tatsächliche Dateisystemumbenennung. Bei Konflikten
erscheint ein Fehlerdialog; die Quell- und Zieldatei sowie das Blatt werden
nicht verändert. Bei Erfolg werden der Pfad aller Projektverweise und die
geöffnete Editor-Registerkarte aktualisiert; die Projekt-INI wird gespeichert.

## 4. Prüfungen

- `python -m py_compile d64_dism.py` — bestanden.
- `python -m unittest -v test_stage393_hex_refresh.py test_stage394_c64_new_rename.py`
  — 15 Tests bestanden (isoliert, ohne PyQt5).
- ZIP-Integritätsprüfung — durchgeführt.
- Vollständiger interaktiver Windows-/PyQt5-Test weiterhin notwendig.
