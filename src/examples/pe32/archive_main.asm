.entry _start
extern add42
extern ExitProcess
_start:
    mov eax, 1
    call add42
    push 0
    call ExitProcess
    ret
