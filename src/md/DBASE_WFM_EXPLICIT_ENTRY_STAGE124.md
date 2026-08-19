# Stage 124 – expliziter WFM-Programmeinstieg

Der WFM-Fallback durchsucht den vom normalen dBase-Compiler erzeugten
Assemblertext nicht mehr nach `.entry`, `_start`, `start` oder `main`.

Stattdessen wird ein eigener Einstieg erzeugt:

```asm
.entry __d64_wfm_entry
__d64_wfm_entry:
    call DBaseQtInitialize
    ; Formular / Komponenten / Properties
    call DBaseQtFormOpen
    call DBaseQtExec
    call DBaseQtShutdown
    xor eax, eax
    ret
```

Für PE32+ wird die vorhandene Win64-Aufrufkonvention mit RCX und
40 Byte Shadow-Space verwendet.

Der interne PE-Assembler wertet `.entry` direkt aus. Damit ist der
WFM-Compiler unabhängig vom Entry-Aufbau des normalen dBase-Backends.
