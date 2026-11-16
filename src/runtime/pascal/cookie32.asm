; Stage 583: shared Pascal PE32 stack cookie services.
; Exported DLL ABI: 32-bit cdecl, module-local guard storage passed by pointer.
; The compiler still emits a 4-byte guard in every protected COFF module.
; The Windows CSPRNG and the fail-fast implementation are centralized here.
;
; Function: jit_pas_cookie_initialize32(volatile uint32_t *module_secret)
; Function: jit_pas_cookie_failure32()  -- noreturn
;
; Build: nasm -f win32 cookie32.asm -o cookie32.o
; Link: -lbcrypt -lkernel32 (Windows x86 import libraries)
; The atomic first writer uses the native x86 LOCK CMPXCHG instruction,
; not an import of the Windows InterlockedCompareExchange macro/intrinsic.

bits 32
section .text

global _jit_pas_cookie_initialize32
global _jit_pas_cookie_failure32

extern _BCryptGenRandom@16
extern _RaiseFailFastException@12
extern _ExitProcess@4

_jit_pas_cookie_initialize32:
    push ebp
    mov ebp, esp
    sub esp, 4

    mov ecx, [ebp+8]             ; module's 4-byte aligned guard slot
    test ecx, ecx
    jz _jit_pas_cookie_failure32
    cmp dword [ecx], 0
    jne .done

    ; BCryptGenRandom(NULL, &random, sizeof(random),
    ;                 BCRYPT_USE_SYSTEM_PREFERRED_RNG)
    lea eax, [ebp-4]
    push 2
    push 4
    push eax
    push 0
    call _BCryptGenRandom@16
    test eax, eax                ; NTSTATUS: negative means error
    js _jit_pas_cookie_failure32

    mov edx, [ebp-4]
    or edx, 1                   ; 0 is reserved for uninitialized
    mov ecx, [ebp+8]            ; reload guard pointer (ECX is caller-saved)
    xor eax, eax                ; compare against uninitialized value (0)
    lock cmpxchg dword [ecx], edx
    ; If *guard == 0, store EDX exactly once. Otherwise leave the winner's
    ; already published guard untouched. This is atomic across x86 threads.

.done:
    mov esp, ebp
    pop ebp
    ret

_jit_pas_cookie_failure32:
    push 0                      ; dwFlags
    push 0                      ; pExceptionInformation
    push 0                      ; pExceptionRecord
    call _RaiseFailFastException@12
    ; If the OS unexpectedly returns, terminate unconditionally.
    push 0xC0000409            ; STATUS_STACK_BUFFER_OVERRUN
    call _ExitProcess@4
    ud2
