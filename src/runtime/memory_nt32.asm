; ---------------------------------------------------------------------------
; File:   memory_nt32_min.asm
; Author: (c) 2026 Jens Kallup - paule32
; Note:   Minimal NASM replacement for memory.cc
; Target: 32-bit Windows / i386 COFF
; ---------------------------------------------------------------------------
;
; Assemble for a normal MinGW32 link:
;
;   nasm -f win32 -Ox ^
;       -dDYNSTRING_MAGIC=0x........ ^
;       -dJIT_RUNTIME_ERROR=........ ^
;       -dJIT_RESOLVE_AUX=1 ^
;       memory_nt32_min.asm -o memory.o
;
; DYNSTRING_MAGIC and JIT_RUNTIME_ERROR must have exactly the same values as
; in memory.h.  The file intentionally refuses to assemble without them.
;
; This version uses the p_LoadLibraryA, p_GetProcAddress, p_GetStdHandle and
; p_ReadFile function-pointer variables supplied by loader/windows.o.  It has
; no __imp__ references and therefore needs no KERNEL32 import library.
;
; JIT_RESOLVE_AUX=1 additionally resolves the API pointers from the C++ source
; (kernel32/user32/mpr). Set it to 0 only when another runtime module resolves
; those auxiliary pointers.
;
; The default symbol spelling is the 32-bit MinGW C ABI:
;     C name _jit_malloc  -> COFF symbol __jit_malloc
; Define JIT_RAW_SYMBOLS=1 only if the custom COFF linker expects the public
; name literally without the extra C leading underscore.
; ---------------------------------------------------------------------------

BITS 32

%ifndef DYNSTRING_MAGIC
    %error "Pass DYNSTRING_MAGIC with -dDYNSTRING_MAGIC=<value>"
%endif

%ifndef JIT_RUNTIME_ERROR
    %error "Pass JIT_RUNTIME_ERROR with -dJIT_RUNTIME_ERROR=<value>"
%endif

%ifndef JIT_RESOLVE_AUX
    %define JIT_RESOLVE_AUX 1
%endif

%ifdef JIT_RAW_SYMBOLS
    %define C(x) x
%else
    %define C(x) _ %+ x
%endif

%define DYNARRAY_HEADER_SIZE   8
%define DYNSTRING_HEADER_SIZE 12

%define STD_INPUT_HANDLE      -10
%define INVALID_HANDLE_VALUE  -1

; Runtime helpers supplied by the other runtime objects.
extern C(_jit_raise)
extern C(_jit_error_out_of_memory)
extern C(_jit_print_text)
extern C(__jit_setjmp)
extern C(__jit_longjmp)

; Win32 function-pointer variables initialized by loader/windows.o.
extern C(p_LoadLibraryA)
extern C(p_GetProcAddress)
extern C(p_GetStdHandle)
extern C(p_ReadFile)

%if JIT_RESOLVE_AUX
    ; These variables already exist in the runtime's Win32 API module.
    extern C(p_ExitProcess)
    extern C(p_GetDriveTypeA)
    extern C(p_GetVolumeInformationA)
    extern C(p_MessageBoxA)
    extern C(p_WNetGetConnectionA)
%endif

section .text align=1

; ---------------------------------------------------------------------------
; Resolve all {name,target} entries in ESI from the DLL named by EDX.
; The table ends with a null name.  Returns EAX=1 on success, EAX=0 on error.
; Called only by init_runtime; EBX/ESI/EDI are saved there.
; ---------------------------------------------------------------------------
load_and_resolve:
    push edx
    call [C(p_LoadLibraryA)]
    test eax, eax
    jz .failed

    mov ebx, eax

.next:
    mov eax, [esi]
    add esi, 4
    test eax, eax
    jz .success

    mov edi, [esi]
    add esi, 4

    push eax
    push ebx
    call [C(p_GetProcAddress)]
    test eax, eax
    jz .failed

    mov [edi], eax
    jmp .next

.success:
    mov eax, 1
    ret

.failed:
    xor eax, eax
    ret

; ---------------------------------------------------------------------------
; Resolve the CRT once.  This intentionally uses a simple non-thread-safe
; guard, matching the original code and keeping the implementation small.
; ---------------------------------------------------------------------------
init_runtime:
    cmp dword [p_malloc], 0
    je .initialize
    cmp dword [p_free], 0
    jne .already_ready

.initialize:
    push ebx
    push esi
    push edi

    mov edx, dll_msvcrt
    mov esi, crt_imports
    call load_and_resolve
    test eax, eax
    jz .done

%if JIT_RESOLVE_AUX
    mov edx, dll_kernel32
    mov esi, kernel32_imports
    call load_and_resolve
    test eax, eax
    jz .done

    mov edx, dll_user32
    mov esi, user32_imports
    call load_and_resolve
    test eax, eax
    jz .done

    mov edx, dll_mpr
    mov esi, mpr_imports
    call load_and_resolve
    test eax, eax
    jz .done
%endif

    mov eax, 1

.done:
    pop edi
    pop esi
    pop ebx
    ret

.already_ready:
    mov eax, 1
    ret

; ---------------------------------------------------------------------------
; Small common dispatcher for the resolved CRT functions.
; EAX points to the function-pointer slot.  The original arguments stay on
; the stack, so the final JMP is a proper cdecl tail call.
; ---------------------------------------------------------------------------
dispatch_crt:
    cmp dword [eax], 0
    jne .jump

    push eax
    call init_runtime
    pop edx
    test eax, eax
    jz .failed
    mov eax, edx

.jump:
    jmp [eax]

.failed:
    xor eax, eax
    ret

; ---------------------------------------------------------------------------
; Allocation and memory wrappers
; ---------------------------------------------------------------------------
global C(_jit_malloc)
C(_jit_malloc):
    mov eax, p_malloc
    jmp dispatch_crt

global C(_jit_calloc)
C(_jit_calloc):
    mov eax, p_calloc
    jmp dispatch_crt

global C(_jit_realloc)
C(_jit_realloc):
    mov eax, p_realloc
    jmp dispatch_crt

global C(_jit_free)
C(_jit_free):
    cmp dword [esp + 4], 0
    je .null
    mov eax, p_free
    jmp dispatch_crt
.null:
    xor eax, eax
    ret

global C(_jit_memcpy)
C(_jit_memcpy):
    mov eax, p_memcpy
    jmp dispatch_crt

global C(_jit_memset)
global C(memset)
C(_jit_memset):
C(memset):
    mov eax, p_memset
    jmp dispatch_crt

global C(_jit_memcmp)
C(_jit_memcmp):
    mov eax, p_memcmp
    jmp dispatch_crt

global C(_jit_memmove)
C(_jit_memmove):
    mov eax, p_memmove
    jmp dispatch_crt

global C(_jit_new_memory)
C(_jit_new_memory):
    push dword [esp + 4]
    call C(_jit_malloc)
    add esp, 4
    test eax, eax
    jz oom_error

    push dword [esp + 4]
    push byte 0
    push eax
    call C(_jit_memset)
    add esp, 12
    ret

global C(_jit_dispose_memory)
C(_jit_dispose_memory):
    jmp C(_jit_free)

global C(_jit_setlength_memory)
C(_jit_setlength_memory):
    ; The high dword of uint64_t new_size is deliberately ignored because
    ; size_t and the PE32 address space are 32 bit.
    jmp C(_jit_realloc)

; ---------------------------------------------------------------------------
; Dynamic array
;
; Header:
;   +0 uint32 length
;   +4 uint32 element_size
; Returned pointer = header + 8
; ---------------------------------------------------------------------------
global C(_jit_dynarray_setlength)
C(_jit_dynarray_setlength):
    push ebp
    push ebx
    push esi
    push edi

    xor esi, esi                    ; old header
    xor ebp, ebp                    ; old payload size

    mov eax, [esp + 20]             ; data
    test eax, eax
    jz .new_size

    lea esi, [eax - DYNARRAY_HEADER_SIZE]
    mov eax, [esi]
    mul dword [esi + 4]
    jc .overflow
    mov ebp, eax

.new_size:
    mov eax, [esp + 24]             ; length
    test eax, eax
    jz .release

    mul dword [esp + 28]            ; element_size
    jc .overflow
    mov edi, eax                    ; new payload size

    add eax, DYNARRAY_HEADER_SIZE
    jc .overflow
    push eax
    push esi
    call C(_jit_realloc)
    add esp, 8
    test eax, eax
    jz .out_of_memory

    mov ebx, eax
    mov eax, [esp + 24]
    mov [ebx], eax
    mov eax, [esp + 28]
    mov [ebx + 4], eax

    cmp edi, ebp
    jbe .return_data

    mov eax, ebx
    add eax, DYNARRAY_HEADER_SIZE
    add eax, ebp
    mov ecx, edi
    sub ecx, ebp

    push ecx
    push byte 0
    push eax
    call C(_jit_memset)
    add esp, 12

.return_data:
    lea eax, [ebx + DYNARRAY_HEADER_SIZE]
    jmp .done

.release:
    test esi, esi
    jz .return_null
    push esi
    call C(_jit_free)
    add esp, 4

.return_null:
    xor eax, eax
    jmp .done

.overflow:
.out_of_memory:
    call oom_error

.done:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret

; ---------------------------------------------------------------------------
; Dynamic string
;
; Header:
;   +0 uint32 magic
;   +4 uint32 reserved
;   +8 uint32 length
; Returned pointer = header + 12
; ---------------------------------------------------------------------------
global C(_jit_dynstring_setlength)
C(_jit_dynstring_setlength):
    push ebx
    push esi
    push edi

    xor esi, esi                    ; old header
    xor ebx, ebx                    ; old length
    mov eax, [esp + 16]             ; old_data
    mov edi, [esp + 20]             ; new_length
    test eax, eax
    jz .resize

    lea esi, [eax - DYNSTRING_HEADER_SIZE]
    cmp dword [esi], DYNSTRING_MAGIC
    jne .invalid
    mov ebx, [esi + 8]

.resize:
    mov eax, edi
    add eax, DYNSTRING_HEADER_SIZE + 1
    jc .out_of_memory

    push eax
    push esi
    call C(_jit_realloc)
    add esp, 8
    test eax, eax
    jz .out_of_memory

    mov dword [eax], DYNSTRING_MAGIC
    mov dword [eax + 4], 0
    mov [eax + 8], edi
    lea esi, [eax + DYNSTRING_HEADER_SIZE]

    cmp edi, ebx
    jbe .terminate

    lea eax, [esi + ebx]
    mov ecx, edi
    sub ecx, ebx
    push ecx
    push byte 0
    push eax
    call C(_jit_memset)
    add esp, 12

.terminate:
    mov byte [esi + edi], 0
    mov eax, esi
    jmp .done

.invalid:
    call invalid_string_error
    jmp .done

.out_of_memory:
    call oom_error

.done:
    pop edi
    pop esi
    pop ebx
    ret

global C(_jit_dynstring_length)
C(_jit_dynstring_length):
    mov eax, [esp + 4]
    test eax, eax
    jz .zero
    mov eax, [eax - 4]              ; header.length
    ret
.zero:
    xor eax, eax
    ret

global C(_jit_dynstring_concat)
C(_jit_dynstring_concat):
    push ebp
    push ebx
    push esi
    push edi

    mov esi, [esp + 20]             ; left data
    mov edi, [esp + 24]             ; right data
    test esi, esi
    jz .invalid
    test edi, edi
    jz .invalid
    cmp dword [esi - DYNSTRING_HEADER_SIZE], DYNSTRING_MAGIC
    jne .invalid
    cmp dword [edi - DYNSTRING_HEADER_SIZE], DYNSTRING_MAGIC
    jne .invalid

    mov ebp, [esi - 4]              ; left length
    mov eax, [edi - 4]              ; right length
    add eax, ebp
    jc .out_of_memory
    mov edx, eax                    ; total length
    add eax, DYNSTRING_HEADER_SIZE + 1
    jc .out_of_memory

    push edx                        ; preserve total across malloc
    push eax
    call C(_jit_malloc)
    add esp, 4
    pop edx
    test eax, eax
    jz .out_of_memory

    mov dword [eax], DYNSTRING_MAGIC
    mov dword [eax + 4], 0
    mov [eax + 8], edx
    lea ebx, [eax + DYNSTRING_HEADER_SIZE]

    push ebp
    push esi
    push ebx
    call C(_jit_memcpy)
    add esp, 12

    push dword [edi - 4]
    push edi
    lea eax, [ebx + ebp]
    push eax
    call C(_jit_memcpy)
    add esp, 12

    mov eax, ebp
    add eax, [edi - 4]
    mov byte [ebx + eax], 0
    mov eax, ebx
    jmp .done

.invalid:
    call invalid_string_error
    jmp .done

.out_of_memory:
    call oom_error

.done:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret

global C(_jit_dynstring_from_cstr)
C(_jit_dynstring_from_cstr):
    push ebx
    push esi
    push edi

    mov esi, [esp + 16]
    test esi, esi
    jnz .have_text
    mov esi, empty_text

.have_text:
    push esi
    call C(_jit_strlen)
    add esp, 4
    mov edi, eax

    push edi
    push byte 0
    call C(_jit_dynstring_setlength)
    add esp, 8
    test eax, eax
    jz .done
    mov ebx, eax

    test edi, edi
    jz .return_data
    push edi
    push esi
    push ebx
    call C(_jit_memcpy)
    add esp, 12

.return_data:
    mov eax, ebx

.done:
    pop edi
    pop esi
    pop ebx
    ret

; ---------------------------------------------------------------------------
; Raw C-string helpers
; ---------------------------------------------------------------------------
global C(_jit_strlen)
C(_jit_strlen):
    mov edx, [esp + 4]
    test edx, edx
    jz .zero
    mov eax, edx
.scan:
    cmp byte [eax], 0
    je .found
    inc eax
    jmp .scan
.found:
    sub eax, edx
    ret
.zero:
    xor eax, eax
    ret

global C(_jit_strdup)
C(_jit_strdup):
    push ebx
    push esi
    push edi

    mov esi, [esp + 16]
    test esi, esi
    jnz .have_text
    mov esi, empty_text

.have_text:
    push esi
    call C(_jit_strlen)
    add esp, 4
    lea edi, [eax + 1]

    push edi
    call C(_jit_malloc)
    add esp, 4
    test eax, eax
    jz .done
    mov ebx, eax

    push edi
    push esi
    push ebx
    call C(_jit_memcpy)
    add esp, 12
    mov eax, ebx

.done:
    pop edi
    pop esi
    pop ebx
    ret

; ---------------------------------------------------------------------------
; setjmp/longjmp adapters
; ---------------------------------------------------------------------------
global C(_jit_setjmp)
C(_jit_setjmp):
    jmp C(__jit_setjmp)

global C(_jit_longjmp)
C(_jit_longjmp):
    jmp C(__jit_longjmp)

; ---------------------------------------------------------------------------
; printf/snprintf adapters
; ---------------------------------------------------------------------------
global C(_jit_vprintf)
C(_jit_vprintf):
    mov eax, p_vprintf
    jmp dispatch_crt

global C(_jit_printf)
C(_jit_printf):
    lea eax, [esp + 8]              ; first unnamed argument
    push eax
    push dword [esp + 8]            ; format after the first PUSH
    call C(_jit_vprintf)
    add esp, 8
    ret

global C(_jit_vsnprintf)
C(_jit_vsnprintf):
    mov eax, p_vsnprintf
    jmp dispatch_crt

global C(_jit_snprintf)
C(_jit_snprintf):
    lea eax, [esp + 16]             ; first unnamed argument
    push eax
    push dword [esp + 16]           ; fmt
    push dword [esp + 16]           ; size
    push dword [esp + 16]           ; buffer
    call C(_jit_vsnprintf)
    add esp, 16
    ret

; ---------------------------------------------------------------------------
; Console input
; ---------------------------------------------------------------------------
global C(parse_integer)
C(parse_integer):
    push ebx
    mov edx, [esp + 8]
    mov ecx, 1
    xor eax, eax

    cmp byte [edx], '-'
    jne .digits
    mov ecx, -1
    inc edx

.digits:
    movzx ebx, byte [edx]
    cmp bl, '0'
    jb .finish
    cmp bl, '9'
    ja .finish
    imul eax, eax, 10
    sub ebx, '0'
    add eax, ebx
    inc edx
    jmp .digits

.finish:
    cmp ecx, 1
    je .positive
    neg eax
.positive:
    pop ebx
    ret

; EAX=buffer, ECX=byte count.  Removes trailing CR/LF and terminates the text.
trim_input_line:
    test ecx, ecx
    jz .terminate
.again:
    mov dl, [eax + ecx - 1]
    cmp dl, 13
    je .remove
    cmp dl, 10
    jne .terminate
.remove:
    dec ecx
    jnz .again
.terminate:
    mov byte [eax + ecx], 0
    ret

global C(_jit_read_int)
C(_jit_read_int):
    push ebp
    mov ebp, esp
    sub esp, 260                    ; 256-byte buffer + DWORD bytesRead

    push byte STD_INPUT_HANDLE
    call [C(p_GetStdHandle)]
    test eax, eax
    jz .failed
    cmp eax, INVALID_HANDLE_VALUE
    je .failed

    push byte 0
    lea edx, [ebp - 4]
    push edx
    push dword 255
    lea edx, [ebp - 260]
    push edx
    push eax
    call [C(p_ReadFile)]
    test eax, eax
    jz .failed

    lea eax, [ebp - 260]
    mov ecx, [ebp - 4]
    call trim_input_line
    push eax
    call C(parse_integer)
    add esp, 4
    leave
    ret

.failed:
    xor eax, eax
    leave
    ret

global C(_jit_read_string)
C(_jit_read_string):
    push ebp
    mov ebp, esp
    push ebx
    sub esp, 4                     ; bytesRead

    push dword 1024
    call C(_jit_malloc)
    add esp, 4
    test eax, eax
    jz .return
    mov ebx, eax
    mov byte [ebx], 0

    push byte STD_INPUT_HANDLE
    call [C(p_GetStdHandle)]
    test eax, eax
    jz .buffer
    cmp eax, INVALID_HANDLE_VALUE
    je .buffer

    push byte 0
    lea edx, [ebp - 8]
    push edx
    push dword 1023
    push ebx
    push eax
    call [C(p_ReadFile)]
    test eax, eax
    jz .buffer

    mov eax, ebx
    mov ecx, [ebp - 8]
    call trim_input_line

.buffer:
    mov eax, ebx

.return:
    mov ebx, [ebp - 4]
    leave
    ret

global C(_jit_read_char)
C(_jit_read_char):
    push ebp
    mov ebp, esp
    sub esp, 20                    ; 16-byte buffer + DWORD bytesRead

    push byte STD_INPUT_HANDLE
    call [C(p_GetStdHandle)]
    test eax, eax
    jz .failed
    cmp eax, INVALID_HANDLE_VALUE
    je .failed

    push byte 0
    lea edx, [ebp - 4]
    push edx
    push byte 16
    lea edx, [ebp - 20]
    push edx
    push eax
    call [C(p_ReadFile)]
    test eax, eax
    jz .failed
    cmp dword [ebp - 4], 0
    je .failed

    movzx eax, byte [ebp - 20]
    leave
    ret

.failed:
    mov eax, -1
    leave
    ret

global C(_jit_debug_break)
C(_jit_debug_break):
    push debug_prompt
    call C(_jit_print_text)
    add esp, 4
    call C(_jit_read_char)
    push newline_text
    call C(_jit_print_text)
    add esp, 4
    ret

; ---------------------------------------------------------------------------
; Error helpers.  _jit_raise normally does not return; returning EAX=0 keeps
; the wrappers deterministic if a host implementation chooses to return.
; ---------------------------------------------------------------------------
oom_error:
    push oom_text
    call C(_jit_error_out_of_memory)
    add esp, 4
    xor eax, eax
    ret

invalid_string_error:
    push invalid_string_text
    push dword JIT_RUNTIME_ERROR
    call C(_jit_raise)
    add esp, 8
    xor eax, eax
    ret

section .rdata align=4

crt_imports:
    dd name_malloc,    p_malloc
    dd name_calloc,    p_calloc
    dd name_realloc,   p_realloc
    dd name_free,      p_free
    dd name_memcpy,    p_memcpy
    dd name_memset,    p_memset
    dd name_memcmp,    p_memcmp
    dd name_memmove,   p_memmove
    dd name_vprintf,   p_vprintf
    dd name_vsnprintf, p_vsnprintf
    dd 0

%if JIT_RESOLVE_AUX
kernel32_imports:
    dd name_ExitProcess,           C(p_ExitProcess)
    dd name_GetDriveTypeA,         C(p_GetDriveTypeA)
    dd name_GetVolumeInformationA, C(p_GetVolumeInformationA)
    dd 0

user32_imports:
    dd name_MessageBoxA, C(p_MessageBoxA)
    dd 0

mpr_imports:
    dd name_WNetGetConnectionA, C(p_WNetGetConnectionA)
    dd 0
%endif

dll_msvcrt:     db "msvcrt.dll", 0
%if JIT_RESOLVE_AUX
dll_kernel32:   db "kernel32.dll", 0
dll_user32:     db "user32.dll", 0
dll_mpr:        db "mpr.dll", 0
%endif

name_malloc:    db "malloc", 0
name_calloc:    db "calloc", 0
name_realloc:   db "realloc", 0
name_free:      db "free", 0
name_memcpy:    db "memcpy", 0
name_memset:    db "memset", 0
name_memcmp:    db "memcmp", 0
name_memmove:   db "memmove", 0
name_vprintf:   db "vprintf", 0
name_vsnprintf: db "vsnprintf", 0

%if JIT_RESOLVE_AUX
name_ExitProcess:           db "ExitProcess", 0
name_GetDriveTypeA:         db "GetDriveTypeA", 0
name_GetVolumeInformationA: db "GetVolumeInformationA", 0
name_MessageBoxA:           db "MessageBoxA", 0
name_WNetGetConnectionA:    db "WNetGetConnectionA", 0
%endif

empty_text:          db 0
oom_text:            db "Out of memory.", 0
invalid_string_text: db "Invalid dynamic string", 0
debug_prompt:        db "[DEBUG BREAK] press Enter...", 0
newline_text:        db 10, 0

section .bss align=4

p_malloc:      resd 1
p_calloc:      resd 1
p_realloc:     resd 1
p_free:        resd 1
p_memcpy:      resd 1
p_memset:      resd 1
p_memcmp:      resd 1
p_memmove:     resd 1
p_vprintf:     resd 1
p_vsnprintf:   resd 1
