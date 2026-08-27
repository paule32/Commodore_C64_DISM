; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_sha1


section .text align=1
__jit_sha1:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 168
    mov	ebx, dword [esp + 192]
    push	5
    pop	ecx
    mov	edi, esp
    mov	esi, L_const_jit_sha1_st
    rep movsd
    xor	eax, eax
    test	ebx, ebx
    js	LBB0_21
    mov	esi, dword [esp + 188]
    test	esi, esi
    sete	cl
    test	ebx, ebx
    setne	dl
    test	cl, dl
    jne	LBB0_21
    mov	edi, esp
    mov	ebp, ebx
LBB0_3:
    cmp	ebp, 64
    jb	LBB0_5
    mov	ecx, edi
    mov	edx, esi
    call	_sha1_compress
    add	esi, 64
    add	ebp, -64
    jmp	LBB0_3
LBB0_5:
    mov	edi, ebx
    and	edi, 63
    xor	eax, eax
    cmp	edi, 56
    setae	al
    shl	eax, 6
    add	eax, 64
    xor	ecx, ecx
LBB0_6:
    cmp	eax, ecx
    je	LBB0_7
    mov	byte [esp + ecx + 40], 0
    inc	ecx
    jmp	LBB0_6
LBB0_7:
    xor	eax, eax
LBB0_8:
    cmp	edi, eax
    je	LBB0_10
    mov	cl, byte [esi + eax]
    mov	byte [esp + eax + 40], cl
    inc	eax
    jmp	LBB0_8
LBB0_10:
    xor	eax, eax
    cmp	edi, 56
    setae	al
    mov	byte [esp + edi + 40], -128
    lea	ecx, [8*ebx]
    mov	edx, ebx
    shr	edx, 29
    shl	eax, 6
    and	word [esp + eax + 96], 0
    mov	byte [esp + eax + 98], 0
    mov	byte [esp + eax + 99], dl
    mov	edx, ebx
    shr	edx, 21
    mov	byte [esp + eax + 100], dl
    mov	edx, ebx
    shr	edx, 13
    mov	byte [esp + eax + 101], dl
    shr	ebx, 5
    mov	byte [esp + eax + 102], bl
    mov	byte [esp + eax + 103], cl
    mov	ecx, esp
    lea	edx, [esp + 40]
    call	_sha1_compress
    cmp	edi, 56
    jb	LBB0_12
    lea	edx, [esp + 104]
    mov	ecx, esp
    call	_sha1_compress
LBB0_12:
    push	-20
    pop	eax
LBB0_13:
    test	eax, eax
    je	LBB0_15
    mov	ecx, dword [esp + eax + 20]
    bswap	ecx
    mov	dword [esp + eax + 40], ecx
    add	eax, 4
    jmp	LBB0_13
LBB0_15:
    push	41
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_16
    push	-20
    pop	ecx
LBB0_18:
    test	ecx, ecx
    je	LBB0_20
    movzx	edx, byte [esp + ecx + 40]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 40], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 41], dl
    inc	ecx
    jmp	LBB0_18
LBB0_20:
    mov	byte [eax + 40], 0
    jmp	LBB0_21
LBB0_16:
    xor	eax, eax
LBB0_21:
    add	esp, 168
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret
_sha1_compress:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 100
    mov	eax, dword [ecx]
    mov	dword [esp + 4], eax
    mov	eax, dword [ecx + 4]
    mov	dword [esp + 8], eax
    mov	eax, dword [ecx + 8]
    mov	dword [esp + 12], eax
    mov	ebx, dword [ecx + 12]
    mov	dword [esp + 28], ecx
    mov	esi, dword [ecx + 16]
    push	-64
    pop	eax
LBB1_1:
    test	eax, eax
    je	LBB1_2
    mov	ecx, dword [edx + eax + 64]
    bswap	ecx
    mov	dword [esp + eax + 100], ecx
    add	eax, 4
    jmp	LBB1_1
LBB1_2:
    xor	edi, edi
    mov	eax, dword [esp + 12]
    mov	dword [esp + 20], ebx
    mov	ecx, ebx
    mov	dword [esp + 24], esi
    mov	dword [esp], esi
    mov	ebx, dword [esp + 8]
    mov	edx, dword [esp + 4]
LBB1_3:
    mov	esi, dword [esp]
    mov	dword [esp], ecx
    mov	ecx, eax
    cmp	edi, 80
    je	LBB1_13
    mov	dword [esp + 32], esi
    mov	esi, ebx
    mov	ebx, edx
    cmp	edi, 16
    mov	eax, edi
    mov	dword [esp + 16], ecx
    jb	LBB1_6
    lea	ecx, [edi + 13]
    and	ecx, 15
    mov	eax, edi
    and	eax, 15
    mov	edx, eax
    xor	edx, 8
    mov	ebp, dword [esp + 4*edx + 36]
    xor	ebp, dword [esp + 4*ecx + 36]
    lea	ecx, [edi + 2]
    and	ecx, 15
    xor	ebp, dword [esp + 4*ecx + 36]
    mov	ecx, dword [esp + 16]
    xor	ebp, dword [esp + 4*eax + 36]
    rol	ebp, 1
    mov	dword [esp + 4*eax + 36], ebp
    cmp	edi, 19
    ja	LBB1_7
LBB1_6:
    mov	ebp, dword [esp]
    mov	edx, ebp
    xor	edx, ecx
    and	edx, esi
    xor	edx, ebp
    mov	ebp, dword [esp + 4*eax + 36]
    mov	eax, 1518500249
LBB1_12:
    mov	ecx, ebx
    rol	ecx, 5
    add	ecx, dword [esp + 32]
    add	ecx, eax
    add	ecx, edx
    add	ecx, ebp
    rol	esi, 30
    mov	eax, esi
    inc	edi
    mov	edx, ecx
    mov	ecx, dword [esp + 16]
    jmp	LBB1_3
LBB1_7:
    cmp	edi, 39
    ja	LBB1_9
    mov	edx, dword [esp]
    xor	edx, ecx
    xor	edx, esi
    mov	eax, 1859775393
    jmp	LBB1_12
LBB1_9:
    cmp	edi, 59
    ja	LBB1_11
    mov	eax, esi
    and	eax, ecx
    mov	edx, esi
    or	edx, ecx
    and	edx, dword [esp]
    or	edx, eax
    mov	eax, -1894007588
    jmp	LBB1_12
LBB1_11:
    mov	edx, dword [esp]
    xor	edx, ecx
    xor	edx, esi
    mov	eax, -899497514
    jmp	LBB1_12
LBB1_13:
    add	edx, dword [esp + 4]
    mov	eax, dword [esp + 28]
    mov	dword [eax], edx
    add	ebx, dword [esp + 8]
    mov	dword [eax + 4], ebx
    add	ecx, dword [esp + 12]
    mov	dword [eax + 8], ecx
    mov	ecx, dword [esp]
    add	ecx, dword [esp + 20]
    mov	dword [eax + 12], ecx
    add	esi, dword [esp + 24]
    mov	dword [eax + 16], esi
    add	esp, 100
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret

section .rdata align=4
align 4
L_const_jit_sha1_st:
    dd 1732584193
    dd 4023233417
    dd 2562383102
    dd 271733878
    dd 3285377520
_hex_alloc_lo:
    db 48,49,50,51,52,53,54,55,56,57,97,98,99,100,101,102
    db 0
