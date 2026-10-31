[Deutsch](STAGE471_WFM_EXTERN_AND_UI_PAYLOAD_INCLUDES.md) | [English](STAGE471_WFM_EXTERN_AND_UI_PAYLOAD_INCLUDES.en.md)

# Stage 471 – External WFM Imports and UI Payload Include Files

Moves long WFM generated import declarations and optional external-UI payload data into separate assembler include files. `windows_asm_macros.py` adds `externalize_windows_imports()` plus an associated helper; `d64_dism.py` calls both from `_finish_compile_stage()`, writing the externalized files beside generated assembly. The main ASM becomes easier to inspect, while `%include` preserves the same linked semantics. Tests examine file generation, naming, imports, and consistency across PE32/PE64.

## Source code and command examples (unchanged)

```asm
%include "<Form1.generated.pe32.extern.inc>"
...
__dbase_wfm_external_ui_payload:
    db 123, 34, 118, 101, ...
    db 114, 115, 105, 111, ...
```


```asm
%include "Form1.generated.pe32.extern.inc"
...
.section .data
...
__dbase_wfm_external_ui_payload:
    %include "Form1.generated.pe32.payload.inc"
...
```


```asm
import DBaseQtRuntimeStartup, "libd64_qt5.dll", "#1011"
...
```


```asm
    db 123, 34, 118, 101, ...
    db 114, 115, 105, 111, ...
```

