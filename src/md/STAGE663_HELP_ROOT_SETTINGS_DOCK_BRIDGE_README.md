# Stage 663 – Projekt-Einstellungen → Hilfe (eigenständiger Hauptknoten)

**Verbindliche Basis:** Stage 662. Die am 21.11.2026 präzisierte Struktur
setzt **Hilfe** als eigenständigen *letzten Hauptknoten* in die Windows-
Einstellungen (PE32 und PE64), **nicht** als Unterknoten von Debug.

```text
Windows → 32-Bit / 64-Bit
  Umgebung
  Compiler
  Assembler
  Linker
  Debug
  Hilfe
    Entwicklung
    Anwendung
```

## Einstellungen

Jedes Hilfe-Blatt enthält „Suchpfade:“ mit „relative Pfade“,
Verzeichniseingabe und Browser-Schaltfläche, Pfadliste sowie „Hinzufügen“,
„Löschen“ (Bestätigung), „Abbrechen“, „↑“ und „↓“. Darunter liegt
„Compressor“ mit „Microsoft CHM“, der auswählbaren `HH.EXE` und „internal“.
Der Standard-Dateidialog übernimmt Doppelklick (OK) und bietet Abbrechen.
Abbrechen setzt den Fokus zurück auf das Eingabefeld.

Die Werte werden im Projekt unter `[Settings.Windows.Hilfe]` als JSON
persistiert und für PE32 und PE64 gemeinsam verwaltet.

- **Entwicklung**: konfigurierte Suchverzeichnisse für den IDE-CHM-Viewer;
  bei der Erstauswahl wird dort nach `*.chm` gesucht.
- **Anwendung**: Verzeichnisse der Laufzeithilfe werden beim F2-Kompilieren
  und beim EXE-Build als `<EXE-Stamm>.help.json` neben der EXE abgelegt.
  `libd64_qt5.dll` versucht zuerst `<EXE-Stamm>.hlp` neben der EXE und
  danach dieselbe Datei in den konfigurierten Pfaden. Relative Pfade werden
  im Laufzeitprozess relativ zum **EXE-Verzeichnis** aufgelöst.

**CHM-Entpacker:** `Microsoft CHM` verwendet die gewählte `HH.EXE` mit
`-decompile`. Der interne Weg bevorzugt die optionale Python-Bibliothek
`pychm` (CHMLib-Bindings); falls diese nicht installiert/benutzbar ist,
verwendet er die vorhandene 7-Zip-Integration. Die Python-Standardbibliothek
enthält keinen eigenen CHM-Entpacker. Ohne beide Backends erscheint eine
Fehlermeldung. Die Dateiauswahl führt `HH.EXE` nicht aus.

## Dock-Wechsel

Ein Klick auf ein Projektblatt außerhalb „Turbo Help“ speichert zunächst
alle veränderten `.thlp`-Editoren und blendet den Hilfecompiler aus.
Bei abgebrochenem Speichern bleibt das Hilfecompiler-Dock geöffnet.
`Projekt-Informationen` und das vor dem Hilfecompiler aktive Fensterlayout
werden wiederhergestellt. Ein Klick auf ein weiteres Turbo-Help-Blatt
wechselt weiterhin im Hilfecompiler zu dessen Tab.

Die Titelleiste von **Projekt-Einstellungen** hat ca. 100 Pixel hinter der
Beschriftung eine Schaltfläche **schließen**, die das Dock ausblendet.

## Qt5-Bridge

`d64qt5/d64_turbo_help_window.hpp`:

- Dreipixel-Schatten mit Versatz 3 Pixel nach rechts und nach unten
- Titelleiste zeigt **`Hilfe:  <Hilfethema>`**, aktualisiert bei jedem Themenwechsel
- Rasterverschieben, Rastervergrößern, Scrollleisten und F1 bleiben erhalten
- Keine `turbo_help_host.exe`

Neu zu bauen ist `libd64_qt5.dll` mit
`build_and_deploy_dbase_editor_stage663.bat`.

## Überprüfung

- Python-Syntax von `turbo_help_settings.py` und die mit Python 3.15 `lazy`
  importierte `d64_dism.py` (für den hiesigen Parser testweise `lazy` entfernt)
- **86** gezielte/bestehende Tests bestanden, inklusive der Stage-663-Tests
- Archivintegrität (ZIP-CRC) geprüft

**Nicht geprüft:** nativer Windows-/PyQt5-/Qt5-Laufzeittest. Die Ausführung
von `HH.EXE` und der Python-CHM-Extraktion wurde mangels verfügbarer
Windows-/CHM-Testdateien und optionaler Bibliotheken nicht verifiziert.
