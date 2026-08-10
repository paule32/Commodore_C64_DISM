# d64qt5.dll – dBase Qt5 bridge

Die generierten dBase-Programme importieren eine kleine stabile C-ABI aus
`d64qt5.dll`. Die Bridge verwendet intern Qt5Core, Qt5Gui und Qt5Widgets.
Dadurch muss der Assembler keine C++-Namensmangling-Symbole aus
`Qt5Widgets.dll` direkt kennen.

## Build unter Windows mit Qt 5 / MinGW

In einer Qt-5-MinGW-Eingabeaufforderung:

```bat
qmake d64qt5_bridge.pro
mingw32-make release
```

Die erzeugte `d64qt5.dll` muss neben der dBase-EXE liegen. Ebenfalls benoetigt
werden die zur verwendeten Qt-Installation gehoerenden `Qt5Core.dll`,
`Qt5Gui.dll`, `Qt5Widgets.dll` und ggf. die Qt-Platform-Plugins, insbesondere
`platforms/qwindows.dll`.

PE32 muss mit einer 32-Bit-Qt5-Toolchain gebaut werden, PE32+ mit einer
64-Bit-Qt5-Toolchain.

## Stage 6: Dark output style and zoom

Die dBase-Ausgabe verwendet einen schwarzen GUI-Hintergrund und grauen Text.
Die Schrift wird in dieser Reihenfolge gewaehlt: `Consolas`, `Courier New`,
`Courier`, danach der Qt-System-Fixed-Font.

Links in der oberen Tab-Leiste befinden sich zwei selbst gezeichnete
Lupen-Schaltflaechen: `+` vergroessert die Schrift, `-` verkleinert sie.
Die Groesse wird fuer Konsole, DEBUG und DEBUG-Eingabe synchron zwischen
9 pt und 75 pt gehalten.
