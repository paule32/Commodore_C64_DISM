# Stage 134 – OnClick-Callback und sichtbare WFM-Console

Die internen PE32- und PE32+-Relocationstests bestätigen, dass
`__dbase_wfm_proc_<Event>` als korrekte Callback-Adresse in das gelinkte
Executable-Image eingetragen wird.

Die sichtbare Console war bisher nicht garantiert: `AllocConsole()` wurde nur
verwendet, wenn Windows keine Console-Zuordnung meldete. Eine GUI-EXE kann aber
an einer geerbten oder unsichtbaren Console/ConPTY hängen.

Stage 134 erzeugt beim ersten `?`/`??` einer WFM-GUI eine eigene Console:

- `FreeConsole()` trennt nur den WFM-Prozess von einer geerbten Console.
- `AllocConsole()` erzeugt anschließend die eigene WFM-Console.
- `ShowWindow()` macht sie sichtbar.
- Die Position bleibt im freien Workstation-Bereich.
- Die Ausgabe wird über `CONOUT$` geöffnet und mit `WriteConsoleW()` geschrieben.

Zusätzlich verwendet der Win32-WFM-Callback explizit `__cdecl`.
`QPushButton::clicked(bool)` wird mit einer bool-Lambda verbunden und das
Ergebnis von `QObject::connect()` wird geprüft.

Der Event-Maschinencode bleibt weiterhin in `.text`; WFM-Quelltext wird nicht
in die EXE eingebettet.
