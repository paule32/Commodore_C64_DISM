; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_md5


section .text align=1
__jit_md5:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 160
    mov	ebx, dword [esp + 184]
    mov	dword [esp + 12], 271733878
    mov	dword [esp + 8], -1732584194
    mov	dword [esp + 4], -271733879
    mov	dword [esp], 1732584193
    xor	eax, eax
    test	ebx, ebx
    js	LBB0_21
    mov	esi, dword [esp + 180]
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
    call	_md5_compress
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
    lea	edx, [8*ebx]
    mov	ecx, ebx
    shr	ecx, 29
    shl	eax, 6
    mov	byte [esp + eax + 88], dl
    mov	edx, ebx
    shr	edx, 5
    mov	byte [esp + eax + 89], dl
    mov	edx, ebx
    shr	edx, 13
    mov	byte [esp + eax + 90], dl
    shr	ebx, 21
    mov	byte [esp + eax + 91], bl
    mov	byte [esp + eax + 92], cl
    and	word [esp + eax + 93], 0
    mov	byte [esp + eax + 95], 0
    mov	ecx, esp
    lea	edx, [esp + 32]
    call	_md5_compress
    cmp	edi, 56
    jb	LBB0_12
    lea	edx, [esp + 96]
    mov	ecx, esp
    call	_md5_compress
LBB0_12:
    push	-16
    pop	eax
LBB0_13:
    test	eax, eax
    je	LBB0_15
    mov	ecx, dword [esp + eax + 16]
    mov	dword [esp + eax + 32], ecx
    add	eax, 4
    jmp	LBB0_13
LBB0_15:
    push	33
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_16
    push	-16
    pop	ecx
LBB0_18:
    test	ecx, ecx
    je	LBB0_20
    movzx	edx, byte [esp + ecx + 32]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 32], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 33], dl
    inc	ecx
    jmp	LBB0_18
LBB0_20:
    mov	byte [eax + 32], 0
    jmp	LBB0_21
LBB0_16:
    xor	eax, eax
LBB0_21:
    add	esp, 160
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret
_md5_compress:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 96
    mov	eax, dword [ecx]
    mov	dword [esp], eax
    mov	esi, dword [ecx + 4]
    mov	ebp, dword [ecx + 8]
    mov	dword [esp + 24], ecx
    mov	edi, dword [ecx + 12]
    push	-64
    pop	eax
LBB1_1:
    test	eax, eax
    je	LBB1_2
    mov	ecx, dword [edx + eax + 64]
    mov	dword [esp + eax + 96], ecx
    add	eax, 4
    jmp	LBB1_1
LBB1_2:
    xor	ebx, ebx
    inc	ebx
    mov	dword [esp + 8], 0
    push	5
    pop	eax
    mov	dword [esp + 4], eax
    mov	dword [esp + 12], esi
    mov	dword [esp + 16], ebp
    mov	dword [esp + 20], edi
    mov	eax, edi
    mov	edx, dword [esp]
    xor	edi, edi
LBB1_3:
    mov	ecx, edx
    mov	edx, eax
    mov	eax, ebp
    mov	ebp, esi
    cmp	ebx, 321
    je	LBB1_13
    cmp	edi, 15
    mov	dword [esp + 28], ebx
    ja	LBB1_6
    mov	esi, edx
    xor	esi, eax
    and	esi, ebp
    xor	esi, edx
    mov	ebx, edi
    jmp	LBB1_12
LBB1_6:
    cmp	edi, 31
    ja	LBB1_8
    mov	esi, eax
    xor	esi, ebp
    and	esi, edx
    xor	esi, eax
    jmp	LBB1_11
LBB1_8:
    cmp	edi, 47
    ja	LBB1_10
    mov	esi, eax
    xor	esi, ebp
    xor	esi, edx
    mov	ebx, dword [esp + 4]
    jmp	LBB1_11
LBB1_10:
    mov	esi, edx
    not	esi
    or	esi, ebp
    xor	esi, eax
    mov	ebx, dword [esp + 8]
LBB1_11:
    and	ebx, 15
LBB1_12:
    add	esi, ecx
    add	esi, dword [4*edi + _K]
    add	esi, dword [esp + 4*ebx + 32]
    mov	cl, byte [edi + _S]
    rol	esi, cl
    add	esi, ebp
    inc	edi
    mov	ebx, dword [esp + 28]
    add	ebx, 5
    add	dword [esp + 8], 7
    add	dword [esp + 4], 3
    jmp	LBB1_3
LBB1_13:
    add	ecx, dword [esp]
    mov	esi, dword [esp + 24]
    mov	dword [esi], ecx
    add	ebp, dword [esp + 12]
    mov	dword [esi + 4], ebp
    add	eax, dword [esp + 16]
    mov	dword [esi + 8], eax
    add	edx, dword [esp + 20]
    mov	dword [esi + 12], edx
    add	esp, 96
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret

section .rdata align=4
align 4
L_const_jit_md5_st:
    dd 1732584193
    dd 4023233417
    dd 2562383102
    dd 271733878
align 4
_K:
    dd 3614090360
    dd 3905402710
    dd 606105819
    dd 3250441966
    dd 4118548399
    dd 1200080426
    dd 2821735955
    dd 4249261313
    dd 1770035416
    dd 2336552879
    dd 4294925233
    dd 2304563134
    dd 1804603682
    dd 4254626195
    dd 2792965006
    dd 1236535329
    dd 4129170786
    dd 3225465664
    dd 643717713
    dd 3921069994
    dd 3593408605
    dd 38016083
    dd 3634488961
    dd 3889429448
    dd 568446438
    dd 3275163606
    dd 4107603335
    dd 1163531501
    dd 2850285829
    dd 4243563512
    dd 1735328473
    dd 2368359562
    dd 4294588738
    dd 2272392833
    dd 1839030562
    dd 4259657740
    dd 2763975236
    dd 1272893353
    dd 4139469664
    dd 3200236656
    dd 681279174
    dd 3936430074
    dd 3572445317
    dd 76029189
    dd 3654602809
    dd 3873151461
    dd 530742520
    dd 3299628645
    dd 4096336452
    dd 1126891415
    dd 2878612391
    dd 4237533241
    dd 1700485571
    dd 2399980690
    dd 4293915773
    dd 2240044497
    dd 1873313359
    dd 4264355552
    dd 2734768916
    dd 1309151649
    dd 4149444226
    dd 3174756917
    dd 718787259
    dd 3951481745
_S:
    db 7,12,17,22,7,12,17,22,7,12,17,22,7,12,17,22
    db 5,9,14,20,5,9,14,20,5,9,14,20,5,9,14,20
    db 4,11,16,23,4,11,16,23,4,11,16,23,4,11,16,23
    db 6,10,15,21,6,10,15,21,6,10,15,21,6,10,15,21
_hex_alloc_lo:
    db 48,49,50,51,52,53,54,55,56,57,97,98,99,100,101,102
    db 0
