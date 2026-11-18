# Stage 627 – C++20-Warnungen in der Qt5-Bridge behoben

Verbindliche Basis: `d64_dism_stage626.zip`.

## Änderungen

* `d64qt5/d64qt5_bridge.cpp`: Die sechs Tastenkürzel für „Rückgängig“, „Wiederherstellen“, „Ausschneiden“, „Kopieren“, „Einfügen“ und „Alles auswählen“ verwenden nun `QKeySequence(static_cast<int>(Qt::CTRL) | static_cast<int>(Qt::Key_X))` (jeweils mit dem zugehörigen Buchstaben) statt der unter C++20 veralteten Addition unterschiedlicher Enum-Typen.
* `install_debug_tab(bool)` bleibt aus Kompatibilitätsgründen vorhanden, erhält aber das C++17/20-Attribut `[[maybe_unused]]`, da aktuell kein Aufruf erfolgt. Die eigentliche DEBUG-Funktionalität wird nicht verändert.
* Das Kürzel `Delete` und alle Menü-Einträge, Signalverbindungen und Editorfunktionen bleiben unverändert.

## Bauen und installieren

Unter Windows, im Projektverzeichnis:

```bat
build_and_deploy_dbase_editor_stage627.bat
```

Das Skript verwendet die bestehende `d64qt5\build_d64qt5_mingw32.bat`, erwartet die Qt5-/MinGW32-Toolchain und kopiert `libd64_qt5.dll` in `runtime\dbase\pe32` (oder in den als erstes Argument übergebenen Zielordner). Vor dem DLL-Austausch alle verwendenden Prozesse beenden.

**Hinweis:** Die vom Benutzer gemeldeten sieben Zeilen sind Warnungen, keine Fehler; sofern der Linker keine weiteren Fehler meldet, wird die DLL auch ohne diese Änderung erzeugt. Stage 627 entfernt die Warnungsursachen, ohne die Runtime-ABI zu verändern.

## Tests

`python -m unittest -q tests/test_stage627_cpp20_warnings.py`

Ein nativer Qt5-/MinGW32-Build ist in dieser Linux-Umgebung nicht möglich; den finalen Windows-Build bitte dort durchführen.
