; ---------------------------------------------------------------------------
; Interne Windows-PE64-DLL mit Export
; ---------------------------------------------------------------------------
bits 64

dllname "library64.dll"

global __d64_dll_entry
global Answer
entry __d64_dll_entry
export Answer, Answer

__d64_dll_entry:
    mov eax, 1
    ret

Answer:
    mov eax, 42
    ret
