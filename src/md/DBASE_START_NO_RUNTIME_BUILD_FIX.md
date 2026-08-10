# dBase Start: kein automatischer Qt5-Runtime-Build

## Ursache

Im Stage-9-Stand rief `_launch_dbase_qt5_gui()` vor jedem Start
`ensure_dbase_qt5_runtime(...)` auf. Wenn `d64qt5.dll` im EXE-Verzeichnis
fehlte oder nicht zur Zielarchitektur passte, startete diese Funktion
`qmake` und danach `mingw32-make`/`nmake`.

Damit konnte ein Klick auf **Start** unbeabsichtigt einen Qt5-DLL-Build
auslösen.

## Neues Verhalten

Für dBase gilt nun:

- **F2**: Compile -> Assemble -> interner Linker -> EXE starten.
- **Start**: ausschließlich die bereits vorhandene `<Quellname>.exe` im
  aktuellen Arbeitsverzeichnis starten.
- Beim Start werden weder Compiler noch Assembler noch Linker erneut gestartet.
- Beim Start werden weder `qmake`, `mingw32-make`, `nmake` noch andere
  Runtime-Build-Werkzeuge gestartet.
- Auch der CLI-Linkpfad baut/deployt `d64qt5.dll` nicht mehr automatisch.

`_launch_dbase_qt5_gui()` ruft direkt:

```python
subprocess.Popen([str(output_path)], ...)
```

auf.

## d64qt5.dll

Die bereits manuell erzeugte `d64qt5.dll` wird nicht verändert oder neu gebaut.
Sie muss für den Windows-DLL-Loader erreichbar sein, am einfachsten direkt
neben der erzeugten EXE. Dasselbe gilt für die benötigten Qt5-Laufzeitdateien
(z.B. `Qt5Core.dll`, `Qt5Gui.dll`, `Qt5Widgets.dll` und
`platforms/qwindows.dll`), sofern sie nicht bereits über den Windows-Suchpfad
erreichbar sind.

Die Funktion `build_dbase_qt5_runtime_dll()` bleibt als explizite manuelle
Hilfsfunktion im Quellcode erhalten, besitzt aber keine automatische
Aufrufstelle mehr.

## Regression

Neue Tests prüfen insbesondere:

1. Start verwendet die EXE aus `self.current_directory`.
2. Start ruft keinen Buildpfad auf.
3. `_launch_dbase_qt5_gui()` ruft direkt `subprocess.Popen()` auf.
4. Der Runtime-Ensure-Helper baut nichts mehr.
5. Der CLI-Linkpfad baut keine Qt5-Runtime automatisch.
6. F2 führt weiterhin Compile/Assemble/Link aus und startet danach die EXE.
