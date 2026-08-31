; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_crc32c


section .text align=1
__jit_crc32c:
    push	ebp
    push	ebx
    push	edi
    push	esi
    push	eax
    mov	eax, dword [esp + 28]
    xor	esi, esi
    test	eax, eax
    js	LBB0_13
    mov	ecx, dword [esp + 24]
    test	ecx, ecx
    sete	dl
    test	eax, eax
    setne	dh
    test	dl, dh
    jne	LBB0_13
    xor	edx, edx
    dec	edx
    push	8
    pop	edi
LBB0_4:
    sub	eax, 1
    jb	LBB0_8
    movzx	ebx, byte [ecx]
    xor	edx, ebx
    mov	ebx, edi
LBB0_6:
    sub	ebx, 1
    jb	LBB0_3
    mov	ebp, edx
    shr	ebp, 1
    and	edx, 1
    neg	edx
    and	edx, -2097792136
    xor	edx, ebp
    jmp	LBB0_6
LBB0_3:
    inc	ecx
    jmp	LBB0_4
LBB0_8:
    not	edx
    bswap	edx
    mov	dword [esp], edx
    push	9
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_13
    push	-4
    pop	ecx
LBB0_10:
    test	ecx, ecx
    je	LBB0_12
    movzx	edx, byte [esp + ecx + 4]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 8], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 9], dl
    inc	ecx
    jmp	LBB0_10
LBB0_12:
    mov	byte [eax + 8], 0
    mov	esi, eax
LBB0_13:
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
