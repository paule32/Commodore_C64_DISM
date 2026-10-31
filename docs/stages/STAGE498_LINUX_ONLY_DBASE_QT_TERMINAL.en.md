[Deutsch](STAGE498_LINUX_ONLY_DBASE_QT_TERMINAL.md) | [English](STAGE498_LINUX_ONLY_DBASE_QT_TERMINAL.en.md)

# Stage 498 – dBASE Qt5 Terminal Restricted to Linux

Reverts the Stage-490 independent terminal behavior **on Windows** while retaining it for Linux. Under Windows WFM, `DBaseQtAppendConsole` writes to the pre-existing application console, and `DBaseQtConsoleWrite` (`?` / `??`) again uses the existing Workstation Runner/pipe path. `SET DEBUG ON/OFF` and related Windows diagnostics remain unchanged. Linux keeps its standalone Qt5 terminal. Windows-specific extra globals/functions and their build dependencies are separated, resolving platform-specific compile problems without removing the Linux feature. Tests cover conditional build selection.
