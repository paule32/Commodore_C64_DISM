; ---------------------------------------------------------------------------
; BLAKE2s-256, compact one-shot implementation for i386 / COFF32
;
; ABI:
;   char * __cdecl _jit_blake2(const char *text, int length)
;
; Result:
;   pointer to a static, zero-terminated 64-character lowercase hex string.
;
; Restrictions:
;   - unkeyed BLAKE2s-256 only
;   - not re-entrant / not thread-safe because the result buffer is static
;   - negative length and NIL input are treated as an empty message
; ---------------------------------------------------------------------------

bits 32

section .text

; Drop-in symbol used by dBase2Many's existing BLAKE2 builtin.
global _jit_blake2, jit_blake2

; Optional aliases for direct external declarations.
global Blake2sHex
global _Blake2sHex

; Main-frame local offsets.  EBX/ESI/EDI occupy [ebp-4..ebp-12].
%define HASH_H       -44                 ; 8 dwords
%define HASH_T0      -48
%define HASH_T1      -52
%define HASH_BLOCK  -116                 ; 64 bytes
%define HASH_LOCAL   104

; Compression-frame local offsets.
%define CMP_M        -76                 ; 16 dwords
%define CMP_V       -140                 ; 16 dwords
%define CMP_PA      -144
%define CMP_PB      -148
%define CMP_PC      -152
%define CMP_PD      -156
%define CMP_ROUND   -160
%define CMP_G       -164
%define CMP_SIGROW  -168
%define CMP_LOCAL    156

; ---------------------------------------------------------------------------
; char * __cdecl _jit_blake2(const char *text, int length)
; ---------------------------------------------------------------------------
_jit_blake2:
jit_blacke2:
Blake2sHex:
_Blake2sHex:
    push ebp
    mov  ebp, esp
    push ebx
    push esi
    push edi
    sub  esp, HASH_LOCAL

    ; h[0..7] = IV; h[0] ^= parameter block for digest=32,key=0,fanout=1,depth=1
    mov  esi, blake2s_iv
    lea  edi, [ebp + HASH_H]
    mov  ecx, 8
    rep  movsd
    xor  dword [ebp + HASH_H], 0x01010020

    mov  dword [ebp + HASH_T0], 0
    mov  dword [ebp + HASH_T1], 0

    mov  esi, [ebp + 8]                 ; input
    mov  ebx, [ebp + 12]                ; remaining length

    test ebx, ebx
    jns  .length_ok
    xor  ebx, ebx
.length_ok:
    test esi, esi
    jnz  .blocks
    xor  ebx, ebx

.blocks:
    ; Keep the final block (including a complete 64-byte block) uncompressed
    ; until it can be marked with the final-block flag.
    cmp  ebx, 64
    jbe  .final_block

    add  dword [ebp + HASH_T0], 64
    adc  dword [ebp + HASH_T1], 0

    push dword 0                         ; final = false
    push dword [ebp + HASH_T1]
    push dword [ebp + HASH_T0]
    push esi                             ; block
    lea  eax, [ebp + HASH_H]
    push eax                             ; h
    call blake2s_compress
    add  esp, 20

    add  esi, 64
    sub  ebx, 64
    jmp  .blocks

.final_block:
    ; Zero-pad the local final block.
    lea  edi, [ebp + HASH_BLOCK]
    xor  eax, eax
    mov  ecx, 16
    rep  stosd

    ; Copy 0..64 final bytes.
    test ebx, ebx
    jz   .final_ready
    lea  edi, [ebp + HASH_BLOCK]
    mov  ecx, ebx
    rep  movsb

.final_ready:
    add  dword [ebp + HASH_T0], ebx
    adc  dword [ebp + HASH_T1], 0

    push dword 1                         ; final = true
    push dword [ebp + HASH_T1]
    push dword [ebp + HASH_T0]
    lea  eax, [ebp + HASH_BLOCK]
    push eax                             ; block
    lea  eax, [ebp + HASH_H]
    push eax                             ; h
    call blake2s_compress
    add  esp, 20

    ; Encode the 32-byte little-endian digest as 64 lowercase hex digits.
    lea  esi, [ebp + HASH_H]
    mov  edi, blake2_hex_output
    mov  ecx, 32

.hex_loop:
    movzx eax, byte [esi]
    inc  esi
    mov  edx, eax
    shr  eax, 4
    and  edx, 15
    mov  al, [hex_digits + eax]
    mov  [edi], al
    mov  dl, [hex_digits + edx]
    mov  [edi + 1], dl
    add  edi, 2
    dec  ecx
    jnz  .hex_loop

    mov  byte [edi], 0
    mov  eax, blake2_hex_output

    add  esp, HASH_LOCAL
    pop  edi
    pop  esi
    pop  ebx
    pop  ebp
    ret

; ---------------------------------------------------------------------------
; void blake2s_compress(
;     uint32_t h[8], const uint8_t block[64],
;     uint32_t t0, uint32_t t1, uint32_t final)
; ---------------------------------------------------------------------------
blake2s_compress:
    push ebp
    mov  ebp, esp
    push ebx
    push esi
    push edi
    sub  esp, CMP_LOCAL

    ; m[0..15] = block words. x86 is little-endian, so a dword copy suffices.
    mov  esi, [ebp + 12]
    lea  edi, [ebp + CMP_M]
    mov  ecx, 16
    rep  movsd

    ; v[0..7] = h[0..7]
    mov  esi, [ebp + 8]
    lea  edi, [ebp + CMP_V]
    mov  ecx, 8
    rep  movsd

    ; v[8..15] = IV[0..7]
    mov  esi, blake2s_iv
    lea  edi, [ebp + CMP_V + 32]
    mov  ecx, 8
    rep  movsd

    mov  eax, [ebp + 16]
    xor  [ebp + CMP_V + 48], eax         ; v[12] ^= t0
    mov  eax, [ebp + 20]
    xor  [ebp + CMP_V + 52], eax         ; v[13] ^= t1

    cmp  dword [ebp + 24], 0
    je   .rounds_start
    not  dword [ebp + CMP_V + 56]        ; v[14] ^= 0xffffffff

.rounds_start:
    mov  dword [ebp + CMP_ROUND], 0

.round_loop:
    ; sigma row = sigma + round * 16
    mov  eax, [ebp + CMP_ROUND]
    shl  eax, 4
    add  eax, blake2s_sigma
    mov  [ebp + CMP_SIGROW], eax

    mov  dword [ebp + CMP_G], 0

.g_loop:
    ; Build pointers to v[a], v[b], v[c], v[d] from the compact table.
    mov  eax, [ebp + CMP_G]
    shl  eax, 2
    add  eax, blake2s_g_positions
    mov  edi, eax

    movzx esi, byte [edi]
    lea  esi, [ebp + esi * 4 + CMP_V]
    mov  [ebp + CMP_PA], esi

    movzx esi, byte [edi + 1]
    lea  esi, [ebp + esi * 4 + CMP_V]
    mov  [ebp + CMP_PB], esi

    movzx esi, byte [edi + 2]
    lea  esi, [ebp + esi * 4 + CMP_V]
    mov  [ebp + CMP_PC], esi

    movzx esi, byte [edi + 3]
    lea  esi, [ebp + esi * 4 + CMP_V]
    mov  [ebp + CMP_PD], esi

    ; Load a,b,c,d into eax,ebx,ecx,edx.
    mov  esi, [ebp + CMP_PA]
    mov  eax, [esi]
    mov  esi, [ebp + CMP_PB]
    mov  ebx, [esi]
    mov  esi, [ebp + CMP_PC]
    mov  ecx, [esi]
    mov  esi, [ebp + CMP_PD]
    mov  edx, [esi]

    ; EDI points to the two sigma indices used by this G invocation.
    mov  edi, [ebp + CMP_SIGROW]
    mov  esi, [ebp + CMP_G]
    lea  edi, [edi + esi * 2]

    ; G(a,b,c,d,x,y)
    add  eax, ebx
    movzx esi, byte [edi]
    add  eax, [ebp + esi * 4 + CMP_M]
    xor  edx, eax
    ror  edx, 16

    add  ecx, edx
    xor  ebx, ecx
    ror  ebx, 12

    add  eax, ebx
    movzx esi, byte [edi + 1]
    add  eax, [ebp + esi * 4 + CMP_M]
    xor  edx, eax
    ror  edx, 8

    add  ecx, edx
    xor  ebx, ecx
    ror  ebx, 7

    ; Store the updated a,b,c,d words.
    mov  esi, [ebp + CMP_PA]
    mov  [esi], eax
    mov  esi, [ebp + CMP_PB]
    mov  [esi], ebx
    mov  esi, [ebp + CMP_PC]
    mov  [esi], ecx
    mov  esi, [ebp + CMP_PD]
    mov  [esi], edx

    inc  dword [ebp + CMP_G]
    cmp  dword [ebp + CMP_G], 8
    jb   .g_loop

    inc  dword [ebp + CMP_ROUND]
    cmp  dword [ebp + CMP_ROUND], 10
    jb   .round_loop

    ; h[i] ^= v[i] ^ v[i+8]
    mov  edi, [ebp + 8]
    xor  esi, esi

.finish_loop:
    mov  eax, [ebp + esi * 4 + CMP_V]
    xor  eax, [ebp + esi * 4 + CMP_V + 32]
    xor  [edi + esi * 4], eax
    inc  esi
    cmp  esi, 8
    jb   .finish_loop

    add  esp, CMP_LOCAL
    pop  edi
    pop  esi
    pop  ebx
    pop  ebp
    ret

section .rdata align=4

blake2s_iv:
    dd 0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A
    dd 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19

; Ten BLAKE2s message permutations, RFC 7693.
blake2s_sigma:
    db  0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15
    db 14,10, 4, 8, 9,15,13, 6, 1,12, 0, 2,11, 7, 5, 3
    db 11, 8,12, 0, 5, 2,15,13,10,14, 3, 6, 7, 1, 9, 4
    db  7, 9, 3, 1,13,12,11,14, 2, 6, 5,10, 4, 0,15, 8
    db  9, 0, 5, 7, 2, 4,10,15,14, 1,11,12, 6, 8, 3,13
    db  2,12, 6,10, 0,11, 8, 3, 4,13, 7, 5,15,14, 1, 9
    db 12, 5, 1,15,14,13, 4,10, 0, 7, 6, 3, 9, 2, 8,11
    db 13,11, 7,14,12, 1, 3, 9, 5, 0,15, 4, 8, 6, 2,10
    db  6,15,14, 9,11, 3, 0, 8,12, 2,13, 7, 1, 4,10, 5
    db 10, 2, 8, 4, 7, 6, 1, 5,15,11, 9,14, 3,12,13, 0

; Four column G calls followed by four diagonal G calls.
blake2s_g_positions:
    db 0,4, 8,12
    db 1,5, 9,13
    db 2,6,10,14
    db 3,7,11,15
    db 0,5,10,15
    db 1,6,11,12
    db 2,7, 8,13
    db 3,4, 9,14

hex_digits:
    db '0123456789abcdef'

section .bss align=4

blake2_hex_output:
    resb 65
