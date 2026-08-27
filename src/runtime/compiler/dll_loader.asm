; ---------------------------------------------------------------------------
; File: dll_loader_small.asm
; Target: NASM -f win32 (COFF32), 32-bit x86
;
; Compact replacement for dll_loader.cc.
;
; Exports:
;   BOOL packed_dll_load_resource(HMODULE module, int id, PackedDllHandle *out)
;   void packed_dll_unload(PackedDllHandle *handle)
;
; PackedDllHandle:
;   +0  HMODULE module
;   +4  char temporary_file[260]
;
; DBDLLZ1 header:
;   +0  "DBDLLZ1",0
;   +8  uint32 version (=1)
;   +12 uint32 original_size
;   +16 uint32 compressed_size
;   +20 uint32 crc32
;   +24 raw DEFLATE data
;
; Notes:
; - Keeps the public API and CRC/header validation.
; - Uses one WriteFile call instead of a partial-write loop.
; - Omits secure memory wiping and detailed SetLastError preservation.
; ---------------------------------------------------------------------------

bits 32

%define MAX_PATH                 260
%define RT_RCDATA                10
%define GENERIC_WRITE            0x40000000
%define CREATE_ALWAYS            2
%define FILE_ATTRIBUTE_TEMPORARY 0x00000100
%define INVALID_HANDLE_VALUE     -1

; EBP-relative locals
%define L_RESULT       -4
%define L_BLOB_SIZE   -8
%define L_HEAP        -12
%define L_IMAGE       -16
%define L_ORIGINAL    -20
%define L_COMPRESSED  -24
%define L_FILE        -28
%define L_WRITTEN     -32
%define L_OUTPUT_SIZE -36
%define L_TEMP_DIR   -300

section .text align=16

global _packed_dll_load_resource
global _packed_dll_unload

extern _db_inflate_raw
extern _db_crc32

extern __imp__FindResourceA@12
extern __imp__SizeofResource@8
extern __imp__LoadResource@8
extern __imp__LockResource@4
extern __imp__GetProcessHeap@0
extern __imp__HeapAlloc@12
extern __imp__HeapFree@12
extern __imp__GetTempPathA@8
extern __imp__GetTempFileNameA@16
extern __imp__CreateFileA@28
extern __imp__WriteFile@20
extern __imp__CloseHandle@4
extern __imp__LoadLibraryA@4
extern __imp__FreeLibrary@4
extern __imp__DeleteFileA@4


; BOOL __cdecl packed_dll_load_resource(
;     HMODULE resource_module,
;     int resource_id,
;     PackedDllHandle *result
; );
_packed_dll_load_resource:
    push    ebp
    mov     ebp, esp
    sub     esp, 300
    push    ebx
    push    esi
    push    edi
    cld

    mov     edi, [ebp + 16]
    test    edi, edi
    jz      .fail
    mov     [ebp + L_RESULT], edi
    mov     dword [edi], 0
    mov     byte  [edi + 4], 0
    mov     dword [ebp + L_IMAGE], 0
    mov     dword [ebp + L_FILE], INVALID_HANDLE_VALUE

    ; Find RCDATA resource.
    push    byte RT_RCDATA
    push    dword [ebp + 12]
    push    dword [ebp + 8]
    call    [__imp__FindResourceA@12]
    test    eax, eax
    jz      .fail
    mov     ebx, eax

    push    ebx
    push    dword [ebp + 8]
    call    [__imp__SizeofResource@8]
    cmp     eax, 24
    jb      .fail
    mov     [ebp + L_BLOB_SIZE], eax

    push    ebx
    push    dword [ebp + 8]
    call    [__imp__LoadResource@8]
    test    eax, eax
    jz      .fail

    push    eax
    call    [__imp__LockResource@4]
    test    eax, eax
    jz      .fail
    mov     esi, eax

    ; Validate DBDLLZ1 header.
    cmp     dword [esi],     0x4c444244 ; "DBDL"
    jne     .fail
    cmp     dword [esi + 4], 0x00315a4c ; "LZ1",0
    jne     .fail
    cmp     dword [esi + 8], 1
    jne     .fail

    mov     eax, [esi + 12]
    test    eax, eax
    jz      .fail
    mov     [ebp + L_ORIGINAL], eax

    mov     ecx, [esi + 16]
    test    ecx, ecx
    jz      .fail
    mov     [ebp + L_COMPRESSED], ecx

    mov     edx, [ebp + L_BLOB_SIZE]
    sub     edx, 24
    cmp     ecx, edx
    ja      .fail

    ; Allocate output image.
    call    [__imp__GetProcessHeap@0]
    test    eax, eax
    jz      .fail
    mov     [ebp + L_HEAP], eax

    push    dword [ebp + L_ORIGINAL]
    push    byte 0
    push    eax
    call    [__imp__HeapAlloc@12]
    test    eax, eax
    jz      .fail
    mov     [ebp + L_IMAGE], eax
    mov     dword [ebp + L_OUTPUT_SIZE], 0

    ; db_inflate_raw(blob+24, packed, image, original, &output_size)
    lea     edx, [ebp + L_OUTPUT_SIZE]
    push    edx
    push    dword [ebp + L_ORIGINAL]
    push    eax
    push    dword [ebp + L_COMPRESSED]
    lea     eax, [esi + 24]
    push    eax
    call    _db_inflate_raw
    add     esp, 20
    test    eax, eax
    jnz     .free_fail

    mov     eax, [ebp + L_OUTPUT_SIZE]
    cmp     eax, [ebp + L_ORIGINAL]
    jne     .free_fail

    ; CRC32 check.
    push    dword [ebp + L_ORIGINAL]
    push    dword [ebp + L_IMAGE]
    call    _db_crc32
    add     esp, 8
    cmp     eax, [esi + 20]
    jne     .free_fail

    ; Build temporary file name directly in result->temporary_file.
    lea     eax, [ebp + L_TEMP_DIR]
    push    eax
    push    dword MAX_PATH
    call    [__imp__GetTempPathA@8]
    test    eax, eax
    jz      .free_fail
    cmp     eax, MAX_PATH
    jae     .free_fail

    mov     edi, [ebp + L_RESULT]
    lea     edx, [edi + 4]
    push    edx
    push    byte 0
    push    dword _dbm_prefix
    lea     eax, [ebp + L_TEMP_DIR]
    push    eax
    call    [__imp__GetTempFileNameA@16]
    test    eax, eax
    jz      .free_fail

    ; CreateFileA(path, GENERIC_WRITE, 0, 0, CREATE_ALWAYS,
    ;             FILE_ATTRIBUTE_TEMPORARY, 0)
    push    byte 0
    push    dword FILE_ATTRIBUTE_TEMPORARY
    push    byte CREATE_ALWAYS
    push    byte 0
    push    byte 0
    push    dword GENERIC_WRITE
    lea     eax, [edi + 4]
    push    eax
    call    [__imp__CreateFileA@28]
    cmp     eax, INVALID_HANDLE_VALUE
    je      .delete_free_fail
    mov     [ebp + L_FILE], eax
    mov     dword [ebp + L_WRITTEN], 0

    ; One local-file WriteFile call is sufficient for this compact loader.
    push    byte 0
    lea     edx, [ebp + L_WRITTEN]
    push    edx
    push    dword [ebp + L_ORIGINAL]
    push    dword [ebp + L_IMAGE]
    push    eax
    call    [__imp__WriteFile@20]
    test    eax, eax
    jz      .close_delete_free_fail
    mov     eax, [ebp + L_WRITTEN]
    cmp     eax, [ebp + L_ORIGINAL]
    jne     .close_delete_free_fail

    push    dword [ebp + L_FILE]
    call    [__imp__CloseHandle@4]
    mov     dword [ebp + L_FILE], INVALID_HANDLE_VALUE

    ; Release decompressed buffer before LoadLibrary.
    push    dword [ebp + L_IMAGE]
    push    byte 0
    push    dword [ebp + L_HEAP]
    call    [__imp__HeapFree@12]
    mov     dword [ebp + L_IMAGE], 0

    mov     edi, [ebp + L_RESULT]
    lea     eax, [edi + 4]
    push    eax
    call    [__imp__LoadLibraryA@4]
    test    eax, eax
    jz      .delete_fail

    mov     [edi], eax
    mov     eax, 1
    jmp     .done

.close_delete_free_fail:
    push    dword [ebp + L_FILE]
    call    [__imp__CloseHandle@4]
    mov     dword [ebp + L_FILE], INVALID_HANDLE_VALUE

.delete_free_fail:
    mov     edi, [ebp + L_RESULT]
    cmp     byte [edi + 4], 0
    je      .free_fail
    lea     eax, [edi + 4]
    push    eax
    call    [__imp__DeleteFileA@4]
    mov     byte [edi + 4], 0

.free_fail:
    mov     eax, [ebp + L_IMAGE]
    test    eax, eax
    jz      .fail
    push    eax
    push    byte 0
    push    dword [ebp + L_HEAP]
    call    [__imp__HeapFree@12]
    mov     dword [ebp + L_IMAGE], 0
    jmp     .fail

.delete_fail:
    mov     edi, [ebp + L_RESULT]
    lea     eax, [edi + 4]
    push    eax
    call    [__imp__DeleteFileA@4]
    mov     byte [edi + 4], 0

.fail:
    xor     eax, eax

.done:
    pop     edi
    pop     esi
    pop     ebx
    mov     esp, ebp
    pop     ebp
    ret


; void __cdecl packed_dll_unload(PackedDllHandle *handle);
_packed_dll_unload:
    push    ebx
    mov     ebx, [esp + 8]
    test    ebx, ebx
    jz      .unload_done

    mov     eax, [ebx]
    test    eax, eax
    jz      .unload_file
    push    eax
    call    [__imp__FreeLibrary@4]
    mov     dword [ebx], 0

.unload_file:
    cmp     byte [ebx + 4], 0
    je      .unload_done
    lea     eax, [ebx + 4]
    push    eax
    call    [__imp__DeleteFileA@4]
    mov     byte [ebx + 4], 0

.unload_done:
    pop     ebx
    ret


section .rdata align=4
_dbm_prefix:
    db "dbm", 0
