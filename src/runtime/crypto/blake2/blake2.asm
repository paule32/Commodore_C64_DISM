; Auto-generated from size-optimized i386 code (-Oz, -march=i386).
; NASM syntax, Win32 COFF, cdecl public wrapper.
bits 32

global __jit_blake2


section .text align=1
__jit_blake2:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 128
    mov	edi, dword [esp + 152]
    test	edi, edi
    js	LBB0_2
    mov	ebx, dword [esp + 148]
    test	ebx, ebx
    setne	al
    test	edi, edi
    sete	cl
    or	cl, al
    jne	LBB0_3
LBB0_2:
    xor	edi, edi
    xor	ebx, ebx
LBB0_3:
    push	-32
    pop	eax
LBB0_4:
    test	eax, eax
    je	LBB0_6
    mov	ecx, dword [eax + _IV+32]
    mov	dword [esp + eax + 32], ecx
    add	eax, 4
    jmp	LBB0_4
LBB0_6:
    mov	eax, esp
    xor	dword [eax], 16842784
    xor	eax, eax
    xor	ebp, ebp
LBB0_7:
    cmp	edi, 64
    jbe	LBB0_8
    lea	edx, [ebx + eax]
    lea	esi, [eax + 64]
    xor	ecx, ecx
    cmp	eax, -64
    sete	cl
    add	ebp, ecx
    mov	ecx, esp
    push	0
    push	ebp
    push	esi
    call	_compress
    add	esp, 12
    add	edi, -64
    mov	eax, esi
    jmp	LBB0_7
LBB0_8:
    push	-64
    pop	ecx
LBB0_9:
    test	ecx, ecx
    je	LBB0_11
    mov	byte [esp + ecx + 128], 0
    inc	ecx
    jmp	LBB0_9
LBB0_11:
    test	edi, edi
    je	LBB0_15
    xor	ecx, ecx
LBB0_13:
    cmp	edi, ecx
    je	LBB0_15
    lea	edx, [ebx + ecx]
    mov	dl, byte [edx + eax]
    mov	byte [esp + ecx + 64], dl
    inc	ecx
    jmp	LBB0_13
LBB0_15:
    add	edi, eax
    adc	ebp, 0
    mov	ecx, esp
    lea	edx, [esp + 64]
    push	-1
    push	ebp
    push	edi
    call	_compress
    add	esp, 12
    push	-32
    pop	eax
LBB0_16:
    test	eax, eax
    je	LBB0_17
    mov	ecx, dword [esp + eax + 32]
    mov	dword [esp + eax + 64], ecx
    add	eax, 4
    jmp	LBB0_16
LBB0_17:
    push	-32
    pop	eax
LBB0_18:
    test	eax, eax
    je	LBB0_20
    movzx	ecx, byte [esp + eax + 64]
    mov	edx, ecx
    shr	edx, 4
    mov	dl, byte [edx + _jit_blake2_hex]
    mov	byte [eax + eax + _result+64], dl
    and	ecx, 15
    mov	cl, byte [ecx + _jit_blake2_hex]
    mov	byte [eax + eax + _result+65], cl
    inc	eax
    jmp	LBB0_18
LBB0_20:
    mov	byte [_result+64], 0
    mov	eax, _result
    add	esp, 128
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret
_compress:
    push	ebp
    push	ebx
    push	edi
    push	esi
    sub	esp, 200
    mov	edi, dword [esp + 228]
    mov	eax, dword [esp + 224]
    mov	dword [esp + 12], eax
    mov	eax, dword [esp + 220]
    mov	dword [esp + 8], eax
    push	-64
    pop	eax
LBB1_1:
    test	eax, eax
    je	LBB1_2
    mov	esi, dword [edx + eax + 64]
    mov	dword [esp + eax + 200], esi
    add	eax, 4
    jmp	LBB1_1
LBB1_2:
    push	-32
    pop	eax
LBB1_3:
    test	eax, eax
    je	LBB1_5
    mov	edx, dword [ecx + eax + 32]
    mov	dword [esp + eax + 100], edx
    mov	edx, dword [eax + _IV+32]
    mov	dword [esp + eax + 132], edx
    add	eax, 4
    jmp	LBB1_3
LBB1_5:
    mov	dword [esp + 132], ecx
    mov	eax, dword [esp + 8]
    xor	eax, dword [esp + 116]
    mov	dword [esp + 8], eax
    mov	eax, dword [esp + 12]
    xor	eax, dword [esp + 120]
    mov	dword [esp + 12], eax
    xor	edi, dword [esp + 124]
    mov	dword [esp + 32], edi
    mov	eax, dword [esp + 68]
    mov	dword [esp + 36], eax
    mov	eax, dword [esp + 72]
    mov	dword [esp + 40], eax
    mov	ebx, dword [esp + 84]
    mov	eax, dword [esp + 100]
    mov	dword [esp + 16], eax
    mov	eax, dword [esp + 88]
    mov	dword [esp + 20], eax
    mov	ecx, dword [esp + 104]
    mov	eax, dword [esp + 76]
    mov	dword [esp + 44], eax
    mov	eax, dword [esp + 92]
    mov	dword [esp + 56], eax
    mov	eax, dword [esp + 108]
    mov	dword [esp + 28], eax
    mov	eax, dword [esp + 80]
    mov	dword [esp + 48], eax
    mov	eax, dword [esp + 96]
    mov	dword [esp + 52], eax
    mov	eax, dword [esp + 128]
    mov	dword [esp + 60], eax
    mov	edx, -160
    mov	eax, dword [esp + 112]
    mov	dword [esp + 24], eax
LBB1_6:
    test	edx, edx
    je	LBB1_7
    mov	esi, dword [esp + 36]
    add	esi, ebx
    mov	dword [esp + 4], ebx
    movzx	ebx, byte [edx + _SIGMA+160]
    add	esi, dword [esp + 4*ebx + 136]
    mov	eax, dword [esp + 8]
    xor	eax, esi
    rol	eax, 16
    mov	edi, dword [esp + 16]
    add	edi, eax
    xor	dword [esp + 4], edi
    rol	dword [esp + 4], 20
    add	esi, dword [esp + 4]
    movzx	ebx, byte [edx + _SIGMA+161]
    add	esi, dword [esp + 4*ebx + 136]
    mov	dword [esp + 36], esi
    xor	eax, esi
    rol	eax, 24
    mov	dword [esp + 8], eax
    add	edi, eax
    mov	dword [esp + 16], edi
    xor	dword [esp + 4], edi
    rol	dword [esp + 4], 25
    mov	esi, dword [esp + 40]
    mov	edi, dword [esp + 20]
    add	esi, edi
    movzx	ebx, byte [edx + _SIGMA+162]
    add	esi, dword [esp + 4*ebx + 136]
    mov	eax, dword [esp + 12]
    xor	eax, esi
    rol	eax, 16
    add	ecx, eax
    xor	edi, ecx
    rol	edi, 20
    add	esi, edi
    movzx	ebx, byte [edx + _SIGMA+163]
    add	esi, dword [esp + 4*ebx + 136]
    mov	dword [esp + 40], esi
    xor	eax, esi
    rol	eax, 24
    mov	dword [esp + 12], eax
    add	ecx, eax
    mov	dword [esp + 64], ecx
    xor	edi, ecx
    rol	edi, 25
    mov	dword [esp + 20], edi
    mov	ebp, dword [esp + 56]
    mov	ecx, dword [esp + 44]
    add	ecx, ebp
    movzx	ebx, byte [edx + _SIGMA+164]
    add	ecx, dword [esp + 4*ebx + 136]
    mov	dword [esp], edx
    mov	eax, dword [esp + 32]
    xor	eax, ecx
    rol	eax, 16
    mov	edx, dword [esp + 28]
    add	edx, eax
    xor	ebp, edx
    rol	ebp, 20
    add	ecx, ebp
    mov	esi, dword [esp]
    movzx	ebx, byte [esi + _SIGMA+165]
    add	ecx, dword [esp + 4*ebx + 136]
    mov	dword [esp + 44], ecx
    xor	eax, ecx
    rol	eax, 24
    mov	dword [esp + 32], eax
    add	edx, eax
    mov	dword [esp + 28], edx
    xor	ebp, edx
    rol	ebp, 25
    mov	edx, dword [esp + 52]
    mov	edi, dword [esp + 48]
    add	edi, edx
    mov	esi, dword [esp]
    movzx	ebx, byte [esi + _SIGMA+166]
    add	edi, dword [esp + 4*ebx + 136]
    mov	esi, edi
    mov	edi, dword [esp + 60]
    xor	edi, esi
    rol	edi, 16
    mov	eax, dword [esp + 24]
    add	eax, edi
    xor	edx, eax
    rol	edx, 20
    add	esi, edx
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+167]
    add	esi, dword [esp + 4*ebx + 136]
    xor	edi, esi
    rol	edi, 24
    add	eax, edi
    mov	dword [esp + 24], eax
    xor	edx, eax
    rol	edx, 25
    mov	eax, dword [esp + 20]
    mov	ecx, dword [esp + 36]
    add	ecx, eax
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+168]
    add	ecx, dword [esp + 4*ebx + 136]
    mov	ebx, ecx
    xor	edi, ecx
    rol	edi, 16
    add	dword [esp + 28], edi
    xor	eax, dword [esp + 28]
    rol	eax, 20
    mov	dword [esp + 20], eax
    add	ebx, eax
    mov	eax, ebx
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+169]
    add	eax, dword [esp + 4*ebx + 136]
    mov	dword [esp + 36], eax
    mov	eax, dword [esp + 40]
    add	eax, ebp
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+170]
    add	eax, dword [esp + 4*ebx + 136]
    mov	ebx, dword [esp + 8]
    xor	ebx, eax
    rol	ebx, 16
    mov	dword [esp + 8], ebx
    mov	ecx, dword [esp + 24]
    add	ecx, ebx
    mov	dword [esp + 24], ecx
    xor	ebp, ecx
    rol	ebp, 20
    add	eax, ebp
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+171]
    add	eax, dword [esp + 4*ebx + 136]
    mov	dword [esp + 40], eax
    mov	ecx, dword [esp + 44]
    add	ecx, edx
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+172]
    add	ecx, dword [esp + 4*ebx + 136]
    mov	ebx, dword [esp + 12]
    xor	ebx, ecx
    rol	ebx, 16
    mov	eax, ebx
    mov	dword [esp + 12], ebx
    mov	ebx, dword [esp + 16]
    add	ebx, eax
    mov	dword [esp + 16], ebx
    xor	edx, ebx
    rol	edx, 20
    add	ecx, edx
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+173]
    add	ecx, dword [esp + 4*ebx + 136]
    add	esi, dword [esp + 4]
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+174]
    add	esi, dword [esp + 4*ebx + 136]
    mov	eax, dword [esp + 32]
    xor	eax, esi
    rol	eax, 16
    mov	dword [esp + 32], eax
    add	dword [esp + 64], eax
    mov	ebx, dword [esp + 4]
    xor	ebx, dword [esp + 64]
    mov	dword [esp + 4], ebx
    rol	dword [esp + 4], 20
    add	esi, dword [esp + 4]
    mov	ebx, dword [esp]
    movzx	ebx, byte [ebx + _SIGMA+175]
    add	esi, dword [esp + 4*ebx + 136]
    xor	edi, dword [esp + 36]
    rol	edi, 24
    mov	dword [esp + 60], edi
    add	dword [esp + 28], edi
    mov	edi, esi
    mov	esi, dword [esp + 20]
    xor	esi, dword [esp + 28]
    rol	esi, 25
    mov	dword [esp + 20], esi
    mov	esi, dword [esp + 8]
    xor	esi, dword [esp + 40]
    rol	esi, 24
    mov	dword [esp + 8], esi
    mov	eax, dword [esp + 24]
    add	eax, esi
    mov	dword [esp + 24], eax
    xor	ebp, eax
    rol	ebp, 25
    mov	dword [esp + 56], ebp
    mov	dword [esp + 44], ecx
    mov	esi, dword [esp + 12]
    xor	esi, ecx
    mov	ecx, dword [esp + 64]
    rol	esi, 24
    mov	dword [esp + 12], esi
    mov	eax, dword [esp + 16]
    add	eax, esi
    mov	dword [esp + 16], eax
    xor	edx, eax
    rol	edx, 25
    mov	dword [esp + 52], edx
    mov	ebx, dword [esp + 4]
    mov	dword [esp + 48], edi
    mov	eax, dword [esp + 32]
    xor	eax, edi
    rol	eax, 24
    mov	dword [esp + 32], eax
    add	ecx, eax
    mov	edx, dword [esp]
    xor	ebx, ecx
    rol	ebx, 25
    add	edx, 16
    jmp	LBB1_6
LBB1_7:
    mov	eax, dword [esp + 36]
    mov	dword [esp + 68], eax
    mov	dword [esp + 84], ebx
    mov	eax, dword [esp + 8]
    mov	dword [esp + 116], eax
    mov	eax, dword [esp + 16]
    mov	dword [esp + 100], eax
    mov	eax, dword [esp + 40]
    mov	dword [esp + 72], eax
    mov	eax, dword [esp + 20]
    mov	dword [esp + 88], eax
    mov	eax, dword [esp + 12]
    mov	dword [esp + 120], eax
    mov	dword [esp + 104], ecx
    mov	eax, dword [esp + 44]
    mov	dword [esp + 76], eax
    mov	eax, dword [esp + 56]
    mov	dword [esp + 92], eax
    mov	eax, dword [esp + 32]
    mov	dword [esp + 124], eax
    mov	eax, dword [esp + 28]
    mov	dword [esp + 108], eax
    mov	eax, dword [esp + 48]
    mov	dword [esp + 80], eax
    mov	eax, dword [esp + 52]
    mov	dword [esp + 96], eax
    mov	eax, dword [esp + 60]
    mov	dword [esp + 128], eax
    mov	eax, dword [esp + 24]
    mov	dword [esp + 112], eax
    push	-32
    pop	eax
    mov	edx, dword [esp + 132]
LBB1_8:
    test	eax, eax
    je	LBB1_10
    mov	ecx, dword [esp + eax + 132]
    xor	ecx, dword [esp + eax + 100]
    xor	dword [edx + eax + 32], ecx
    add	eax, 4
    jmp	LBB1_8
LBB1_10:
    add	esp, 200
    pop	esi
    pop	edi
    pop	ebx
    pop	ebp
    ret

section .rdata align=4
_jit_blake2_hex:
    db 48,49,50,51,52,53,54,55,56,57,97,98,99,100,101,102
    db 0
align 4
_IV:
    dd 1779033703
    dd 3144134277
    dd 1013904242
    dd 2773480762
    dd 1359893119
    dd 2600822924
    dd 528734635
    dd 1541459225
_SIGMA:
    db 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
    db 14,10,4,8,9,15,13,6,1,12,0,2,11,7,5,3
    db 11,8,12,0,5,2,15,13,10,14,3,6,7,1,9,4
    db 7,9,3,1,13,12,11,14,2,6,5,10,4,0,15,8
    db 9,0,5,7,2,4,10,15,14,1,11,12,6,8,3,13
    db 2,12,6,10,0,11,8,3,4,13,7,5,15,14,1,9
    db 12,5,1,15,14,13,4,10,0,7,6,3,9,2,8,11
    db 13,11,7,14,12,1,3,9,5,0,15,4,8,6,2,10
    db 6,15,14,9,11,3,0,8,12,2,13,7,1,4,10,5
    db 10,2,8,4,7,6,1,5,15,11,9,14,3,12,13,0

; ---------------------------------------------------------------------------
; Statischer Hex-Ausgabepuffer.
; .bss belegt Speicher zur Laufzeit, aber keine initialisierten 65 Bytes
; in der COFF-Objektdatei.
; ---------------------------------------------------------------------------
section .bss align=1
_result:
    resb 65
