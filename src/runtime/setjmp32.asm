; ---------------------------------------------------------------------------
; int __cdecl _jit_setjmp(JitJumpBuffer *env)
; ---------------------------------------------------------------------------
bits 32
section .text
global ___jit_setjmp
___jit_setjmp:
    mov     edx, [esp + 4]      ; env

    mov     [edx + 0], ebx
    mov     [edx + 4], esi
    mov     [edx + 8], edi
    mov     [edx + 12], ebp

    lea     eax, [esp + 4]      ; stack nach return
    mov     [edx + 16], eax

    mov     eax, [esp]          ; return address
    mov     [edx + 20], eax

    xor     eax, eax            ; return 0
    ret


; ---------------------------------------------------------------------------
; void __cdecl _jit_longjmp(JitJumpBuffer *env, int value)
; ---------------------------------------------------------------------------
global ___jit_longjmp
___jit_longjmp:
    mov     edx, [esp + 4]      ; env
    mov     eax, [esp + 8]      ; value

    test    eax, eax
    jne     .value_ok
    mov     eax, 1              ; longjmp darf nicht 0 zurückgeben

.value_ok:
    mov     ebx, [edx + 0]
    mov     esi, [edx + 4]
    mov     edi, [edx + 8]
    mov     ebp, [edx + 12]
    mov     esp, [edx + 16]

    jmp     dword [edx + 20]
