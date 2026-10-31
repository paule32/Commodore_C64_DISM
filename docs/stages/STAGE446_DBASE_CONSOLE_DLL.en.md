[Deutsch](STAGE446_DBASE_CONSOLE_DLL.md) | [English](STAGE446_DBASE_CONSOLE_DLL.en.md)

# Stage 446 – dBASE Console as an External PE32/PE32+ Runtime DLL

Introduces architecture-specific `d64_dbase_console.dll` builds at `d64dbase/bin/pe32/` (i386) and `d64dbase/bin/pe64/` (AMD64). The console runtime exports C-callable functions for writing text, shutting down, and maintaining console state. The ordinary dBASE PRG compiler imports and calls `DBaseConsoleWrite` and `DBaseConsoleShutdown`; the existing `D64DBASE_LAZY_CONSOLE_V1` marker is retained. WFM event output still uses `DBaseQtConsoleWrite` from `libd64_qt5.dll` and is not silently redirected. The PE32+ assembler receives the necessary eight-bit instructions. The documentation records internal COFF/PE build and deployment, tests, and limitations of native Windows validation.
