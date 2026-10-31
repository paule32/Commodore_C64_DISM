[Deutsch](STAGE490_DBASE_CROSS_PLATFORM_QT_TERMINAL.md) | [English](STAGE490_DBASE_CROSS_PLATFORM_QT_TERMINAL.en.md)

# Stage 490 – Cross-Platform dBASE Qt5 Terminal and TYPE()

Adds a Qt5 text terminal for `?` and `??` output on supported platforms. In GUI mode `?` appends a line break, while `??` does not; output appears in a read-only `QPlainTextEdit` window. Windows extends existing `DBaseQtConsoleWrite`/`DBaseQtAppendConsole` support. Linux WFM invokes `DBaseQtRunFormJson` in `libd64_qt5.so` and includes pre-class executable output as JSON `startup_output`; Linux PRG compilation can use `compile_linux_prg(..., qt_terminal=True)`. The source documents limitations of native Qt builds and an issue reproduced with `Form1.wfm`, distinguishing tested generation from unverified runtime.

## Source code and command examples (unchanged)

```bash
sudo apt install build-essential qtbase5-dev qt5-qmake
cd d64qt5
./build_linux.sh
```

