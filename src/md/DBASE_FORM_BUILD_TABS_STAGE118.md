Stage 118 - dBase Form Designer Build Tabs

- Designer-Dock: QTabWidget mit Formular-Designer und Quellcode.
- Build-Leiste ueber dem TabWidget: Compile, Windows PE32/PE32+, Assemble, Start.
- Quellcode wird aus dem aktuellen Designerzustand als WFM/OOP erzeugt.
- Compile erzeugt nur ASM; danach werden Assemble und Start sichtbar.
- Assemble benutzt den vorhandenen internen COFF32/COFF64-Linker.
- Start startet ausschliesslich die bereits erzeugte EXE.
- d64qt5.dll wird vor Start aus bekannten Runtime-Verzeichnissen neben die EXE kopiert, falls erforderlich.
- d64qt5-Runtime erweitert um DBaseQtWidgetSetProperty und weitere Designer-Controltypen.
- Runtime-Quellen liegen weiterhin ausschliesslich unter d64qt5/.

Hinweis: In dieser Umgebung ist kein nativer PyQt5/MinGW-Qt5-Laufzeittest moeglich. Die aktualisierte d64qt5.dll muss aus den mitgelieferten Quellen neu gebaut werden, damit der neue Export DBaseQtWidgetSetProperty vorhanden ist.
