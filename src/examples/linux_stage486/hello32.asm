; Ubuntu 22.04, x86 / ELF32, Linux i386 syscall ABI.
section .text
entry _start
_start:
    mov eax, 4          ; __NR_write
    mov ebx, 1
    mov ecx, message
    mov edx, 13
    int 0x80
    mov eax, 1          ; __NR_exit
    mov ebx, 0
    int 0x80
section .data
message:
    db 72,97,108,108,111,32,76,105,110,117,120,33,10
