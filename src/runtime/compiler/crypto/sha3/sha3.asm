; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_sha3


section .text align=1
__jit_sha3:
    push	ebp
    mov	ebp, esp
    push	ebx
    push	edi
    push	esi
    and	esp, -8
    sub	esp, 376
    mov	edi, dword [ebp + 12]
    xor	eax, eax
    test	edi, edi
    js	LBB0_26
    mov	ebx, dword [ebp + 8]
    test	ebx, ebx
    sete	cl
    test	edi, edi
    setne	dl
    test	cl, dl
    jne	LBB0_26
    mov	eax, -200
LBB0_3:
    test	eax, eax
    je	LBB0_4
    and	dword [esp + eax + 236], 0
    and	dword [esp + eax + 232], 0
    add	eax, 8
    jmp	LBB0_3
LBB0_4:
    lea	esi, [esp + 32]
LBB0_5:
    mov	eax, -136
    cmp	edi, 136
    jae	LBB0_6
    jmp	LBB0_10
LBB0_7:
    mov	ecx, dword [ebx + eax + 136]
    mov	edx, dword [ebx + eax + 140]
    xor	dword [esp + eax + 168], ecx
    xor	dword [esp + eax + 172], edx
    add	eax, 8
LBB0_6:
    test	eax, eax
    jne	LBB0_7
    mov	ecx, esi
    call	_keccakf
    add	ebx, 136
    add	edi, -136
    jmp	LBB0_5
LBB0_9:
    mov	byte [esp + eax + 372], 0
    inc	eax
LBB0_10:
    test	eax, eax
    jne	LBB0_9
    xor	eax, eax
LBB0_12:
    cmp	edi, eax
    je	LBB0_14
    mov	cl, byte [ebx + eax]
    mov	byte [esp + eax + 236], cl
    inc	eax
    jmp	LBB0_12
LBB0_14:
    xor	byte [esp + edi + 236], 6
    xor	byte [esp + 371], -128
    mov	eax, -136
LBB0_15:
    test	eax, eax
    je	LBB0_17
    mov	ecx, dword [esp + eax + 372]
    mov	edx, dword [esp + eax + 376]
    xor	dword [esp + eax + 168], ecx
    xor	dword [esp + eax + 172], edx
    add	eax, 8
    jmp	LBB0_15
LBB0_17:
    lea	ecx, [esp + 32]
    call	_keccakf
    push	-32
    pop	eax
LBB0_18:
    test	eax, eax
    je	LBB0_20
    mov	ecx, dword [esp + eax + 64]
    mov	edx, dword [esp + eax + 68]
    mov	dword [esp + eax + 36], edx
    mov	dword [esp + eax + 32], ecx
    add	eax, 8
    jmp	LBB0_18
LBB0_20:
    push	65
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_21
    push	-32
    pop	ecx
LBB0_23:
    test	ecx, ecx
    je	LBB0_25
    movzx	edx, byte [esp + ecx + 32]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 64], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 65], dl
    inc	ecx
    jmp	LBB0_23
LBB0_25:
    mov	byte [eax + 64], 0
    jmp	LBB0_26
LBB0_21:
    xor	eax, eax
LBB0_26:
    lea	esp, [ebp - 12]
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret
_keccakf:
    push	ebp
    mov	ebp, esp
    push	ebx
    push	edi
    push	esi
    and	esp, -8
    sub	esp, 64
    xor	edx, edx
    mov	dword [esp], ecx
LBB1_1:
    cmp	edx, 24
    je	LBB1_34
    mov	dword [esp + 12], edx
    push	-40
    pop	eax
LBB1_3:
    test	eax, eax
    je	LBB1_4
    mov	esi, dword [ecx + eax + 80]
    mov	ecx, dword [esp]
    mov	edx, dword [ecx + eax + 84]
    mov	ecx, dword [esp]
    xor	esi, dword [ecx + eax + 40]
    mov	ecx, dword [esp]
    xor	edx, dword [ecx + eax + 44]
    mov	ecx, dword [esp]
    xor	edx, dword [ecx + eax + 124]
    mov	ecx, dword [esp]
    xor	esi, dword [ecx + eax + 120]
    mov	ecx, dword [esp]
    xor	esi, dword [ecx + eax + 160]
    mov	ecx, dword [esp]
    xor	edx, dword [ecx + eax + 164]
    mov	ecx, dword [esp]
    xor	edx, dword [ecx + eax + 204]
    mov	ecx, dword [esp]
    xor	esi, dword [ecx + eax + 200]
    mov	dword [esp + eax + 56], esi
    mov	dword [esp + eax + 60], edx
    mov	ecx, dword [esp]
    add	eax, 8
    jmp	LBB1_3
LBB1_4:
    xor	eax, eax
LBB1_5:
    cmp	eax, 5
    je	LBB1_14
    mov	edx, eax
    sub	edx, 1
    push	4
    pop	esi
    jb	LBB1_8
    mov	esi, edx
LBB1_8:
    lea	ecx, [eax + 1]
    xor	edi, edi
    cmp	ecx, 5
    je	LBB1_10
    mov	edi, ecx
LBB1_10:
    mov	dword [esp + 8], ecx
    mov	edx, dword [esp + 8*edi + 16]
    mov	edi, dword [esp + 8*edi + 20]
    mov	ebx, edx
    shld	ebx, edi, 1
    shld	edi, edx, 1
    xor	edi, dword [esp + 8*esi + 20]
    xor	ebx, dword [esp + 8*esi + 16]
    mov	ecx, dword [esp]
LBB1_11:
    cmp	eax, 24
    ja	LBB1_12
    xor	dword [ecx + 8*eax], ebx
    xor	dword [ecx + 8*eax + 4], edi
    add	eax, 5
    jmp	LBB1_11
LBB1_12:
    mov	eax, dword [esp + 8]
    jmp	LBB1_5
LBB1_14:
    mov	edi, dword [ecx + 8]
    mov	ebx, dword [ecx + 12]
    push	-24
    pop	eax
LBB1_15:
    test	eax, eax
    je	LBB1_16
    mov	cl, byte [eax + _ROTC+24]
    mov	edx, ebx
    shld	edx, edi, cl
    mov	esi, edi
    shl	esi, cl
    test	cl, 32
    jne	LBB1_26
    mov	dword [esp + 4], edx
    jmp	LBB1_28
LBB1_26:
    mov	dword [esp + 4], esi
    xor	esi, esi
LBB1_28:
    mov	dword [esp + 8], eax
    mov	dl, 64
    sub	dl, cl
    mov	ecx, edx
    shrd	edi, ebx, cl
    shr	ebx, cl
    test	dl, 32
    je	LBB1_30
    mov	edi, ebx
    xor	ebx, ebx
LBB1_30:
    mov	eax, dword [esp]
    mov	ecx, dword [esp + 4]
    or	edi, esi
    or	ebx, ecx
    mov	edx, dword [esp + 8]
    movzx	ecx, byte [edx + _PILN+24]
    mov	esi, dword [eax + 8*ecx]
    mov	dword [esp + 4], esi
    mov	dword [eax + 8*ecx], edi
    mov	esi, dword [eax + 8*ecx + 4]
    mov	dword [eax + 8*ecx + 4], ebx
    mov	eax, edx
    inc	eax
    mov	edi, dword [esp + 4]
    mov	ebx, esi
    jmp	LBB1_15
LBB1_16:
    xor	eax, eax
    mov	edx, dword [esp]
LBB1_17:
    cmp	eax, 24
    ja	LBB1_33
    mov	dword [esp + 8], eax
    push	-40
    pop	ecx
LBB1_19:
    test	ecx, ecx
    je	LBB1_20
    mov	esi, dword [edx + ecx + 40]
    mov	edi, dword [edx + ecx + 44]
    mov	dword [esp + ecx + 56], esi
    mov	dword [esp + ecx + 60], edi
    add	ecx, 8
    jmp	LBB1_19
LBB1_20:
    xor	esi, esi
LBB1_21:
    cmp	esi, 5
    je	LBB1_32
    lea	edi, [esi + 1]
    xor	ebx, ebx
    cmp	edi, 5
    je	LBB1_24
    mov	ebx, edi
LBB1_24:
    mov	ecx, dword [esp + 8*ebx + 16]
    mov	ebx, dword [esp + 8*ebx + 20]
    not	ecx
    not	ebx
    xor	eax, eax
    cmp	esi, 3
    setb	al
    lea	eax, [eax + 4*eax]
    add	eax, esi
    and	ebx, dword [esp + 8*eax - 4]
    and	ecx, dword [esp + 8*eax - 8]
    xor	dword [edx + 8*esi], ecx
    xor	dword [edx + 8*esi + 4], ebx
    mov	esi, edi
    jmp	LBB1_21
LBB1_32:
    mov	eax, dword [esp + 8]
    add	eax, 5
    add	edx, 40
    jmp	LBB1_17
LBB1_33:
    mov	esi, dword [esp + 12]
    mov	eax, dword [8*esi + _RC+4]
    mov	edx, dword [8*esi + _RC]
    mov	ecx, dword [esp]
    xor	dword [ecx], edx
    mov	edx, esi
    xor	dword [ecx + 4], eax
    inc	edx
    jmp	LBB1_1
LBB1_34:
    lea	esp, [ebp - 12]
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret

section .rdata align=4
_PILN:
    db 10,7,11,17,18,3,5,16,8,21,24,4,15,23,19,13
    db 12,2,20,14,22,9,6,1
_ROTC:
    db 1,3,6,10,15,21,28,36,45,55,2,14,27,41,56,8
    db 25,43,62,18,39,61,20,44
align 8
_RC:
    dq 1
    dq 32898
    dq -9223372036854742902
    dq -9223372034707259392
    dq 32907
    dq 2147483649
    dq -9223372034707259263
    dq -9223372036854743031
    dq 138
    dq 136
    dq 2147516425
    dq 2147483658
    dq 2147516555
    dq -9223372036854775669
    dq -9223372036854742903
    dq -9223372036854743037
    dq -9223372036854743038
    dq -9223372036854775680
    dq 32778
    dq -9223372034707292150
    dq -9223372034707259263
    dq -9223372036854742912
    dq 2147483649
    dq -9223372034707259384
_hex_alloc_lo:
    db 48,49,50,51,52,53,54,55,56,57,97,98,99,100,101,102
    db 0
