[Deutsch](STAGE473_WFM_ASM_CTRL_N.md) | [English](STAGE473_WFM_ASM_CTRL_N.en.md)

# Stage 473 – Ctrl+N in the WFM Assembler Tab Widget

Ctrl+N in either the fixed Generated Assembler editor or an additional ASM/INC tab creates a **new unsaved assembly document tab** in the lower WFM source area. The tab has a close icon, is marked unsaved by `_dbase_form_asm_new`, receives focus, and can be repeated to create multiple independent documents. The standard Save/Save As flow assigns a path on first save. The change is local to WFM assembly tabs rather than overriding global editor shortcuts. Tests verify creation and state.
