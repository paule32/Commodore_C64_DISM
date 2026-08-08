; ---------------------------------------------------------------------------
; Interner d64_dism AMD64 / Windows PE64 Assembler
; ---------------------------------------------------------------------------
bits 64

import ExitProcess, "kernel32.dll", "ExitProcess"

global _start
entry _start
extern ExitProcess

_start:
    ; Compilerinternes Stack-ABI; d64_dism erzeugt beim Linken den
    ; Microsoft-x64-ABI-Adapter fuer den Windows-Import.
    push 0
    call ExitProcess
