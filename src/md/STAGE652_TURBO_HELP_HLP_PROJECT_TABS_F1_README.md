# Stage 652 – Turbo Help als `.hlp`, Projekt-THLP-Tabs und F1 im DEBUG-Viewport

**Verbindliche Basis:** `d64_dism_stage651.zip`.

## Zuständigkeiten

- **dBase2Many (`d64_dism.py`, `turbo_help_gui.py`, `turbo_help_compiler.py`)**: `Werkzeuge → Hilfecompiler`, `.thlp`-Editor, rote X-Schaltflächen, Quellenverwaltung im Projektbaum, F2, `.po`/GNU-Binärkompilierung, Installation der HLP im Ausgabeverzeichnis.
- **Qt5-Bridge (`d64qt5/d64qt5_bridge.cpp`, `d64_turbo_help_window.hpp`)**: nur das bereits in der DLL implementierte cyanfarbene Hilfe-Fenster im DEBUG-Viewport; Öffnen von `App.hlp`, Themenwechsel, Mausaktionen, globaler F1-Shortcut.
- **Kein Compiler in der Qt5-Bridge.** Der Name `.hlp` bezeichnet hier einen *GNU-MO-formatigen* Hilfekatalog, **keine klassische Microsoft-WinHelp-Datei**.

## Dateinamen

```text
Projekt/Quellen/
  System.Help.thlp                 (bearbeitbarer Haupttext)
  navigation.thlp                  (weitere, separate Textquelle)
  System.Help.po                   (gettext-Zwischenformat)
  System.Help.hlp                  (optionaler F2-Vorschaukatalog)

<dBASE-Ausgabe-Verzeichnisse / EXE-DLL>/
  App.exe
  App.hlp                          (tatsächlich gelinkter Hilfekatalog)
  libd64_qt5.dll                   (Turbo-Vision-Hilfefenster)
```

Der Zielpfad wird **aus dem für die EXE wirklich verwendeten Output-Pfad** abgeleitet (einschließlich `Projekt-Einstellungen → dBASE → Ausgabe Verzeichnisse → Exe / dll`). Dadurch stimmen `App.exe` und `App.hlp` unabhängig vom aktuellen Arbeitsverzeichnis überein.

Beim Linken werden **alle im Projekt unter `Turbo Help` registrierten `.thlp`-Dateien** in einem gemeinsamen Topic-Katalog kompiliert, selbst wenn F2 noch nicht benutzt wurde. Die Ausgabe wird atomar als `<EXE-Stamm>.hlp` geschrieben. Ein fehlerhafter Hilfekatalog führt zu einer Warnmeldung im IDE-Protokoll; die bereits gelinkte EXE bleibt bestehen, ein vorhandener früherer HLP-Katalog bleibt erhalten.

## Projekt-Informationen

Neuer, eigenständiger **Turbo Help**-Knoten im Projektbaum. Rechtsklick auf Knoten/Blatt:

- **Neu:  Inhalt** – neuer `.thlp`-Tab und vorläufiges Blatt `Unbenannt.thlp`.
- **Hinzufügen** – Dateiauswahl für eine oder mehrere vorhandene `.thlp`-Dateien; Blatt anlegen, im geöffneten Editor eigene Tabs.
- **Entfernen** – nur bei Blatt: falls geöffnet, ungespeicherte Änderungen zuerst speichern; das Blatt aus dem Projekt nehmen, **nicht** die Datei löschen.

Persistenz erfolgt im bestehenden `.pro`-INI-Format im Abschnitt `[Category.TurboHelp]`. Nur gesicherte Dateipfade werden gespeichert; `Unbenannt.thlp` ohne Dateipfad bleibt bewusst temporär. Ältere Projektdateien ohne Abschnitt sind weiterhin ladbar.

## Editor

Unter den Werkzeug-Buttons befindet sich das `QTabWidget`. Die Reiter tragen die `.thlp`-Dateinamen und ein **rotes `×`** rechts. Geänderte Dateien werden **vor** dem Schließen gespeichert, und ein neues, ungespeichertes Dokument öffnet den Dateispeichern-Dialog. Abbruch des Dialogs verhindert das Schließen des Tabs. Bereits geöffnete Dateien werden nicht ein zweites Mal geöffnet.

**F2** speichert alle Änderungen und kompiliert die Projekt-Quellen nach gettext-`.po` und einer binären `.hlp`-Datei. `%include`, `%topic`, `%ref`, `%link`, `%anchor` und `<b>` funktionieren unverändert. Mehrere registrierte Dateien werden als gemeinsamer Katalog behandelt; mehrfach definierte Themen sind Fehler. Für die Anzeige ist `%topic "index"` verpflichtend.

## Native Qt5-Bridge

`DBaseQtHelpShowMo(nullptr)` bleibt aus ABI-Kompatibilitätsgründen der bestehende Exportname, lädt jetzt aber automatisch **`<laufendes-EXE-Stamm>.hlp`**, mithilfe von `QCoreApplication::applicationFilePath()`; keine `.mo`-Dateisuche, keine Abhängigkeit vom aktuellen Verzeichnis.

- **F1** löst in der nativen Qt5-Laufzeit den Hilfeaufruf global aus (`Qt::ApplicationShortcut`).
- **Hilfe → Inhalt** ruft denselben Viewer auf.
- Viewer im **DEBUG-Viewport**, cyan mit hellerer Titelleiste, Schließen links oben, Verschieben per Titelbalken, Doppelklick maximiert/stellt wieder her.
- **Resize-Griff rechts unten** (`Qt::SizeFDiagCursor`); nur das Hilfe-Fenster wird verändert, nicht das übergeordnete DEBUG-Window. Der Griff ist im maximierten Zustand ausgeblendet.
- **Blaue unterstrichene Links** und interne Anker, beim Navigieren wird der bisherige Thema-Text ersetzt.
- **Hilfe → Über ...** behält seinen zentrierten Text ohne Kontextmenü.

### Warum existiert `turbo_help_host.exe` für die IDE-Vorschau noch?

Das **fertige Windows-Programm benötigt keinen separaten Hilfehost**. Der Viewer ist in `libd64_qt5.dll` enthalten und wird über F1 / Menü aufgerufen. Nur die F2-Vorschau der IDE verwendet weiterhin einen kleinen nativen Host-Prozess, weil ein Python-64-Bit-Prozess eine mit MinGW32 erstellte Qt5-DLL nicht laden kann. Der Host enthält weder Compiler noch Fensterimplementation, sondern lädt die DLL. Auf die ausgelieferte `App.exe`/`App.hlp` trifft diese Einschränkung nicht zu.

## Build

```bat
build_and_deploy_dbase_editor_stage652.bat
```

Das Skript verwendet die vorhandene MinGW32/Qt5-Toolchain, erzeugt `libd64_qt5.dll` und für die IDE-Vorschau weiterhin `turbo_help_host.exe`. Für die gebaute EXE wird ausschließlich `libd64_qt5.dll` gebraucht (neben den bisherigen Qt-Runtime-Abhängigkeiten).

### Tests

- `pytest -q test_stage652.py test_stage650.py test_stage631.py test_stage634.py test_stage635.py test_stage636.py test_stage637.py`: **54 bestanden**.
- Binärer GNU-MO-Roundtrip nach `.hlp`, Lesen mit `gettext.GNUTranslations`, Dateiname `App.hlp`, atomarer Austausch, Mehrdatei-Topic-Kompilierung einschließlich `%include` wurden geprüft.
- `d64_dism.py` unter Python 3.13 syntaktisch geprüft **mit nur für den Test ersetzten Python-3.15-`lazy`-Importen**. Die Originaldatei bleibt unverändert und erfordert ihre bisherige Python-3.15-Umgebung.
- Nativer Qt5-/MinGW32-Build und visueller Windows-Laufzeittest **nicht** in dieser Umgebung möglich; die C++-Änderungen wurden quellenbasiert überprüft.
