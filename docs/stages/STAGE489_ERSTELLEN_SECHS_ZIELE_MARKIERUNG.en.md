[Deutsch](STAGE489_ERSTELLEN_SECHS_ZIELE_MARKIERUNG.md) | [English](STAGE489_ERSTELLEN_SECHS_ZIELE_MARKIERUNG.en.md)

# Stage 489 – All Six Compiler Targets Selectable in the Build Menu

Fixes an interaction where architecture selections were not always available or visibly checked. The Build menu contains **one mutually exclusive group of six selectable targets** (Windows PE32/PE64, Linux ELF32/ELF64, and the existing additional targets), available even before opening a source file. The active choice is visibly marked and tracked per open document so switching editors preserves intended targets. This changes menu/UI state management, not compiler language semantics. Tests verify selection, persistence, and activation.
