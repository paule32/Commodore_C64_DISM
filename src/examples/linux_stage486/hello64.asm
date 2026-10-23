; Ubuntu 22.04, x86-64 / ELF64, Linux syscall ABI.
%include "linux64_syscalls.inc"
section .text
entry _start
_start:
    mov rax, SYS_WRITE
    mov rdi, 1
    mov rsi, message
    mov rdx, 13
    syscall
    mov rax, SYS_EXIT
    mov rdi, 0
    syscall
section .data
message:
    db 72,97,108,108,111,32,76,105,110,117,120,33,10
