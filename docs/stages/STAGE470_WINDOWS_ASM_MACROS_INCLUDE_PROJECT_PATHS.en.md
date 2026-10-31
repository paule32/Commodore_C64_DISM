[Deutsch](STAGE470_WINDOWS_ASM_MACROS_INCLUDE_PROJECT_PATHS.md) | [English](STAGE470_WINDOWS_ASM_MACROS_INCLUDE_PROJECT_PATHS.en.md)

# Stage 470 – Windows Assembly Preprocessor and Project Include Paths

Adds assembly preprocessor macros for PE32 and PE32+, including `__LINE__` (original ASM/INC source line), `__TIME__` (`"HH:MM:SS"`), and `__DATE__` (`"YYYY-MM-DD"`). Project Settings → Compiler → Input Directory supplies include search paths; nested includes and source locations are tracked. The generated WFM/dBASE import lists are also compacted. The preprocessor must preserve references, symbols, and diagnostics after macro expansion. Tests cover both Windows architectures and project include paths.

## Source code and command examples (unchanged)

```asm
%include "extern.inc"
%include "<extern.inc>"        ; alternative, ebenfalls erlaubt
%include <extern.inc>
%define MAKRO 2
%define TEXT "text"
%undef MAKRO

%if MAKRO == 2
    mov eax, MAKRO
%elif MAKRO => 4
    mov eax, 4
%else
    mov eax, 0
%endif

%ifdef TEXT
    ; ...
%endif
%ifndef TEXT
    ; ...
%endif
```


```text
Projekt-Einstellungen → Windows → 32-Bit → Compiler → Eingabe-Verzeichnis
  C:\MeinProjekt\asm\include
  C:\MeineBibliotheken\extern
```


```asm
%include "extern.inc"
section .text
entry _start
_start:
    mov eax, 2
    ret
```


```text
Form1.generated.pe32.asm
Form1.generated.pe32.extern.inc
```


```asm
%include "<Form1.generated.pe32.extern.inc>"
```

