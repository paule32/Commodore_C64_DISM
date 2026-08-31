; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

extern __jit_malloc
global __jit_sha384


section .text align=1
__jit_sha384:
    push	ebp
    mov	ebp, esp
    push	ebx
    push	edi
    push	esi
    and	esp, -8
    sub	esp, 376
    mov	ebx, dword [ebp + 12]
    push	16
    pop	ecx
    mov	edi, esp
    mov	esi, L_const_jit_sha384_st
    rep movsd
    xor	eax, eax
    test	ebx, ebx
    js	LBB0_21
    mov	esi, dword [ebp + 8]
    test	esi, esi
    sete	cl
    test	ebx, ebx
    setne	dl
    test	cl, dl
    jne	LBB0_21
    mov	edi, esp
LBB0_3:
    cmp	ebx, 128
    jb	LBB0_5
    mov	ecx, edi
    mov	edx, esi
    call	_sha384_compress
    sub	esi, -128
    add	ebx, -128
    jmp	LBB0_3
LBB0_5:
    mov	ebx, dword [ebp + 12]
    mov	edi, ebx
    and	edi, 127
    xor	eax, eax
    cmp	edi, 112
    setae	al
    shl	eax, 7
    sub	eax, -128
    xor	ecx, ecx
LBB0_6:
    cmp	eax, ecx
    je	LBB0_7
    mov	byte [esp + ecx + 116], 0
    inc	ecx
    jmp	LBB0_6
LBB0_7:
    xor	eax, eax
LBB0_8:
    cmp	edi, eax
    je	LBB0_10
    mov	cl, byte [esi + eax]
    mov	byte [esp + eax + 116], cl
    inc	eax
    jmp	LBB0_8
LBB0_10:
    xor	eax, eax
    cmp	edi, 112
    setae	al
    mov	byte [esp + edi + 116], -128
    lea	edx, [8*ebx]
    shr	ebx, 29
    shl	eax, 7
    lea	ecx, [esp + eax + 236]
    and	dword [ecx - 8], 0
    and	dword [ecx - 4], 0
    push	ebx
    call	_store_be64
    pop	eax
    mov	ecx, esp
    lea	edx, [esp + 116]
    call	_sha384_compress
    cmp	edi, 112
    jb	LBB0_12
    lea	edx, [esp + 244]
    mov	ecx, esp
    call	_sha384_compress
LBB0_12:
    push	-6
    pop	edi
    lea	esi, [esp + 68]
LBB0_13:
    test	edi, edi
    je	LBB0_15
    mov	edx, dword [esp + 8*edi + 48]
    mov	ecx, esi
    push	dword [esp + 8*edi + 52]
    call	_store_be64
    pop	eax
    inc	edi
    add	esi, 8
    jmp	LBB0_13
LBB0_15:
    push	97
    call	__jit_malloc
    pop	ecx
    test	eax, eax
    je	LBB0_16
    push	-48
    pop	ecx
LBB0_18:
    test	ecx, ecx
    je	LBB0_20
    movzx	edx, byte [esp + ecx + 116]
    mov	esi, edx
    shr	esi, 4
    mov	bl, byte [esi + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 96], bl
    and	edx, 15
    mov	dl, byte [edx + _hex_alloc_lo]
    mov	byte [eax + 2*ecx + 97], dl
    inc	ecx
    jmp	LBB0_18
LBB0_20:
    mov	byte [eax + 96], 0
    jmp	LBB0_21
LBB0_16:
    xor	eax, eax
LBB0_21:
    lea	esp, [ebp - 12]
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret
_sha384_compress:
    push	ebp
    mov	ebp, esp
    push	ebx
    push	edi
    push	esi
    and	esp, -8
    sub	esp, 280
    mov	edi, edx
    mov	eax, dword [ecx]
    mov	dword [esp + 36], eax
    mov	eax, dword [ecx + 4]
    mov	dword [esp + 8], eax
    mov	eax, dword [ecx + 12]
    mov	dword [esp + 24], eax
    mov	eax, dword [ecx + 8]
    mov	dword [esp + 56], eax
    mov	eax, dword [ecx + 20]
    mov	dword [esp + 48], eax
    mov	eax, dword [ecx + 16]
    mov	dword [esp + 44], eax
    mov	eax, dword [ecx + 28]
    mov	dword [esp + 64], eax
    mov	eax, dword [ecx + 24]
    mov	dword [esp + 60], eax
    mov	eax, dword [ecx + 36]
    mov	dword [esp + 28], eax
    mov	eax, dword [ecx + 32]
    mov	dword [esp + 20], eax
    mov	eax, dword [ecx + 44]
    mov	dword [esp + 12], eax
    mov	edx, dword [ecx + 40]
    mov	ebx, dword [ecx + 52]
    mov	eax, dword [ecx + 48]
    mov	dword [esp + 52], eax
    mov	eax, dword [ecx + 60]
    mov	dword [esp], eax
    mov	dword [esp + 76], ecx
    mov	eax, dword [ecx + 56]
    mov	dword [esp + 16], eax
    push	-16
    pop	esi
    mov	dword [esp + 40], ebx
    mov	dword [esp + 4], edx
LBB1_1:
    test	esi, esi
    je	LBB1_2
    mov	ecx, edi
    call	_load_be32
    mov	ebx, eax
    lea	ecx, [edi + 4]
    call	_load_be32
    mov	edx, dword [esp + 4]
    mov	dword [esp + 8*esi + 276], ebx
    mov	ebx, dword [esp + 40]
    mov	dword [esp + 8*esi + 272], eax
    inc	esi
    add	edi, 8
    jmp	LBB1_1
LBB1_2:
    xor	ecx, ecx
    mov	edi, dword [esp + 36]
    mov	esi, dword [esp + 12]
LBB1_3:
    mov	dword [esp + 68], ebx
    mov	eax, dword [esp + 52]
    mov	dword [esp + 12], eax
    mov	ebx, esi
    cmp	ecx, 80
    mov	dword [esp + 52], edx
    je	LBB1_4
    mov	dword [esp + 40], ebx
    mov	dword [esp + 36], edi
    lea	eax, [ecx + 1]
    mov	dword [esp + 72], eax
    cmp	ecx, 16
    mov	dword [esp + 4], ecx
    mov	edx, ecx
    jb	LBB1_9
    mov	eax, dword [esp + 72]
    and	eax, 15
    mov	ebx, dword [esp + 8*eax + 144]
    mov	eax, dword [esp + 8*eax + 148]
    mov	esi, ebx
    shld	esi, eax, 31
    mov	edi, eax
    shld	edi, ebx, 31
    mov	ecx, ebx
    shld	ecx, eax, 24
    xor	ecx, esi
    mov	esi, eax
    shld	esi, ebx, 24
    xor	esi, edi
    shrd	ebx, eax, 7
    xor	ebx, esi
    shr	eax, 7
    xor	eax, ecx
    mov	ecx, dword [esp + 4]
    add	ecx, 14
    and	ecx, 15
    mov	esi, dword [esp + 8*ecx + 144]
    mov	ecx, dword [esp + 8*ecx + 148]
    mov	edx, esi
    shld	edx, ecx, 13
    mov	edi, ecx
    shld	edi, esi, 3
    xor	edi, edx
    mov	edx, ecx
    shld	edx, esi, 13
    mov	dword [esp + 32], ecx
    shld	dword [esp + 32], esi, 26
    shld	esi, ecx, 3
    xor	esi, edx
    xor	esi, dword [esp + 32]
    shr	ecx, 6
    xor	ecx, edi
    mov	edi, dword [esp + 4]
    lea	edx, [edi + 9]
    and	edx, 15
    add	ebx, dword [esp + 8*edx + 144]
    adc	eax, dword [esp + 8*edx + 148]
    mov	edx, edi
    and	edx, 15
    add	ebx, dword [esp + 8*edx + 144]
    adc	eax, dword [esp + 8*edx + 148]
    add	ebx, esi
    adc	eax, ecx
    mov	dword [esp + 8*edx + 144], ebx
    mov	dword [esp + 8*edx + 148], eax
LBB1_9:
    mov	dword [esp + 32], edx
    mov	esi, dword [esp + 20]
    mov	ecx, esi
    mov	edi, dword [esp + 28]
    shld	ecx, edi, 18
    mov	eax, esi
    shld	eax, edi, 14
    xor	eax, ecx
    mov	ecx, edi
    shld	ecx, esi, 18
    mov	edx, edi
    shld	edx, esi, 14
    xor	edx, ecx
    mov	ecx, esi
    mov	ebx, esi
    shld	ecx, edi, 23
    xor	ecx, edx
    mov	esi, edi
    mov	edx, ebx
    mov	dword [esp + 20], ebx
    shld	esi, ebx, 23
    xor	esi, eax
    mov	ebx, dword [esp + 12]
    xor	ebx, dword [esp + 52]
    and	ebx, edx
    mov	edx, dword [esp + 68]
    mov	eax, edx
    xor	eax, dword [esp + 40]
    and	eax, dword [esp + 28]
    xor	eax, edx
    xor	ebx, dword [esp + 12]
    add	ebx, dword [esp + 16]
    adc	eax, dword [esp]
    add	ebx, ecx
    adc	eax, esi
    mov	ecx, dword [esp + 4]
    add	ebx, dword [8*ecx + _K]
    adc	eax, dword [8*ecx + _K+4]
    mov	ecx, dword [esp + 32]
    add	ebx, dword [esp + 8*ecx + 144]
    adc	eax, dword [esp + 8*ecx + 148]
    mov	esi, dword [esp + 36]
    mov	edx, esi
    mov	edi, dword [esp + 8]
    shld	edx, edi, 4
    mov	ecx, edi
    shld	ecx, esi, 30
    xor	ecx, edx
    shld	edi, esi, 4
    mov	dword [esp], edi
    mov	edi, esi
    mov	edx, dword [esp + 8]
    shld	edi, edx, 30
    xor	edi, dword [esp]
    mov	dword [esp], esi
    mov	edx, dword [esp + 8]
    shld	dword [esp], edx, 25
    xor	dword [esp], edi
    mov	edi, edx
    shld	edi, esi, 25
    xor	edi, ecx
    mov	dword [esp + 16], edi
    mov	ecx, esi
    mov	edi, dword [esp + 56]
    and	ecx, edi
    mov	edx, esi
    or	edx, edi
    and	edx, dword [esp + 44]
    or	edx, ecx
    mov	esi, dword [esp + 8]
    mov	edi, esi
    and	edi, dword [esp + 24]
    mov	ecx, esi
    or	ecx, dword [esp + 24]
    and	ecx, dword [esp + 48]
    or	ecx, edi
    add	edx, dword [esp]
    adc	ecx, dword [esp + 16]
    mov	edi, dword [esp + 60]
    add	edi, ebx
    mov	esi, dword [esp + 64]
    adc	esi, eax
    add	edx, ebx
    adc	ecx, eax
    mov	eax, dword [esp + 20]
    mov	dword [esp + 4], eax
    mov	eax, dword [esp + 28]
    mov	ebx, dword [esp + 12]
    mov	dword [esp + 16], ebx
    mov	ebx, dword [esp + 68]
    mov	dword [esp], ebx
    mov	ebx, dword [esp + 40]
    mov	dword [esp + 20], edi
    mov	dword [esp + 28], esi
    mov	esi, dword [esp + 44]
    mov	dword [esp + 60], esi
    mov	esi, dword [esp + 48]
    mov	dword [esp + 64], esi
    mov	esi, dword [esp + 56]
    mov	dword [esp + 44], esi
    mov	esi, dword [esp + 24]
    mov	dword [esp + 48], esi
    mov	esi, dword [esp + 36]
    mov	dword [esp + 56], esi
    mov	esi, eax
    mov	eax, dword [esp + 8]
    mov	dword [esp + 24], eax
    mov	edi, edx
    mov	edx, dword [esp + 4]
    mov	dword [esp + 8], ecx
    mov	ecx, dword [esp + 72]
    jmp	LBB1_3
LBB1_4:
    push	-64
    pop	eax
    mov	esi, dword [esp + 76]
LBB1_5:
    test	eax, eax
    je	LBB1_10
    mov	ecx, dword [esp + 8]
    mov	dword [esp + 84], ecx
    mov	dword [esp + 80], edi
    mov	ecx, dword [esp + 24]
    mov	dword [esp + 92], ecx
    mov	ecx, dword [esp + 56]
    mov	dword [esp + 88], ecx
    mov	ecx, dword [esp + 48]
    mov	dword [esp + 100], ecx
    mov	ecx, dword [esp + 44]
    mov	dword [esp + 96], ecx
    mov	ecx, dword [esp + 64]
    mov	dword [esp + 108], ecx
    mov	ecx, dword [esp + 60]
    mov	dword [esp + 104], ecx
    mov	ecx, dword [esp + 28]
    mov	dword [esp + 116], ecx
    mov	ecx, dword [esp + 20]
    mov	dword [esp + 112], ecx
    mov	dword [esp + 124], ebx
    mov	ecx, dword [esp + 52]
    mov	dword [esp + 120], ecx
    mov	ecx, dword [esp + 68]
    mov	dword [esp + 132], ecx
    mov	ecx, dword [esp + 12]
    mov	dword [esp + 128], ecx
    mov	ecx, dword [esp]
    mov	dword [esp + 140], ecx
    mov	ecx, dword [esp + 16]
    mov	dword [esp + 136], ecx
    mov	ecx, dword [esp + eax + 148]
    mov	edx, dword [esp + eax + 144]
    add	dword [esi + eax + 64], edx
    adc	dword [esi + eax + 68], ecx
    add	eax, 8
    jmp	LBB1_5
LBB1_10:
    lea	esp, [ebp - 12]
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret
_store_be64:
    mov	eax, dword [esp + 4]
    bswap	edx
    mov	dword [ecx + 4], edx
    bswap	eax
    mov	dword [ecx], eax
    ret
_load_be32:
    mov	eax, dword [ecx]
    bswap	eax
    ret

section .rdata align=4
align 8
L_const_jit_sha384_st:
    dq -3766243637369397544
    dq 7105036623409894663
    dq -7973340178411365097
    dq 1526699215303891257
    dq 7436329637833083697
    dq -8163818279084223215
    dq -2662702644619276377
    dq 5167115440072839076
align 8
_K:
    dq 4794697086780616226
    dq 8158064640168781261
    dq -5349999486874862801
    dq -1606136188198331460
    dq 4131703408338449720
    dq 6480981068601479193
    dq -7908458776815382629
    dq -6116909921290321640
    dq -2880145864133508542
    dq 1334009975649890238
    dq 2608012711638119052
    dq 6128411473006802146
    dq 8268148722764581231
    dq -9160688886553864527
    dq -7215885187991268811
    dq -4495734319001033068
    dq -1973867731355612462
    dq -1171420211273849373
    dq 1135362057144423861
    dq 2597628984639134821
    dq 3308224258029322869
    dq 5365058923640841347
    dq 6679025012923562964
    dq 8573033837759648693
    dq -7476448914759557205
    dq -6327057829258317296
    dq -5763719355590565569
    dq -4658551843659510044
    dq -4116276920077217854
    dq -3051310485924567259
    dq 489312712824947311
    dq 1452737877330783856
    dq 2861767655752347644
    dq 3322285676063803686
    dq 5560940570517711597
    dq 5996557281743188959
    dq 7280758554555802590
    dq 8532644243296465576
    dq -9096487096722542874
    dq -7894198246740708037
    dq -6719396339535248540
    dq -6333637450476146687
    dq -4446306890439682159
    dq -4076793802049405392
    dq -3345356375505022440
    dq -2983346525034927856
    dq -860691631967231958
    dq 1182934255886127544
    dq 1847814050463011016
    dq 2177327727835720531
    dq 2830643537854262169
    dq 3796741975233480872
    dq 4115178125766777443
    dq 5681478168544905931
    dq 6601373596472566643
    dq 7507060721942968483
    dq 8399075790359081724
    dq 8693463985226723168
    dq -8878714635349349518
    dq -8302665154208450068
    dq -8016688836872298968
    dq -6606660893046293015
    dq -4685533653050689259
    dq -4147400797238176981
    dq -3880063495543823972
    dq -3348786107499101689
    dq -1523767162380948706
    dq -757361751448694408
    dq 500013540394364858
    dq 748580250866718886
    dq 1242879168328830382
    dq 1977374033974150939
    dq 2944078676154940804
    dq 3659926193048069267
    dq 4368137639120453308
    dq 4836135668995329356
    dq 5532061633213252278
    dq 6448918945643986474
    dq 6902733635092675308
    dq 7801388544844847127
_hex_alloc_lo:
    db 48,49,50,51,52,53,54,55,56,57,97,98,99,100,101,102
    db 0
