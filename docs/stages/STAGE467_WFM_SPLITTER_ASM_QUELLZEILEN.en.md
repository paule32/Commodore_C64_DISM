[Deutsch](STAGE467_WFM_SPLITTER_ASM_QUELLZEILEN.md) | [English](STAGE467_WFM_SPLITTER_ASM_QUELLZEILEN.en.md)

# Stage 467 – Show WFM Source and Generated Assembly Together

The WFM Source tab gains a vertical splitter named `dbase_form_source_assembly_splitter`. Its upper panel keeps the existing horizontal **Source Structure | Source Text** splitter, while the lower panel displays the generated assembly editor. The compiler can annotate assembly with corresponding original WFM source line information, and clicking/navigation can link source and generated output. The divider is adjustable without replacing the editor. Tests verify splitter construction, source-line mapping, and navigation.
