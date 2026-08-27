; ---------------------------------------------------------------------------
; File:   sha512_small.asm
; Target: i386 / Win32 COFF
; Syntax: NASM
;
; Compact one-shot SHA-512 implementation for dBase2Many.
;
; C ABI:
;   char* __cdecl _jit_sha512(char* text, int length);
;
; Returns a heap allocated, zero terminated string containing 128 lowercase
; hexadecimal characters.  The allocation is obtained through _jit_malloc.
;
; Notes:
;   * Pure 32-bit integer implementation; no SSE/MMX required.
;   * Only the one-shot API is exported to keep the object small.
;   * The SHA-512 message schedule uses a 16-word ring buffer.
; ---------------------------------------------------------------------------

bits 32

section .text align=1

extern __jit_malloc
global __jit_sha512

; ---------------------------------------------------------------------------
; Rotate EDX:EAX right by CL bits (0..63).
; Clobbers EBX, ECX.
; ---------------------------------------------------------------------------
sha512_rotr64:
    and     ecx, 63
    jz      .done
    cmp     cl, 32
    jb      .lt32
    xchg    eax, edx
    sub     cl, 32
    jz      .done
.lt32:
    mov     ebx, eax
    shrd    eax, edx, cl
    shrd    edx, ebx, cl
.done:
    ret

; ---------------------------------------------------------------------------
; SHA-512 small sigma 0:
;   ROTR1(x) xor ROTR8(x) xor SHR7(x)
; Input/output: EDX:EAX
; ---------------------------------------------------------------------------
sha512_ssig0:
    push    ebp
    mov     ebp, esp
    sub     esp, 16

    mov     [ebp-8], eax
    mov     [ebp-4], edx

    mov     ecx, 1
    call    sha512_rotr64
    mov     [ebp-16], eax
    mov     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 8
    call    sha512_rotr64
    xor     [ebp-16], eax
    xor     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 7
    shrd    eax, edx, cl
    shr     edx, cl
    xor     eax, [ebp-16]
    xor     edx, [ebp-12]

    leave
    ret

; ---------------------------------------------------------------------------
; SHA-512 small sigma 1:
;   ROTR19(x) xor ROTR61(x) xor SHR6(x)
; Input/output: EDX:EAX
; ---------------------------------------------------------------------------
sha512_ssig1:
    push    ebp
    mov     ebp, esp
    sub     esp, 16

    mov     [ebp-8], eax
    mov     [ebp-4], edx

    mov     ecx, 19
    call    sha512_rotr64
    mov     [ebp-16], eax
    mov     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 61
    call    sha512_rotr64
    xor     [ebp-16], eax
    xor     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 6
    shrd    eax, edx, cl
    shr     edx, cl
    xor     eax, [ebp-16]
    xor     edx, [ebp-12]

    leave
    ret

; ---------------------------------------------------------------------------
; SHA-512 big sigma 0:
;   ROTR28(x) xor ROTR34(x) xor ROTR39(x)
; Input/output: EDX:EAX
; ---------------------------------------------------------------------------
sha512_bsig0:
    push    ebp
    mov     ebp, esp
    sub     esp, 16

    mov     [ebp-8], eax
    mov     [ebp-4], edx

    mov     ecx, 28
    call    sha512_rotr64
    mov     [ebp-16], eax
    mov     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 34
    call    sha512_rotr64
    xor     [ebp-16], eax
    xor     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 39
    call    sha512_rotr64
    xor     eax, [ebp-16]
    xor     edx, [ebp-12]

    leave
    ret

; ---------------------------------------------------------------------------
; SHA-512 big sigma 1:
;   ROTR14(x) xor ROTR18(x) xor ROTR41(x)
; Input/output: EDX:EAX
; ---------------------------------------------------------------------------
sha512_bsig1:
    push    ebp
    mov     ebp, esp
    sub     esp, 16

    mov     [ebp-8], eax
    mov     [ebp-4], edx

    mov     ecx, 14
    call    sha512_rotr64
    mov     [ebp-16], eax
    mov     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 18
    call    sha512_rotr64
    xor     [ebp-16], eax
    xor     [ebp-12], edx

    mov     eax, [ebp-8]
    mov     edx, [ebp-4]
    mov     ecx, 41
    call    sha512_rotr64
    xor     eax, [ebp-16]
    xor     edx, [ebp-12]

    leave
    ret

; ---------------------------------------------------------------------------
; Compress one 128-byte block.
;
; cdecl:
;   [ebp+8]  = uint64_t state[8]
;   [ebp+12] = const uint8_t block[128]
;
; Local layout:
;   -128 ..   -1  W[16]
;   -192 .. -129  v[8]
;   -200 .. -193  t1
;   -208 .. -201  t2
;   -212          round index
; ---------------------------------------------------------------------------
sha512_compress:
    push    ebp
    mov     ebp, esp
    sub     esp, 224
    push    ebx
    push    esi
    push    edi

%define WBASE   -128
%define VBASE   -192
%define T1BASE  -200
%define T2BASE  -208
%define RIDX    -212

    ; Load the first 16 words as big-endian 64-bit values.
    mov     esi, [ebp+12]
    lea     edi, [ebp+WBASE]
    mov     ecx, 16
.load_w:
    mov     edx, [esi]
    mov     eax, [esi+4]
    bswap   edx
    bswap   eax
    mov     [edi], eax
    mov     [edi+4], edx
    add     esi, 8
    add     edi, 8
    dec     ecx
    jnz     .load_w

    ; v[0..7] = state[0..7]
    mov     esi, [ebp+8]
    lea     edi, [ebp+VBASE]
    mov     ecx, 16
    rep     movsd

    mov     dword [ebp+RIDX], 0

.round_loop:
    mov     ebx, [ebp+RIDX]
    cmp     ebx, 16
    jb      .schedule_ready

    ; s1(W[(t-2) & 15])
    mov     ecx, ebx
    sub     ecx, 2
    and     ecx, 15
    mov     eax, [ebp+WBASE+ecx*8]
    mov     edx, [ebp+WBASE+ecx*8+4]
    call    sha512_ssig1
    mov     [ebp+T1BASE], eax
    mov     [ebp+T1BASE+4], edx

    ; + W[(t-7) & 15]
    mov     ecx, [ebp+RIDX]
    sub     ecx, 7
    and     ecx, 15
    mov     eax, [ebp+WBASE+ecx*8]
    mov     edx, [ebp+WBASE+ecx*8+4]
    add     [ebp+T1BASE], eax
    adc     [ebp+T1BASE+4], edx

    ; + s0(W[(t-15) & 15])
    mov     ecx, [ebp+RIDX]
    sub     ecx, 15
    and     ecx, 15
    mov     eax, [ebp+WBASE+ecx*8]
    mov     edx, [ebp+WBASE+ecx*8+4]
    call    sha512_ssig0
    add     [ebp+T1BASE], eax
    adc     [ebp+T1BASE+4], edx

    ; + old W[t & 15], then replace the ring slot.
    mov     ecx, [ebp+RIDX]
    and     ecx, 15
    mov     eax, [ebp+WBASE+ecx*8]
    mov     edx, [ebp+WBASE+ecx*8+4]
    add     eax, [ebp+T1BASE]
    adc     edx, [ebp+T1BASE+4]
    mov     [ebp+WBASE+ecx*8], eax
    mov     [ebp+WBASE+ecx*8+4], edx

.schedule_ready:
    ; t1 = h
    mov     eax, [ebp+VBASE+7*8]
    mov     edx, [ebp+VBASE+7*8+4]
    mov     [ebp+T1BASE], eax
    mov     [ebp+T1BASE+4], edx

    ; t1 += BSIG1(e)
    mov     eax, [ebp+VBASE+4*8]
    mov     edx, [ebp+VBASE+4*8+4]
    call    sha512_bsig1
    add     [ebp+T1BASE], eax
    adc     [ebp+T1BASE+4], edx

    ; t1 += Ch(e,f,g) = g xor (e and (f xor g))
    mov     eax, [ebp+VBASE+5*8]
    xor     eax, [ebp+VBASE+6*8]
    and     eax, [ebp+VBASE+4*8]
    xor     eax, [ebp+VBASE+6*8]

    mov     edx, [ebp+VBASE+5*8+4]
    xor     edx, [ebp+VBASE+6*8+4]
    and     edx, [ebp+VBASE+4*8+4]
    xor     edx, [ebp+VBASE+6*8+4]

    add     [ebp+T1BASE], eax
    adc     [ebp+T1BASE+4], edx

    ; t1 += K[t]
    mov     ecx, [ebp+RIDX]
    mov     eax, [sha512_k+ecx*8]
    mov     edx, [sha512_k+ecx*8+4]
    add     [ebp+T1BASE], eax
    adc     [ebp+T1BASE+4], edx

    ; t1 += W[t & 15]
    and     ecx, 15
    mov     eax, [ebp+WBASE+ecx*8]
    mov     edx, [ebp+WBASE+ecx*8+4]
    add     [ebp+T1BASE], eax
    adc     [ebp+T1BASE+4], edx

    ; t2 = BSIG0(a)
    mov     eax, [ebp+VBASE]
    mov     edx, [ebp+VBASE+4]
    call    sha512_bsig0
    mov     [ebp+T2BASE], eax
    mov     [ebp+T2BASE+4], edx

    ; t2 += Maj(a,b,c) = (a & b) | (c & (a | b))
    mov     eax, [ebp+VBASE]
    mov     ebx, [ebp+VBASE+1*8]
    mov     ecx, eax
    and     ecx, ebx
    or      eax, ebx
    and     eax, [ebp+VBASE+2*8]
    or      eax, ecx

    mov     edx, [ebp+VBASE+4]
    mov     ebx, [ebp+VBASE+1*8+4]
    mov     ecx, edx
    and     ecx, ebx
    or      edx, ebx
    and     edx, [ebp+VBASE+2*8+4]
    or      edx, ecx

    add     [ebp+T2BASE], eax
    adc     [ebp+T2BASE+4], edx

    ; h = g
    mov     eax, [ebp+VBASE+6*8]
    mov     edx, [ebp+VBASE+6*8+4]
    mov     [ebp+VBASE+7*8], eax
    mov     [ebp+VBASE+7*8+4], edx

    ; g = f
    mov     eax, [ebp+VBASE+5*8]
    mov     edx, [ebp+VBASE+5*8+4]
    mov     [ebp+VBASE+6*8], eax
    mov     [ebp+VBASE+6*8+4], edx

    ; f = e
    mov     eax, [ebp+VBASE+4*8]
    mov     edx, [ebp+VBASE+4*8+4]
    mov     [ebp+VBASE+5*8], eax
    mov     [ebp+VBASE+5*8+4], edx

    ; e = d + t1
    mov     eax, [ebp+VBASE+3*8]
    mov     edx, [ebp+VBASE+3*8+4]
    add     eax, [ebp+T1BASE]
    adc     edx, [ebp+T1BASE+4]
    mov     [ebp+VBASE+4*8], eax
    mov     [ebp+VBASE+4*8+4], edx

    ; d = c
    mov     eax, [ebp+VBASE+2*8]
    mov     edx, [ebp+VBASE+2*8+4]
    mov     [ebp+VBASE+3*8], eax
    mov     [ebp+VBASE+3*8+4], edx

    ; c = b
    mov     eax, [ebp+VBASE+1*8]
    mov     edx, [ebp+VBASE+1*8+4]
    mov     [ebp+VBASE+2*8], eax
    mov     [ebp+VBASE+2*8+4], edx

    ; b = a
    mov     eax, [ebp+VBASE]
    mov     edx, [ebp+VBASE+4]
    mov     [ebp+VBASE+1*8], eax
    mov     [ebp+VBASE+1*8+4], edx

    ; a = t1 + t2
    mov     eax, [ebp+T1BASE]
    mov     edx, [ebp+T1BASE+4]
    add     eax, [ebp+T2BASE]
    adc     edx, [ebp+T2BASE+4]
    mov     [ebp+VBASE], eax
    mov     [ebp+VBASE+4], edx

    inc     dword [ebp+RIDX]
    cmp     dword [ebp+RIDX], 80
    jb      .round_loop

    ; state[i] += v[i]
    mov     esi, [ebp+8]
    lea     edi, [ebp+VBASE]
    mov     ecx, 8
.add_state:
    mov     eax, [edi]
    mov     edx, [edi+4]
    add     [esi], eax
    adc     [esi+4], edx
    add     esi, 8
    add     edi, 8
    dec     ecx
    jnz     .add_state

    pop     edi
    pop     esi
    pop     ebx
    mov     esp, ebp
    pop     ebp
    ret

%undef WBASE
%undef VBASE
%undef T1BASE
%undef T2BASE
%undef RIDX

; ---------------------------------------------------------------------------
; char* __cdecl _jit_sha512(char* text, int length)
; ---------------------------------------------------------------------------
__jit_sha512:
    push    ebp
    mov     ebp, esp
    sub     esp, 336
    push    ebx
    push    esi
    push    edi

%define STATE_BASE  -64
%define PAD_BASE    -320
%define RESULT_PTR  -324
%define ORIGINAL_LEN -328
%define REMAIN_LEN  -332
%define INPUT_PTR   -336

    mov     eax, [ebp+12]
    test    eax, eax
    js      .invalid

    mov     [ebp+ORIGINAL_LEN], eax
    mov     [ebp+REMAIN_LEN], eax
    mov     eax, [ebp+8]
    mov     [ebp+INPUT_PTR], eax

    cmp     dword [ebp+REMAIN_LEN], 0
    je      .allocate
    test    eax, eax
    jz      .invalid

.allocate:
    push    dword 129
    call    __jit_malloc
    add     esp, 4
    test    eax, eax
    jz      .invalid
    mov     [ebp+RESULT_PTR], eax

    ; state = initial SHA-512 vector
    mov     esi, sha512_iv
    lea     edi, [ebp+STATE_BASE]
    mov     ecx, 16
    rep     movsd

.full_blocks:
    cmp     dword [ebp+REMAIN_LEN], 128
    jb      .make_final_blocks

    mov     eax, [ebp+INPUT_PTR]
    push    eax
    lea     eax, [ebp+STATE_BASE]
    push    eax
    call    sha512_compress
    add     esp, 8

    add     dword [ebp+INPUT_PTR], 128
    sub     dword [ebp+REMAIN_LEN], 128
    jmp     .full_blocks

.make_final_blocks:
    ; Clear two blocks.  The second one is only used when remainder >= 112.
    lea     edi, [ebp+PAD_BASE]
    xor     eax, eax
    mov     ecx, 64
    rep     stosd

    ; Copy the remaining bytes and append 0x80.
    mov     esi, [ebp+INPUT_PTR]
    lea     edi, [ebp+PAD_BASE]
    mov     ecx, [ebp+REMAIN_LEN]
    rep     movsb
    mov     byte [edi], 80h

    ; Choose the block that receives the 128-bit big-endian length.
    lea     ebx, [ebp+PAD_BASE]
    cmp     dword [ebp+REMAIN_LEN], 112
    jb      .length_target_ready

    lea     ebx, [ebp+PAD_BASE+128]

.length_target_ready:
    ; For a signed 32-bit input length, the upper 64 length bits are zero.
    mov     eax, [ebp+ORIGINAL_LEN]
    xor     edx, edx
    shld    edx, eax, 3
    shl     eax, 3
    bswap   edx
    bswap   eax
    mov     [ebx+120], edx
    mov     [ebx+124], eax

    ; A remainder >= 112 needs two final blocks.
    cmp     dword [ebp+REMAIN_LEN], 112
    jb      .compress_last

    lea     eax, [ebp+PAD_BASE]
    push    eax
    lea     eax, [ebp+STATE_BASE]
    push    eax
    call    sha512_compress
    add     esp, 8

.compress_last:
    push    ebx
    lea     eax, [ebp+STATE_BASE]
    push    eax
    call    sha512_compress
    add     esp, 8

    ; Convert the internal little-endian word pairs to the 64 digest bytes.
    lea     esi, [ebp+STATE_BASE]
    lea     edi, [ebp+PAD_BASE]
    mov     ecx, 8
.make_digest:
    mov     eax, [esi]
    mov     edx, [esi+4]
    bswap   edx
    bswap   eax
    mov     [edi], edx
    mov     [edi+4], eax
    add     esi, 8
    add     edi, 8
    dec     ecx
    jnz     .make_digest

    ; Hex encode the digest.
    lea     esi, [ebp+PAD_BASE]
    mov     edi, [ebp+RESULT_PTR]
    mov     ecx, 64
.hex_loop:
    movzx   eax, byte [esi]
    mov     edx, eax
    shr     eax, 4
    and     edx, 15
    mov     al, [sha512_hex+eax]
    mov     [edi], al
    mov     al, [sha512_hex+edx]
    mov     [edi+1], al
    inc     esi
    add     edi, 2
    dec     ecx
    jnz     .hex_loop

    mov     byte [edi], 0
    mov     eax, [ebp+RESULT_PTR]
    jmp     .done

.invalid:
    xor     eax, eax

.done:
    pop     edi
    pop     esi
    pop     ebx
    mov     esp, ebp
    pop     ebp
    ret

%undef STATE_BASE
%undef PAD_BASE
%undef RESULT_PTR
%undef ORIGINAL_LEN
%undef REMAIN_LEN
%undef INPUT_PTR

section .rdata align=4

sha512_hex:
    db "0123456789abcdef"

sha512_iv:
    dq 0x6a09e667f3bcc908, 0xbb67ae8584caa73b
    dq 0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1
    dq 0x510e527fade682d1, 0x9b05688c2b3e6c1f
    dq 0x1f83d9abfb41bd6b, 0x5be0cd19137e2179

sha512_k:
    dq 0x428a2f98d728ae22, 0x7137449123ef65cd
    dq 0xb5c0fbcfec4d3b2f, 0xe9b5dba58189dbbc
    dq 0x3956c25bf348b538, 0x59f111f1b605d019
    dq 0x923f82a4af194f9b, 0xab1c5ed5da6d8118
    dq 0xd807aa98a3030242, 0x12835b0145706fbe
    dq 0x243185be4ee4b28c, 0x550c7dc3d5ffb4e2
    dq 0x72be5d74f27b896f, 0x80deb1fe3b1696b1
    dq 0x9bdc06a725c71235, 0xc19bf174cf692694
    dq 0xe49b69c19ef14ad2, 0xefbe4786384f25e3
    dq 0x0fc19dc68b8cd5b5, 0x240ca1cc77ac9c65
    dq 0x2de92c6f592b0275, 0x4a7484aa6ea6e483
    dq 0x5cb0a9dcbd41fbd4, 0x76f988da831153b5
    dq 0x983e5152ee66dfab, 0xa831c66d2db43210
    dq 0xb00327c898fb213f, 0xbf597fc7beef0ee4
    dq 0xc6e00bf33da88fc2, 0xd5a79147930aa725
    dq 0x06ca6351e003826f, 0x142929670a0e6e70
    dq 0x27b70a8546d22ffc, 0x2e1b21385c26c926
    dq 0x4d2c6dfc5ac42aed, 0x53380d139d95b3df
    dq 0x650a73548baf63de, 0x766a0abb3c77b2a8
    dq 0x81c2c92e47edaee6, 0x92722c851482353b
    dq 0xa2bfe8a14cf10364, 0xa81a664bbc423001
    dq 0xc24b8b70d0f89791, 0xc76c51a30654be30
    dq 0xd192e819d6ef5218, 0xd69906245565a910
    dq 0xf40e35855771202a, 0x106aa07032bbd1b8
    dq 0x19a4c116b8d2d0c8, 0x1e376c085141ab53
    dq 0x2748774cdf8eeb99, 0x34b0bcb5e19b48a8
    dq 0x391c0cb3c5c95a63, 0x4ed8aa4ae3418acb
    dq 0x5b9cca4f7763e373, 0x682e6ff3d6b2b8a3
    dq 0x748f82ee5defb2fc, 0x78a5636f43172f60
    dq 0x84c87814a1f0ab72, 0x8cc702081a6439ec
    dq 0x90befffa23631e28, 0xa4506cebde82bde9
    dq 0xbef9a3f7b2c67915, 0xc67178f2e372532b
    dq 0xca273eceea26619c, 0xd186b8c721c0c207
    dq 0xeada7dd6cde0eb1e, 0xf57d4f7fee6ed178
    dq 0x06f067aa72176fba, 0x0a637dc5a2c898a6
    dq 0x113f9804bef90dae, 0x1b710b35131c471b
    dq 0x28db77f523047d84, 0x32caab7b40c72493
    dq 0x3c9ebe0a15c9bebc, 0x431d67c49c100d4c
    dq 0x4cc5d4becb3e42b6, 0x597f299cfc657e2a
    dq 0x5fcb6fab3ad6faec, 0x6c44198c4a475817
