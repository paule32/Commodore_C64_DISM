[Deutsch](STAGE483_GERMAN_CONTEXT_AND_WFM_ATT_FIX.md) | [English](STAGE483_GERMAN_CONTEXT_AND_WFM_ATT_FIX.en.md)

# Stage 483 – German Default Context Menus and WFM AT&T Corrections

The standard Qt editing context menus are localized consistently: Undo → **Rückgängig** (Ctrl+Z), Redo → **Wiederherstellen** (Ctrl+Y), Cut → **Ausschneiden** (Ctrl+X), Copy → **Kopieren** (Ctrl+C), with equivalent translations for Paste/Delete/Select All. Existing shortcuts remain. The WFM assembler paths are also corrected for GNU AT&T syntax so compilation, generated include files, and architecture-specific output use the selected syntax instead of mixing conventions. Tests cover menu labels and WFM/AT&T generation.
