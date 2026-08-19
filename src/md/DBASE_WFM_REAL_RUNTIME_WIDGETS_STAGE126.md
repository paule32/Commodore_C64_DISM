# Stage 126 – WFM als echte Workstation-GUI

## Hauptfenster
`DBaseQtFormOpen()` behandelt die WFM-Form jetzt als sichtbares Hauptfenster
der Anwendung. Nach `show()` wird das native HWND mit
`D64WorkstationActivate()` an die vorhandene Workstation gebunden.
Das interne Console-Hauptfenster bleibt für WFM verborgen.

Das DB-Icon der Workstation stellt bei einer WFM-Anwendung zuerst die
zuletzt erzeugte WFM-Form wieder her.

## Runtime-Controls
Die WFM-Runtime erzeugt weiterhin echte Qt-Widgets:
- PUSHBUTTON -> QPushButton
- ENTRYFIELD / LINEEDIT / EDITFIELD / EDIT -> QLineEdit
- CHECKBOX -> QCheckBox
- RADIOBUTTON -> QRadioButton
- COMBOBOX -> QComboBox
- LABEL -> QLabel
- CONTAINER/PANEL -> QFrame
- TABLEGRID -> QTableWidget
- Scrollbars, Statusbar, Toolbar und Menu ebenfalls als echte Qt-Widgets.

`QGraphicsProxyWidget` existiert ausschließlich im Formular-Designer.
Es wird nicht in die kompilierte WFM-Anwendung übernommen.

## Designer
`EntryField` wurde in die Komponentenpalette aufgenommen und wird beim
Speichern als `ENTRYFIELD` geschrieben.
