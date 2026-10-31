[Deutsch](STAGE399_C64_BASIC_CONTEXT_NEW.md) | [English](STAGE399_C64_BASIC_CONTEXT_NEW.en.md)

# Stage 399 – New BASIC Program in the C64 Project Context Menu

**Authoritative starting point:** `d64_dism_asm_398.zip`.

## Usage

Right-click **BASIC Programs → Commodore C= 64** in the **Project Information** dock. The first context-menu action is now **New BASIC Program**. Existing actions for adding a C64 BASIC program and expanding/collapsing a node remain.

The command uses `_new_unsaved_c64_source_document('basic', use_template=True, under_c64_target=True)`. It opens the C64 BASIC template, creates the new leaf **directly under Commodore C= 64**, and sets the established `_is_new_c64_project_file` flag. The source is not written to disk until **Save** opens the existing **Save As** dialog and the user chooses a filename and destination.

After saving, `Category.c64` persists the file in the project. `.bas` and `.basic` files under that branch retain the C64 source type after project reload and can be reopened through the tree. Existing **File → New** commands still create documents under the general BASIC root.

## Implementation

Only `d64_dism.py` changed relative to Stage 398; the new `test_stage399_c64_basic_context.py` contains five tests. Other files are unchanged from the baseline.

## Verification

- `python -m py_compile d64_dism.py`: passed.
- Five Stage-399 and six Stage-394 tests: passed.
- Forty-six Stage-393, 395, 396, 397, and 398 tests: passed.
- Interactive Windows/PyQt5 run: not performed because PyQt5 was unavailable.
