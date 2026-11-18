# Stage 612 – dBASE Include-Kontext, Klassen und SET PROCEDURE

Basis: Stage 611.

## Präprozessor

- `#include "System.Objects.prg"` oder `#include "System.Objects"` mit `.prg`-Fallback.
- `SET PROCEDURE "System.Objects.prg" EXCLUSIVE` und `SET PROCEDURE "System.Objects" ADDITIVE` importieren dBASE-Quelltext zur **Compilezeit**. Sie erzeugen keinen Assembler-Dateizugriff.
- Beide Direktiven suchen relativ zur Quelldatei und in den in den Projekt-Einstellungen unter Compiler → dBASE → Eingabe-Verzeichnis konfigurierten Suchpfaden. Die vorhandenen Ausgabe-Verzeichnisse bleiben unverändert.
- Ein Python-Stack verfolgt verschachtelte Include-Dateien und Ursprungszeilen für Fehlermeldungen.
- `#ifndef`/`#define`/`#endif` unterstützen Include-Guards auch bei rekursiven Imports; ungeschützte Zyklen werden gemeldet.
- EXCLUSIVE: unter Windows `CreateFileW(GENERIC_READ, dwShareMode=0)`; die Datei ist nur für den Compiler lesbar und andere neue Handles mit Sharing-Konflikt werden blockiert. Das Dateiattribut wird nicht verändert.
- ADDITIVE: unter Windows `CreateFileW(GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE)`; andere Programme können kompatible Lese-/Schreibhandles öffnen. Das garantiert nicht, dass eine bestehende fremde Sperre umgangen werden kann.
- Die geöffneten Handles werden für die Dauer des Präprozessor-Durchlaufs gehalten und auch bei Fehlern geschlossen. Der gelesene Inhalt ist ein konsistenter Quelltext-Snapshot innerhalb dieses Compilerlaufs.
- Unter Linux/macOS kann die Windows-Sharing-Semantik nicht emuliert werden; dort erfolgt ein normaler schreibgeschützter Datei-Open.

## Klassen

Der Stage-612-Stand erweitert den nativen dBASE-Klassenpfad für abgeleitete Klassen einschließlich `CLASS Exception OF TObject`, Properties mit `PUBLIC`/`PRIVATE`, Konstruktoraufruf via `super().__ini__(self)` und `new Exception("...")`. Die semantischen Grenzen sind in den zugehörigen Tests dokumentiert.

## Tests

`python -m unittest -q test_stage612 test_stage612_procedure` – 20 Tests erfolgreich, 1 Windows-spezifischer Test auf Nicht-Windows übersprungen.

`python -m unittest -q test_stage605 test_stage609 test_stage610 test_stage611` – 33 Regressionstests erfolgreich.

Native Windows-Share- und DLL-Laufzeitprüfung steht aus.
