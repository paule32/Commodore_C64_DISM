[Deutsch](STAGE431_DBASE_PROJEKT_NEU_DATEIAUSWAHL.md) | [English](STAGE431_DBASE_PROJEKT_NEU_DATEIAUSWAHL.en.md)

# Stage 431 – Eight New-File Actions in the dBASE Project Tree

**Basis:** `d64_dism_asm_430.zip` (see the German release notes for the exact baseline).

The **dBASE Programs** context menu within Project Information receives eight **New: …** actions for the supported document categories. New documents are created as unsaved editor/project-tree entries, not immediately as files on disk. The original **Open/Add existing** behavior is retained.

The work also addresses the distinction between source `.prg` documents and binary PRG objects. The existing project file-dialog and save workflow determine filename and destination. Tests cover menu order, document creation, and correct project-category assignment.
