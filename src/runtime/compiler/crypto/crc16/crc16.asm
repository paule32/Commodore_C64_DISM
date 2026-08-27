; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_crc16


section .text align=1
__jit_crc16:
    push	ebp
    push	ebx
    push	edi
    push	esi
    push	eax
    mov	eax, dword [esp + 28]
    xor	esi, esi
    test	eax, eax
    js	LBB0_15
    mov	ecx, dword [esp + 24]
    test	ecx, ecx
    sete	dl
    test	eax, eax
    setne	dh
    test	dl, dh
    jne	LBB0_15
    xor	edi, edi
    dec	edi
    push	8
    pop	edx
LBB0_4:
    sub	eax, 1
    jb	LBB0_10
    movzx	ebx, byte [ecx]
    shl	ebx, 8
    xor	edi, ebx
    mov	ebx, edx
LBB0_6:
    sub	ebx, 1
    jb	LBB0_3
    lea	ebp, [edi + edi]
    test	di, di
    jns	LBB0_9
    xor	ebp, 4129
LBB0_9:
    mov	edi, ebp
    jmp	LBB0_6
LBB0_3:
    inc	ecx
    jmp	LBB0_4
LBB0_10:
    rol	di, 8
    mov	word [esp + 2], di
    push	5
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_15
    push	-2
    pop	ecx
LBB0_12:
    test	ecx, ecx
    je	LBB0_14
    movzx	edx, byte [esp + ecx + 4]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 4], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 5], dl
    inc	ecx
    jmp	LBB0_12
LBB0_14:
    mov	byte [eax + 4], 0
    mov	esi, eax
LBB0_15:
    mov	eax, esi
    add	esp, 4
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret

section .rdata align=4
_hex_alloc_lo:
    db 48,49,50,51,52,53,54,55,56,57,97,98,99,100,101,102
    db 0
