[Deutsch](STAGE423_ROTATION_MATRIX_LAYOUT_TWEAK.md) | [English](STAGE423_ROTATION_MATRIX_LAYOUT_TWEAK.en.md)

# Stage 423 – Fine-Tuning the Move 3-D Matrix Layout

**Basis:** `d64_dism_asm_422.zip` (see the German release notes for the exact baseline).

Starting from Stage 422, `rotation_matrix_fact.py` adjusts the lower result matrix: it shifts approximately **10 pixels left** and widens the lower tiles/columns by around **10 pixels**. This is a narrowly scoped visual correction, not a change to matrix mathematics or the rest of the interface.

`test_stage423_rotation_matrix_layout_tweak.py` was added, and Python syntax checks passed. The corresponding changes should be assessed at the target DPI and window size.
