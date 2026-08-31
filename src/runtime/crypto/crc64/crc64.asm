; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_crc64


section .text align=1
__jit_crc64:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 8
    mov	ecx, dword [esp + 32]
    xor	eax, eax
    test	ecx, ecx
    js	LBB0_14
    mov	edx, dword [esp + 28]
    test	edx, edx
    sete	bl
    test	ecx, ecx
    setne	bh
    test	bl, bh
    jne	LBB0_14
    xor	eax, eax
    xor	edi, edi
LBB0_4:
    sub	ecx, 1
    jb	LBB0_8
    movzx	ebx, byte [edx]
    shl	ebx, 24
    xor	edi, ebx
    push	8
    pop	ebx
LBB0_6:
    sub	ebx, 1
    jb	LBB0_3
    mov	ebp, edi
    shld	ebp, eax, 1
    add	eax, eax
    sar	edi, 31
    mov	esi, edi
    and	esi, -1444268397
    xor	eax, esi
    and	edi, 1123082731
    xor	edi, ebp
    jmp	LBB0_6
LBB0_3:
    inc	edx
    jmp	LBB0_4
LBB0_8:
    bswap	eax
    mov	dword [esp + 4], eax
    bswap	edi
    mov	dword [esp], edi
    push	17
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_9
    push	-8
    pop	ecx
LBB0_11:
    test	ecx, ecx
    je	LBB0_13
    movzx	edx, byte [esp + ecx + 8]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_hi]
    mov	byte [eax + 2*ecx + 16], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_hi]
    mov	byte [eax + 2*ecx + 17], dl
    inc	ecx
    jmp	LBB0_11
LBB0_13:
    mov	byte [eax + 16], 0
    jmp	LBB0_14
LBB0_9:
    xor	eax, eax
LBB0_14:
    add	esp, 8
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret

section .rdata align=4
_hex_alloc_hi:
    db 48,49,50,51,52,53,54,55,56,57,65,66,67,68,69,70
    db 0
