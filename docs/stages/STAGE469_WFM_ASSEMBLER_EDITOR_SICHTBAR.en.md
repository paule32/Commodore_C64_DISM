[Deutsch](STAGE469_WFM_ASSEMBLER_EDITOR_SICHTBAR.md) | [English](STAGE469_WFM_ASSEMBLER_EDITOR_SICHTBAR.en.md)

# Stage 469 – Make the WFM Assembly Editor Visible below Source

Corrects a layout regression where the generated assembly editor did not appear below the Source Structure/Source Text panes. The obsolete `generated_assembly_page` remains only as a hidden compatibility placeholder; the actual `generated_assembly_editor_container` (editor plus minimap) is inserted into `dbase_form_source_assembly_splitter`. The resulting vertical splitter has the expected upper source row and lower assembler pane. Tests check widget placement and visibility without changing WFM compiler output.
