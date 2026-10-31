[Deutsch](STAGE433_DBASE_KONTEXTMENUES_UNTERKNOTEN.md) | [English](STAGE433_DBASE_KONTEXTMENUES_UNTERKNOTEN.en.md)

# Stage 433 – Context Menus for dBASE Subnodes

**Basis:** `d64_dism_asm_432.zip` (see the German release notes for the exact baseline).

Stage 433 extends dBASE Project Information context menus to the appropriate child nodes instead of limiting actions to their parent category. The correct **New**, **Open/Add**, and related project-tree operations are offered based on the selected leaf or subcategory.

Handlers keep the project hierarchy and file type consistent while preserving existing editor behavior. The documentation records the relevant menu paths and targeted source-level tests.
