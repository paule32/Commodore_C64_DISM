; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_sha256


section .text align=1
__jit_sha256:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 192
    mov	ebx, dword [esp + 216]
    push	8
    pop	ecx
    mov	edi, esp
    mov	esi, L_const_jit_sha256_st
    rep movsd
    xor	eax, eax
    test	ebx, ebx
    js	LBB0_21
    mov	esi, dword [esp + 212]
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
    call	_sha2_compress
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
    mov	byte [esp + ecx + 32], 0
    inc	ecx
    jmp	LBB0_6
LBB0_7:
    xor	eax, eax
LBB0_8:
    cmp	edi, eax
    je	LBB0_10
    mov	cl, byte [esi + eax]
    mov	byte [esp + eax + 32], cl
    inc	eax
    jmp	LBB0_8
LBB0_10:
    xor	eax, eax
    cmp	edi, 56
    setae	al
    mov	byte [esp + edi + 32], -128
    lea	ecx, [8*ebx]
    mov	edx, ebx
    shr	edx, 29
    shl	eax, 6
    and	word [esp + eax + 88], 0
    mov	byte [esp + eax + 90], 0
    mov	byte [esp + eax + 91], dl
    mov	edx, ebx
    shr	edx, 21
    mov	byte [esp + eax + 92], dl
    mov	edx, ebx
    shr	edx, 13
    mov	byte [esp + eax + 93], dl
    shr	ebx, 5
    mov	byte [esp + eax + 94], bl
    mov	byte [esp + eax + 95], cl
    mov	ecx, esp
    lea	edx, [esp + 32]
    call	_sha2_compress
    cmp	edi, 56
    jb	LBB0_12
    lea	edx, [esp + 96]
    mov	ecx, esp
    call	_sha2_compress
LBB0_12:
    push	-32
    pop	eax
LBB0_13:
    test	eax, eax
    je	LBB0_15
    mov	ecx, dword [esp + eax + 32]
    bswap	ecx
    mov	dword [esp + eax + 192], ecx
    add	eax, 4
    jmp	LBB0_13
LBB0_15:
    push	65
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_16
    push	-32
    pop	ecx
LBB0_18:
    test	ecx, ecx
    je	LBB0_20
    movzx	edx, byte [esp + ecx + 192]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 64], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 65], dl
    inc	ecx
    jmp	LBB0_18
LBB0_20:
    mov	byte [eax + 64], 0
    jmp	LBB0_21
LBB0_16:
    xor	eax, eax
LBB0_21:
    add	esp, 192
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret
_sha2_compress:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 132
    mov	eax, dword [ecx]
    mov	dword [esp + 12], eax
    mov	eax, dword [ecx + 4]
    mov	dword [esp + 16], eax
    mov	eax, dword [ecx + 8]
    mov	dword [esp + 20], eax
    mov	eax, dword [ecx + 12]
    mov	dword [esp + 24], eax
    mov	eax, dword [ecx + 16]
    mov	dword [esp + 28], eax
    mov	ebp, dword [ecx + 20]
    mov	ebx, dword [ecx + 24]
    mov	dword [esp + 52], ecx
    mov	esi, dword [ecx + 28]
    push	-64
    pop	eax
LBB1_1:
    test	eax, eax
    je	LBB1_2
    mov	ecx, dword [edx + eax + 64]
    bswap	ecx
    mov	dword [esp + eax + 132], ecx
    add	eax, 4
    jmp	LBB1_1
LBB1_2:
    xor	edi, edi
    mov	dword [esp + 40], ebp
    mov	ecx, ebp
    mov	dword [esp + 44], ebx
    mov	dword [esp], ebx
    mov	dword [esp + 48], esi
    mov	ebx, esi
    mov	edx, dword [esp + 28]
    mov	eax, dword [esp + 24]
    mov	dword [esp + 8], eax
    mov	eax, dword [esp + 20]
    mov	dword [esp + 4], eax
    mov	esi, dword [esp + 16]
    mov	eax, dword [esp + 12]
LBB1_3:
    mov	ebp, dword [esp]
    mov	dword [esp], ecx
    cmp	edi, 64
    je	LBB1_7
    mov	dword [esp + 60], eax
    mov	dword [esp + 64], esi
    mov	esi, ebp
    lea	eax, [edi + 1]
    mov	dword [esp + 32], eax
    cmp	edi, 16
    mov	eax, edi
    mov	dword [esp + 36], edx
    jb	LBB1_6
    mov	eax, dword [esp + 32]
    and	eax, 15
    mov	edx, dword [esp + 4*eax + 68]
    mov	eax, edx
    rol	eax, 25
    mov	ecx, edx
    rol	ecx, 14
    xor	ecx, eax
    shr	edx, 3
    xor	edx, ecx
    lea	eax, [edi + 14]
    and	eax, 15
    mov	ecx, dword [esp + 4*eax + 68]
    mov	ebp, ebx
    mov	ebx, ecx
    rol	ebx, 15
    mov	eax, ecx
    rol	eax, 13
    xor	eax, ebx
    mov	ebx, ebp
    shr	ecx, 10
    xor	ecx, eax
    lea	eax, [edi + 9]
    and	eax, 15
    add	edx, dword [esp + 4*eax + 68]
    mov	eax, edi
    and	eax, 15
    add	edx, dword [esp + 4*eax + 68]
    add	edx, ecx
    mov	dword [esp + 4*eax + 68], edx
    mov	edx, dword [esp + 36]
LBB1_6:
    mov	ecx, edx
    rol	ecx, 26
    mov	ebp, edx
    rol	edx, 21
    xor	edx, ecx
    mov	ecx, ebp
    rol	ecx, 7
    xor	ecx, edx
    mov	dword [esp + 56], esi
    mov	edx, esi
    xor	edx, dword [esp]
    and	edx, ebp
    xor	edx, esi
    add	edx, ebx
    add	edx, ecx
    add	edx, dword [4*edi + _K]
    add	edx, dword [esp + 4*eax + 68]
    mov	esi, dword [esp + 60]
    mov	eax, esi
    rol	eax, 30
    mov	ecx, esi
    rol	ecx, 19
    xor	ecx, eax
    mov	edi, esi
    rol	edi, 10
    xor	edi, ecx
    mov	ecx, esi
    mov	ebx, dword [esp + 64]
    and	ecx, ebx
    mov	eax, esi
    or	eax, ebx
    mov	ebp, dword [esp + 4]
    and	eax, ebp
    or	eax, ecx
    add	eax, edi
    mov	edi, dword [esp + 8]
    add	edi, edx
    add	eax, edx
    mov	ecx, dword [esp + 36]
    mov	edx, edi
    mov	dword [esp + 8], ebp
    mov	dword [esp + 4], ebx
    mov	ebx, dword [esp + 56]
    mov	edi, dword [esp + 32]
    jmp	LBB1_3
LBB1_7:
    add	eax, dword [esp + 12]
    mov	ecx, eax
    mov	eax, dword [esp + 52]
    mov	dword [eax], ecx
    add	esi, dword [esp + 16]
    mov	dword [eax + 4], esi
    mov	ecx, dword [esp + 4]
    add	ecx, dword [esp + 20]
    mov	dword [eax + 8], ecx
    mov	ecx, dword [esp + 8]
    add	ecx, dword [esp + 24]
    mov	dword [eax + 12], ecx
    add	edx, dword [esp + 28]
    mov	dword [eax + 16], edx
    mov	ecx, dword [esp]
    add	ecx, dword [esp + 40]
    mov	dword [eax + 20], ecx
    add	ebp, dword [esp + 44]
    mov	dword [eax + 24], ebp
    add	ebx, dword [esp + 48]
    mov	dword [eax + 28], ebx
    add	esp, 132
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret

section .rdata align=4
align 4
L_const_jit_sha256_st:
    dd 1779033703
    dd 3144134277
    dd 1013904242
    dd 2773480762
    dd 1359893119
    dd 2600822924
    dd 528734635
    dd 1541459225
align 4
_K:
    dd 1116352408
    dd 1899447441
    dd 3049323471
    dd 3921009573
    dd 961987163
    dd 1508970993
    dd 2453635748
    dd 2870763221
    dd 3624381080
    dd 310598401
    dd 607225278
    dd 1426881987
    dd 1925078388
    dd 2162078206
    dd 2614888103
    dd 3248222580
    dd 3835390401
    dd 4022224774
    dd 264347078
    dd 604807628
    dd 770255983
    dd 1249150122
    dd 1555081692
    dd 1996064986
    dd 2554220882
    dd 2821834349
    dd 2952996808
    dd 3210313671
    dd 3336571891
    dd 3584528711
    dd 113926993
    dd 338241895
    dd 666307205
    dd 773529912
    dd 1294757372
    dd 1396182291
    dd 1695183700
    dd 1986661051
    dd 2177026350
    dd 2456956037
    dd 2730485921
    dd 2820302411
    dd 3259730800
    dd 3345764771
    dd 3516065817
    dd 3600352804
    dd 4094571909
    dd 275423344
    dd 430227734
    dd 506948616
    dd 659060556
    dd 883997877
    dd 958139571
    dd 1322822218
    dd 1537002063
    dd 1747873779
    dd 1955562222
    dd 2024104815
    dd 2227730452
    dd 2361852424
    dd 2428436474
    dd 2756734187
    dd 3204031479
    dd 3329325298
_hex_alloc_lo:
    db 48,49,50,51,52,53,54,55,56,57,97,98,99,100,101,102
    db 0
