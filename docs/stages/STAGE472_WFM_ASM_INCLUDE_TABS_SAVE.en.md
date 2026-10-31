[Deutsch](STAGE472_WFM_ASM_INCLUDE_TABS_SAVE.md) | [English](STAGE472_WFM_ASM_INCLUDE_TABS_SAVE.en.md)

# Stage 472 – dBASE/WFM Assembly Tabs and Include Files

Inside the WFM **Source Code** tab, the upper region remains Source Structure | WFM Source, with an adjustable assembly region below. The lower region now uses `QTabWidget#dbase_form_assembly_tabs`: the first fixed tab is **Generated Assembler**, and further ASM/INC files open in independent `SourceEditorWithMiniMap` tabs with syntax highlighting and close icons. Context menus and Save/Save As respect the originating file. New tabs are not mistaken for generated output. Tests cover the UI tree and persistence behavior.
