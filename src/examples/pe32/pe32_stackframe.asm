.entry _start
extern ExitProcess
_start:
    push ebp
    mov ebp, esp
    sub esp, 16
    mov dword ptr [ebp-4], 42
    mov eax, [ebp-4]
    push 0
    call ExitProcess
    leave
    ret
