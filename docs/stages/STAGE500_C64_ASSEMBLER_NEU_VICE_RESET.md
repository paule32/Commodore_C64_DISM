[Deutsch](STAGE500_C64_ASSEMBLER_NEU_VICE_RESET.md) | [English](STAGE500_C64_ASSEMBLER_NEU_VICE_RESET.en.md)

# Stage 500 – Neues C64-Assembler-Programm und VICE-Reset

**Verbindliche Grundlage:** hochgeladenes `d64_dism_asm_499(1).zip` (Stage 499).

## Projektbaum – neuer Menüpunkt

`Projekt-Informationen -> Projekt -> Assembler-Programme -> Commodore C= 64`:

1. **Neu: Assembler-Programm** (neu, **erster** Eintrag)
2. C64-Quellprogramm hinzufügen … (bestehend)
3. Knoten öffnen / Knoten schließen (bestehend)

Der erste Eintrag ruft die bestehende Funktion
`_new_unsaved_c64_source_document("assembler", use_template=True, under_c64_target=True)`
auf. Der Editor wird sofort geöffnet und der ASM-Startquelltext angezeigt. Das neue Blatt
erscheint unter dem richtigen Projektknoten, trägt zunächst `Unbenannt_<Nummer>.asm`,
hat aber **keinen physischen Pfad** (`document.path=None`). Marker: `document._is_new_c64_project_file=True`
und `Qt.UserRole+307=True` am Blatt. Die Marker verhindern frühzeitiges Überschreiben und
phantomhafte dauerhafte Projektverweise.

**Erstmaliges Speichern (Speichern / Strg+S):**
`save_current_document() -> _save_document(save_as=False) -> _choose_document_filename()`
öffnet den Datei-Speichern-Dialog mit Assemblerfilter und Standardendung `.asm`.
Der Benutzer kann Zielverzeichnis und Namen wählen; fehlt die Erweiterung, wird `.asm`
angehängt. Für neue ASM-Dateien sind `.asm`, `.s` und `.a65` erlaubt. Bereits vorhandene
Dateien werden nicht überschrieben. Nach erfolgreichem Speichern werden der Dateipfad
im Projektbaum und im Editor gesetzt, das Neu-Flag gelöscht und die Projektdatei
aktualisiert. Abbrechen erhält den ungespeicherten Zustand.

## Kontextmenü des C64-Assembler-Quelltexteditors

Der vorhandene VICE-Block wird beibehalten und um ein **echtes C64-Reset** ergänzt:

- **Ausführen** (Assemblerprogramm nach VICE laden und starten)
- Zeile in VICE ausführen
- Auswahl in VICE ausführen
- Programm an VICE übertragen
- Programm übertragen + START
- **VICE zurücksetzen** (neu: VICE Binary Monitor `0xCC`, Soft-Reset `0x00`, anschließend `EXIT`)
- VICE Monitor fortsetzen (bestehende Aktion, `0xAA`, weiterhin separat)

Anschließend bleiben **alle Qt-Standardaktionen** erhalten, u. a. Rückgängig,
Wiederherstellen, Ausschneiden, Kopieren, Einfügen, Löschen, Alles markieren.
Auch der Operand-Rechner bleibt vorhanden. Das VICE-Menü wird weiterhin nur
für C64-Assembler und den BASIC-Editor angezeigt.

Der Reset verwendet einen Hintergrund-Thread (wie der bestehende VICE-Debugpfad),
benötigt **keine Kompilierung und keinen Dateispeicherdialog** und startet bei Bedarf
VICE mit aktivem Binary Monitor. Er beendet VICE nicht; der Befehl `0xBB` (Quit)
wird ausdrücklich nicht verwendet. Der zusätzliche `VICE Monitor fortsetzen`-Eintrag
bleibt verfügbar, wenn ausdrücklich nur die CPU fortgesetzt werden soll.

## Änderungen

- `d64_dism.py` – Kontextmenü der C64-Projektzielknoten, VICE-Befehlszuordnung,
  `ViceBinaryMonitorClient.reset_system()`, Reset-Behandlung in der Worker-Route.
- `test_stage500_c64_assembler_new_vice.py` – sieben neue GUI-freie Tests für
  Menüposition, ungespeicherte ASM-Datei, Save-Dialog, Speichern/Marker,
  Reset-Paket und Worker-Routing sowie Editor-Menü.
- `test_stage399_c64_basic_context.py` – die Erwartung an die bisher unveränderte
  Assembler-Menüposition an die neue Anforderung angepasst. BASIC-Verhalten nicht verändert.

## Prüfstand

- `python -m py_compile d64_dism.py`: ohne Syntaxfehler.
- Stage-500-Tests: 7 Tests mit `OK` gemeldet.
- Stage-394-/399-Regressionstests: 11 Tests mit `OK` gemeldet.
- Hinweis zur Umgebung: Die Testprozesse gaben ihre OK-Meldung aus, blieben jedoch
  beim Python-Shutdown hängen; deshalb kein vollständig normal beendeter Lauf.
- Keine interaktive Windows-/PyQt5-/VICE-Prüfung verfügbar; die VICE-Protokollaktion
  wurde mit Mock-Client geprüft, nicht am echten Emulator.
