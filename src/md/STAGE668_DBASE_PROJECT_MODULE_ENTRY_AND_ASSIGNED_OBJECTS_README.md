# Stage 668 – dBASE-Modul als PE-Einstieg; Programme als reine COFF-Objekte

**Verbindliche Basis:** `d64_dism_stage667.zip`.

## Warum der alte Linkversuch fehlgeschlagen ist

Stage 667 verlangte unter `dBASE Programme -> Programme` genau **ein** Hauptprogramm mit `_start`. Dieses Projektmodell ist nun ersetzt:

- `dBASE Programme -> Module`: Das aktuell gewählte und assemblierte Blatt ist der **Link-Eigentümer**. Für EXE liefert es `_start`; für die dBASE-Klassen-DLL `__d64_dll_entry`.
- `dBASE Programme -> Programme`: Die dortigen `.prg`-Blätter erzeugen ausschließlich COFF32-/COFF64-**Objekte**. Der generierte EXE-Startcode, `_start` und der DLL-Lader-Einstieg `__d64_dll_entry` werden entfernt. Die Module werden beim Linken **nicht** umbenannt, weil sie den gültigen PE-Einstieg besitzen.
- Das Modul kann **allein** zu einer EXE/DLL gelinkt werden; es ist kein Programme-Blatt mehr erforderlich.

### EXE: `Programm: App001`

1. In den Projekt-Einstellungen die dBASE-EXE `App001` wählen (`Programm: App001`).
2. Unter `dBASE Programme -> Module -> App001.prg` die Quelle kompilieren und im erzeugten ASM-Tab **Assemble** ausführen.
3. Die benötigten Programme-Quellen unter `dBASE Programme -> Programme` zu `dBASE: Programm — App001` zuweisen und je Blatt **Compile → Assemble** ausführen (nur `.o`). Dieser Schritt ist optional, falls keine zusätzlichen Objekte gebraucht werden.
4. Beim Modul **Link** drücken. Der Linker verwendet ausschließlich die aktuell zugewiesenen Programme-Objekte plus das Modulobjekt und schreibt `App001.exe` in den eingestellten Ausgabepfad.
5. Nur bei erfolgreichem EXE-Link erscheint **Start**. Veraltete, fehlende oder falsch architekturierte `.o`-Dateien stoppen den Link.

### DLL: `Bibliothek: MyLib`

1. In den Projekt-Einstellungen die dBASE-DLL `MyLib` wählen (`Bibliothek: MyLib`), Name aus dem Feld `dBASE DLL:`.
2. Das ausgewählte Module-Blatt muss eine vom dBASE-DLL-Compiler unterstützte **Klassenbibliothek** enthalten; erneut kompilieren, damit `__d64_dll_entry` erzeugt wird.
3. Programme-Blätter für diese DLL mit `dBASE: Runtime — MyLib` zuweisen und jeweils als reine `.o` assemblieren.
4. Im ausgewählten Modul auf **Link** drücken; Ergebnis `MyLib.dll`. Ein DLL-Ergebnis zeigt **keinen** Start-Button.

Der bereits vorhandene dBASE-Klassen-DLL-Compiler unterstützt weiterhin nur seine dokumentierte Klassen-/Exportsyntax; beliebige Top-Level-EXE-Anweisungen sind kein gültiger DLL-Einstieg.

## Projekt-ComboBox: Sammel- und Einzelzuweisung

Wenn die ComboBox in der Zeile **`dBASE Programme -> Programme`** umgestellt wird, erhalten **alle vorhandenen Kinder** dieselbe Zuweisung. Die ComboBox jedes einzelnen Blattes bleibt aktiv und kann **anschließend separat** übersteuert werden. Die Zuweisungen werden wie bisher in der `.pro`-Datei gesichert. Für die Link-Auswahl zählt die effektive Blattzuweisung, nicht die bloße Existenz der Datei im Baum.

## Was sich technisch ändert

- `d64dbase/compiler.py`: EXE-Start-/Shutdown-Code erhält eindeutige Marker. So kann der Programme-Kompilierpfad den kompletten generierten Startcode entfernen, **ohne** nachfolgende Klassen-/Routinenabschnitte wegzuschneiden.
- `dbase_module_coff.py`: Startup-Entfernung, DLL-Einstieg-Entfernung, stabile COFF-Symbolnamensräume für beigelinkte Programme, Vermeidung doppelter `TObject`-Runtime-Exporte, beliebig viele Programme-Objekte (auch null).
- `d64_dism.py`: Objekt-Assembler für Programme, Modul-Assembler ohne Einstieg-Namespace, ziel- und zuweisungsabhängiger EXE-/DLL-Link, COFF-Machine- und Entry-Prüfung, bulk-Zuweisung und Startfreigabe nach EXE-Link.
- `test_stage668.py`: echte PE32-/PE32+-Tests mit dBASE-Frontend, COFF-Writer und PE-Linker, DLL-Tests mit mehreren Objekten, GUI-Link-Handler und Zuweisungskontrolle.

**Beachten:** Top-Level-EXE-Anweisungen in einer *Programme*-Quelldatei werden bewusst **nicht** als zweiter Programmeinstieg ausgeführt. Sie werden zusammen mit dem EXE-Startup entfernt. Für wiederverwendbaren Code in einer reinen COFF-Datei müssen deshalb geeignete Klassen/Routinen vorhanden sein. Eine spätere automatische Initialisierung solcher Einheiten oder modulübergreifende dBASE-Aufruf-ABI ist nicht Bestandteil dieser Stufe.

**Die neu erzeugten Programme-Objekte müssen einmal neu kompiliert und assembliert werden.** Alte Stage-667-Programme-Objekte mit `_start` werden vom neuen Link-Handler ausdrücklich zurückgewiesen; sie können sonst Kollisionen erzeugen.

## Prüfungen

- Echte dBASE-Compiler/COFF-Linktests: EXE-Modul, 0/2 zusätzliche Programme, PE32 und PE32+.
- Echte dBASE-`TObject`-DLL: Modul + Programme-Klassenobjekt, PE32 und PE32+.
- GUI-Link-Handler: EXE/DLL aus aktivem Projektnamen, Filter für passende Programme-Blätter, Start-Status, Programme-Assemble ohne Link.
- Projektbaum: Gruppen-ComboBox propagiert; eine anschließende individuelle Zuweisung bleibt möglich.
- Alte Hilfe- und Qt5-Bridge-Dateien bleiben unangetastet; ein nativer Windows-/PyQt5-GUI-Test bleibt erforderlich.

**Kein Neuaufbau von `libd64_qt5.dll` notwendig.**
