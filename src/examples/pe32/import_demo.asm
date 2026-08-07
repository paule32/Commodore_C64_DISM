; ---------------------------------------------------------------------------
; Expliziter DLL-Import fuer den internen PE32-Assembler/COFF32-Linker
; ---------------------------------------------------------------------------
bits 32

import MessageBoxA, "user32.dll", "MessageBoxA"
import ExitProcess, "kernel32.dll", "ExitProcess"

extern MessageBoxA
extern ExitProcess

global _start
entry _start

_start:
    push 0
    push 0
    push 0
    push 0
    call MessageBoxA

    push 0
    call ExitProcess
    ret
