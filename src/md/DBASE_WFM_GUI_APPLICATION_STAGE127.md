# Stage 127 – WFM als echte GUI-Anwendung

## Zwei Programmtypen

- normale dBase-Programme: Console
- WFM/Formular-Programme: GUI

WFM wird beim internen COFF-Linken mit `entry_symbol="__d64_wfm_entry"`
und immer mit PE-GUI-Subsystem gelinkt. `_start` ist fuer WFM nicht mehr
der Programmeinstieg.

## GUI-Runtime

Neu: `DBaseQtInitializeGui()`.

Diese Initialisierung:
- verbindet/erzeugt weiterhin die Workstation,
- erzeugt QApplication und Workstation-Callbacks,
- erzeugt aber **kein** DBaseMainWindow/Console/DEBUG-Fenster.

Die mit `DBaseQtFormCreate()` erzeugte WFM-Form ist stattdessen ein echtes
`QMainWindow`.

## Komponenten

Neu: `DBaseQtControlCreateEx(type,parent,text)`.

Beispiel:

```dbase
THIS.PushButton1 = NEW PUSHBUTTON(THIS, "press me")
```

wird vom WFM-Assembler ueber `DBaseQtControlCreateEx` aufgebaut und entspricht
in der Runtime:

```cpp
QPushButton *push1 = new QPushButton("press me", mainwindow);
```

Panels werden als Parent-Handles weitergereicht, sodass verschachtelte Controls
auch zur Laufzeit echte Qt-Parent/Child-Beziehungen besitzen.

Danach werden Position/Dimensionen, Font, Brush, Border und weitere WFM-
Properties auf die realen QWidget-Instanzen angewendet.

Zusaetzlich werden `Visible`, `Enabled`, `ToolTip`, `PlaceholderText`,
`ReadOnly`, `Checked` und `CurrentIndex` als echte Widget-Eigenschaften
behandelt.

## DLL

`d64qt5.dll` muss neu gebaut werden, da zwei neue Exporte hinzukommen:

- DBaseQtInitializeGui
- DBaseQtControlCreateEx
