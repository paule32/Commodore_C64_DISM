; Ubuntu 22.04, x86 / ELF32, Linux i386 syscall ABI.
section .text
entry _start
_start:
    mov eax, 1          ; __NR_exit
    mov ebx, 42         ; status
    int 0x80
