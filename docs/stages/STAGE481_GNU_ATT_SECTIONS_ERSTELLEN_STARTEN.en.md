[Deutsch](STAGE481_GNU_ATT_SECTIONS_ERSTELLEN_STARTEN.md) | [English](STAGE481_GNU_ATT_SECTIONS_ERSTELLEN_STARTEN.en.md)

# Stage 481 – GNU AT&T Sections, WFM Form Designer, and Build → Start

Corrects GNU AT&T output so section directives such as `.section` are accepted by the internal assembler. The **Build** menu also routes commands according to the active document. With a visible dBASE Form Designer, **Compile** calls `compile_dbase_form()` and generates ASM; **Compile + Link** then calls `assemble_dbase_form()` without automatically launching; **Start** invokes `start_dbase_form()` after checking/provisioning the Qt runtime. Other source documents keep their existing `_launch_assembled_document()` route. Tests cover correct dispatch, architecture selection, generated sections, and start behavior.
