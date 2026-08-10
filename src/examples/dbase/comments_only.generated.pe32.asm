bits 32

import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start

section .text

_start:
    push 0
    call ExitProcess
