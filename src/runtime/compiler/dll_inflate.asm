; ---------------------------------------------------------------------------
; File: dll_inflate_fixed_win32.asm
; Purpose:
;   Small, operating-system-independent Raw-DEFLATE decoder for NASM/COFF32.
;
; Build:
;   nasm -f win32 dll_inflate_fixed_win32.asm -o dll_inflate_fixed_win32.o
;
; Exports (cdecl, MinGW/COFF32 names):
;   int      db_inflate_raw(const uint8_t *src, uint32_t src_size,
;                           uint8_t *dst, uint32_t dst_capacity,
;                           uint32_t *dst_size);
;   uint32_t db_crc32(const void *data, uint32_t size);
;
; Important:
;   Supports DEFLATE block type 0 (stored) and type 1 (fixed Huffman).
;   Type 2 (dynamic Huffman) deliberately returns DB_INFLATE_BAD_BLOCK_TYPE.
;
;   Compress with Python using raw DEFLATE + Z_FIXED; see pack_fixed_raw.py.
; ---------------------------------------------------------------------------

bits 32

%define DB_INFLATE_OK               0
%define DB_INFLATE_BAD_ARGUMENT    -1
%define DB_INFLATE_TRUNCATED       -4
%define DB_INFLATE_BAD_BLOCK_TYPE  -5
%define DB_INFLATE_BAD_HUFFMAN     -6
%define DB_INFLATE_BAD_DISTANCE    -7
%define DB_INFLATE_OUTPUT_OVERFLOW -8

; EBP-relative locals of _db_inflate_raw.
%define L_SRC_CUR   -4
%define L_SRC_END   -8
%define L_BITBUF   -12
%define L_BITCNT   -16
%define L_DST_CUR  -20
%define L_DST_END  -24
%define L_DST_BASE -28
%define L_FINAL    -32

section .text align=16

global _db_inflate_raw
global _db_crc32


; ---------------------------------------------------------------------------
; int db_inflate_raw(
;     const uint8_t *source,
;     uint32_t       source_size,
;     uint8_t       *destination,
;     uint32_t       destination_capacity,
;     uint32_t      *destination_size
; );
; ---------------------------------------------------------------------------
_db_inflate_raw:
    push    ebp
    mov     ebp, esp
    sub     esp, 32
    push    ebx
    push    esi
    push    edi
    cld

    mov     eax, [ebp + 8]          ; source
    test    eax, eax
    jz      .bad_argument

    mov     edx, [ebp + 16]         ; destination
    test    edx, edx
    jz      .bad_argument

    mov     ecx, [ebp + 24]         ; destination_size
    test    ecx, ecx
    jz      .bad_argument
    mov     dword [ecx], 0

    mov     [ebp + L_SRC_CUR], eax
    add     eax, [ebp + 12]
    mov     [ebp + L_SRC_END], eax

    mov     [ebp + L_DST_CUR], edx
    mov     [ebp + L_DST_BASE], edx
    add     edx, [ebp + 20]
    mov     [ebp + L_DST_END], edx

    mov     dword [ebp + L_BITBUF], 0
    mov     dword [ebp + L_BITCNT], 0
    mov     dword [ebp + L_FINAL], 0

.next_block:
    mov     ecx, 1
    call    .get_bits
    jc      .truncated
    mov     [ebp + L_FINAL], eax

    mov     ecx, 2
    call    .get_bits
    jc      .truncated

    test    eax, eax
    jz      .stored_block

    cmp     eax, 1
    je      .fixed_block

    ; Dynamic Huffman (type 2) and reserved type 3 are not supported here.
    jmp     .bad_block_type


; ---------------------------------------------------------------------------
; Stored block (BTYPE=0).
; ---------------------------------------------------------------------------
.stored_block:
    ; Drop residual bits up to the next byte boundary.
    mov     ecx, [ebp + L_BITCNT]
    and     ecx, 7
    mov     eax, [ebp + L_BITBUF]
    shr     eax, cl
    mov     [ebp + L_BITBUF], eax
    sub     [ebp + L_BITCNT], ecx

    mov     ecx, 16
    call    .get_bits
    jc      .truncated
    mov     ebx, eax                ; LEN

    mov     ecx, 16
    call    .get_bits
    jc      .truncated              ; NLEN

    mov     edx, ebx
    xor     edx, 0x0000ffff
    and     edx, 0x0000ffff
    cmp     eax, edx
    jne     .bad_block_type

    mov     eax, [ebp + L_SRC_END]
    sub     eax, [ebp + L_SRC_CUR]
    cmp     eax, ebx
    jb      .truncated

    mov     eax, [ebp + L_DST_END]
    sub     eax, [ebp + L_DST_CUR]
    cmp     eax, ebx
    jb      .overflow

    mov     esi, [ebp + L_SRC_CUR]
    mov     edi, [ebp + L_DST_CUR]
    mov     ecx, ebx
    rep     movsb
    mov     [ebp + L_SRC_CUR], esi
    mov     [ebp + L_DST_CUR], edi

    cmp     dword [ebp + L_FINAL], 0
    je      .next_block
    jmp     .success


; ---------------------------------------------------------------------------
; Fixed Huffman block (BTYPE=1).
; ---------------------------------------------------------------------------
.fixed_block:
.decode_fixed:
    call    .decode_fixed_symbol
    jc      .truncated

    cmp     eax, 256
    jb      .literal
    je      .end_fixed_block

    cmp     eax, 285
    ja      .bad_huffman

    sub     eax, 257                ; length-table index 0..28
    movzx   esi, word [_db_length_base + eax * 2]
    movzx   ecx, byte [_db_length_extra + eax]
    test    ecx, ecx
    jz      .length_ready

    call    .get_bits
    jc      .truncated
    add     esi, eax

.length_ready:
    call    .decode_distance_symbol
    jc      .truncated
    cmp     eax, 30
    jae     .bad_distance

    movzx   edi, word [_db_distance_base + eax * 2]
    movzx   ecx, byte [_db_distance_extra + eax]
    test    ecx, ecx
    jz      .distance_ready

    call    .get_bits
    jc      .truncated
    add     edi, eax

.distance_ready:
    mov     eax, [ebp + L_DST_CUR]
    mov     edx, eax
    sub     edx, [ebp + L_DST_BASE]
    cmp     edi, edx
    ja      .bad_distance

    mov     edx, [ebp + L_DST_END]
    sub     edx, eax
    cmp     esi, edx
    ja      .overflow

    mov     edx, eax
    sub     edx, edi                ; copy source = dst_cur - distance
    mov     ecx, esi                ; copy length

.copy_match:
    mov     bl, [edx]
    mov     [eax], bl
    inc     edx
    inc     eax
    dec     ecx
    jnz     .copy_match

    mov     [ebp + L_DST_CUR], eax
    jmp     .decode_fixed

.literal:
    mov     edx, [ebp + L_DST_CUR]
    cmp     edx, [ebp + L_DST_END]
    jae     .overflow
    mov     [edx], al
    inc     edx
    mov     [ebp + L_DST_CUR], edx
    jmp     .decode_fixed

.end_fixed_block:
    cmp     dword [ebp + L_FINAL], 0
    je      .next_block


.success:
    mov     eax, [ebp + L_DST_CUR]
    sub     eax, [ebp + L_DST_BASE]
    mov     edx, [ebp + 24]
    mov     [edx], eax
    xor     eax, eax
    jmp     .return

.bad_argument:
    mov     eax, DB_INFLATE_BAD_ARGUMENT
    jmp     .return

.truncated:
    mov     eax, DB_INFLATE_TRUNCATED
    jmp     .return

.bad_block_type:
    mov     eax, DB_INFLATE_BAD_BLOCK_TYPE
    jmp     .return

.bad_huffman:
    mov     eax, DB_INFLATE_BAD_HUFFMAN
    jmp     .return

.bad_distance:
    mov     eax, DB_INFLATE_BAD_DISTANCE
    jmp     .return

.overflow:
    mov     eax, DB_INFLATE_OUTPUT_OVERFLOW

.return:
    pop     edi
    pop     esi
    pop     ebx
    mov     esp, ebp
    pop     ebp
    ret


; ---------------------------------------------------------------------------
; Internal bit reader.
;
; Input:
;   ECX = number of bits (0..16 here)
;
; Output:
;   EAX = value, least-significant-bit first
;   CF  = 0 success, 1 truncated input
;
; Preserves EBX, ESI, EDI, EDX.
; ---------------------------------------------------------------------------
.get_bits:
    push    ebx
    push    esi
    push    edi
    push    edx

    mov     edi, ecx
    mov     eax, [ebp + L_BITBUF]
    mov     edx, [ebp + L_BITCNT]

.gb_fill:
    cmp     edx, edi
    jae     .gb_ready

    mov     esi, [ebp + L_SRC_CUR]
    cmp     esi, [ebp + L_SRC_END]
    jae     .gb_fail

    movzx   ebx, byte [esi]
    inc     esi
    mov     [ebp + L_SRC_CUR], esi

    mov     ecx, edx
    shl     ebx, cl
    or      eax, ebx
    add     edx, 8
    jmp     .gb_fill

.gb_ready:
    test    edi, edi
    jnz     .gb_mask

    xor     esi, esi
    jmp     .gb_store

.gb_mask:
    mov     ebx, 1
    mov     ecx, edi
    shl     ebx, cl
    dec     ebx

    mov     esi, eax
    and     esi, ebx
    shr     eax, cl
    sub     edx, edi

.gb_store:
    mov     [ebp + L_BITBUF], eax
    mov     [ebp + L_BITCNT], edx
    mov     eax, esi
    clc

    pop     edx
    pop     edi
    pop     esi
    pop     ebx
    ret

.gb_fail:
    stc
    pop     edx
    pop     edi
    pop     esi
    pop     ebx
    ret


; ---------------------------------------------------------------------------
; Decode one symbol from the DEFLATE fixed literal/length tree.
;
; Output:
;   EAX = symbol
;   CF  = 0 success, 1 truncated/invalid
;
; The canonical fixed tree has:
;   length 7:  24 symbols  (256..279)
;   length 8: 152 symbols  (0..143, 280..287)
;   length 9: 112 symbols  (144..255)
; ---------------------------------------------------------------------------
.decode_fixed_symbol:
    push    ebx
    push    esi
    push    edi
    push    edx

    xor     ebx, ebx                ; code
    xor     esi, esi                ; first
    xor     edi, edi                ; table index
    mov     edx, 1                  ; code length

.dfs_loop:
    mov     ecx, 1
    call    .get_bits
    jc      .dfs_fail

    or      ebx, eax
    xor     ecx, ecx

    cmp     edx, 7
    jne     .dfs_not7
    mov     ecx, 24
    jmp     .dfs_have_count

.dfs_not7:
    cmp     edx, 8
    jne     .dfs_not8
    mov     ecx, 152
    jmp     .dfs_have_count

.dfs_not8:
    cmp     edx, 9
    jne     .dfs_have_count
    mov     ecx, 112

.dfs_have_count:
    mov     eax, esi
    add     eax, ecx
    cmp     ebx, eax
    jb      .dfs_found

    add     edi, ecx
    mov     esi, eax
    shl     esi, 1
    shl     ebx, 1
    inc     edx
    cmp     edx, 9
    jbe     .dfs_loop

.dfs_fail:
    stc
    pop     edx
    pop     edi
    pop     esi
    pop     ebx
    ret

.dfs_found:
    sub     ebx, esi
    add     ebx, edi                ; canonical symbol slot

    cmp     edx, 7
    jne     .dfs_len8
    lea     eax, [ebx + 256]
    jmp     .dfs_ok

.dfs_len8:
    cmp     edx, 8
    jne     .dfs_len9

    mov     eax, ebx
    sub     eax, 24
    cmp     eax, 144
    jb      .dfs_ok
    add     eax, 136                ; 144..151 -> 280..287
    jmp     .dfs_ok

.dfs_len9:
    lea     eax, [ebx - 32]         ; 176..287 -> 144..255

.dfs_ok:
    clc
    pop     edx
    pop     edi
    pop     esi
    pop     ebx
    ret


; ---------------------------------------------------------------------------
; Decode a fixed distance symbol. All distance codes have length five.
; ---------------------------------------------------------------------------
.decode_distance_symbol:
    push    ebx
    push    edx

    xor     ebx, ebx
    mov     edx, 5

.dds_loop:
    mov     ecx, 1
    call    .get_bits
    jc      .dds_fail
    shl     ebx, 1
    or      ebx, eax
    dec     edx
    jnz     .dds_loop

    mov     eax, ebx
    clc
    pop     edx
    pop     ebx
    ret

.dds_fail:
    stc
    pop     edx
    pop     ebx
    ret


; ---------------------------------------------------------------------------
; uint32_t db_crc32(const void *data, uint32_t size);
; ---------------------------------------------------------------------------
_db_crc32:
    push    esi
    push    ebx

    mov     esi, [esp + 12]         ; data
    mov     ecx, [esp + 16]         ; size
    mov     eax, 0xffffffff

.crc_byte:
    test    ecx, ecx
    jz      .crc_done

    xor     al, [esi]
    inc     esi
    mov     edx, 8

.crc_bit:
    shr     eax, 1
    jnc     .crc_no_xor
    xor     eax, 0xedb88320

.crc_no_xor:
    dec     edx
    jnz     .crc_bit

    dec     ecx
    jmp     .crc_byte

.crc_done:
    not     eax
    pop     ebx
    pop     esi
    ret


section .rdata align=4

_db_length_base:
    dw 3, 4, 5, 6, 7, 8, 9, 10
    dw 11, 13, 15, 17, 19, 23, 27, 31
    dw 35, 43, 51, 59, 67, 83, 99, 115
    dw 131, 163, 195, 227, 258

_db_length_extra:
    db 0, 0, 0, 0, 0, 0, 0, 0
    db 1, 1, 1, 1, 2, 2, 2, 2
    db 3, 3, 3, 3, 4, 4, 4, 4
    db 5, 5, 5, 5, 0

align 2
_db_distance_base:
    dw 1, 2, 3, 4, 5, 7, 9, 13
    dw 17, 25, 33, 49, 65, 97, 129, 193
    dw 257, 385, 513, 769, 1025, 1537
    dw 2049, 3073, 4097, 6145, 8193
    dw 12289, 16385, 24577

_db_distance_extra:
    db 0, 0, 0, 0, 1, 1, 2, 2
    db 3, 3, 4, 4, 5, 5, 6, 6
    db 7, 7, 8, 8, 9, 9, 10, 10
    db 11, 11, 12, 12, 13, 13
