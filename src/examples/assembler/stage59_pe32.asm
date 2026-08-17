bits 32

global _start
entry _start

import ExitProcess, "kernel32.dll", "ExitProcess"

section .text
_start:
    push 0
    call ExitProcess
