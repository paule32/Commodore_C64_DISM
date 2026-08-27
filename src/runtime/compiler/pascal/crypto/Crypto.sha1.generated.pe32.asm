; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: Crypto.sha1
bits 32
global __unit_Crypto_sha1
extern __jit_sha1
__unit_Crypto_sha1:
    ret

; function crypt
global __pas_Crypto_sha1_crypt
__pas_Crypto_sha1_crypt:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    mov ecx, __pas_param_global_crypt_s_0
    pop eax
    mov dword ptr [ecx], eax
    mov eax, dword ptr [ebp+12]
    push eax
    mov ecx, __pas_param_global_crypt_len_1
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_result_global_crypt_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_crypt_len_1
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_global_crypt_s_0
    mov eax, dword ptr [ecx]
    push eax
    call __jit_sha1
    add esp, 8
    push eax
    mov ecx, __pas_result_global_crypt_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_crypt_result_2
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

align 4
__pas_unit_Crypto_sha1_fmt_s: db 37, 115, 0
__pas_unit_Crypto_sha1_fmt_d: db 37, 100, 0
__pas_unit_Crypto_sha1_fmt_c: db 37, 99, 0
__pas_unit_Crypto_sha1_newline: db 13, 10, 0
__pas_unit_Crypto_sha1_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_unit_Crypto_sha1_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal-Variablen
__pas_param_global_crypt_s_0: dd 0 ; intern: string
__pas_param_global_crypt_len_1: dd 0 ; intern: integer
__pas_result_global_crypt_result_2: dd 0 ; intern: string
