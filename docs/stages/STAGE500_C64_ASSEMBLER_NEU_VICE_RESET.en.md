[Deutsch](STAGE500_C64_ASSEMBLER_NEU_VICE_RESET.md) | [English](STAGE500_C64_ASSEMBLER_NEU_VICE_RESET.en.md)

# Stage 500 – New C64 Assembly Program and VICE Reset

The C64 assembler project branch adds **New: Assembler Program** as the first context action. It calls `_new_unsaved_c64_source_document("assembler", use_template=True, under_c64_target=True)`, immediately showing the ASM template and creating `Unnamed_<N>.asm` with `document.path=None` and `_is_new_c64_project_file=True`. Save As occurs on first persistence. The assembler source editor context menu retains VICE actions—Execute, Execute Line, Execute Selection, Transfer Program—and adds/reset fixes for the VICE BASIC/monitor start path. Existing saved projects and target selection are preserved; tests cover leaf placement, command behavior, and transfer/reset logic.
