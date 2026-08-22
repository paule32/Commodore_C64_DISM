Stage 158 – Formdesigner Timer / Source-Outline / ASM / Datenbank-Komponenten

Timer
-----
- feste Designergröße: 42 x 42 Pixel
- Rahmen und alle acht Resize-Knubbel bleiben sichtbar
- Resize-Vorschau und Endgröße bleiben immer exakt 42 x 42
- sichtbare Eigenschaften ausschließlich: Name, Interval, Active / Enabled
- Interval: Default 1000 ms, Minimum 10 ms, Maximum 2147483647 ms
  (QTimer/QSpinBox signed-int Maximum; ca. 24,86 Tage)
- Event: ausschließlich OnTimer
- historische OnInterval-Einträge werden beim Laden UND nach manueller Source-Bearbeitung nach OnTimer migriert
- Doppelklick auf Timer erzeugt/navigiert direkt zum OnTimer-Handler
- Timer1 erzeugt bei fehlendem Handler:

    procedure OnTimer1
        return

- einfacher Klick selektiert nur: Eigenschaften/Ereignisse wechseln und Resize-Rahmen/Knubbel anzeigen

Quellcode-Ansicht
-----------------
Links neben dem editierbaren WFM-Quellcode befindet sich eine TreeList:
- Prozeduren
- Funktionen
- Globale Variablen

Unter Prozeduren/Funktionen stehen die gefundenen Namen. Ein Klick navigiert
direkt zur Quellzeile. Die Liste aktualisiert sich bei Source-Änderungen.

Die normale DocumentEditor Compile/Assemble-Leiste oberhalb des Source-Editors
bleibt verborgen.

Assembler-Tab
-------------
Nach erfolgreichem Compile wird der vorhandene editierbare ASM-Editor als Tab
"Assembler" unmittelbar links vor "Quellcode" eingebettet. Seine interne
DocumentEditor-Buildleiste bleibt ebenfalls verborgen.

F2 im ASM-Editor verwendet den aktuell sichtbaren/bearbeiteten Assemblercode
und ruft assemble_dbase_form() auf: interner Assembler + Linker, kein
automatischer Start.

Die Formdesigner-Leiste oberhalb des TabWidgets bleibt sichtbar und funktional:

    Compile | Windows PE32 / Windows PE32+ | Assemble | Start

Datenbank-Palette
-----------------
Neuer Tab "Datenbank" im linken Icon-Bereich:
- Session
- Database
- Query
- DataSource

Alle vier sind nicht-visuelle Designer-Komponenten mit exakt 42 x 42 Pixel.
Im Runtime-Code werden sie zunächst als QObject-basierte nicht-visuelle Handles
erzeugt. Eine Datenbank-Engine für Query/DataSource wird in dieser Stufe nicht
erfunden. Der neue Runtime-Import wird nur erzeugt, wenn eine dieser vier
Komponenten tatsächlich im WFM vorkommt.

Löschen
-------
Entf/Del löscht selektierte Controls über denselben zentralen Designer-Pfad.
Dabei werden die zugehörigen Eventmethoden aus scene.wfm_methods entfernt und
der WFM-Quelltext neu serialisiert. Dadurch verschwinden sowohl die
Komponenten-Deklaration/Properties als auch ihre Event-Prozeduren aus dem
Quelltext. Bei Panels werden Child-Eventmethoden mit berücksichtigt.

Qt-Runtime
----------
Unter d64qt5/ sind die Buildquellen vollständig zusammengehalten:
- d64qt5_bridge.cpp
- d64qt5_bridge.h
- d64qt5_bridge.def
- d64qt5_bridge.pro
- d64_workstation.cpp
- d64_workstation.h

Runtime-Änderungen:
- QTimer::timeout bindet OnTimer; OnInterval bleibt nur Legacy-Alias
- Timer-Intervall wird in Millisekunden behandelt; Minimum 10 ms
- Timer-Default 1000 ms
- neuer Export DBaseQtNonVisualCreate

Die d64qt5.dll muss für Timer-OnTimer und die neuen Datenbank-Komponenten neu
gebaut werden. Es wurde hier keine DLL erzeugt.

Tests
-----
Python py_compile: OK
Strukturelle Stage-158-Prüfungen: alle OK
Native Windows/PyQt5/Qt5-GUI-Laufzeitprüfung: in dieser Umgebung nicht verfügbar.
