[Deutsch](STAGE422_MATHE_MATRIZEN_MULTIPLIKATION_DARKMODE.md) | [English](STAGE422_MATHE_MATRIZEN_MULTIPLIKATION_DARKMODE.en.md)

# Stage 422 – Matrix Multiplication, Dark Mode, and Tree Icons

**Basis:** `d64_dism_asm_421.zip` (see the German release notes for the exact baseline).

The mathematics/matrix tree now displays icons before its labels. A **Multiplication** leaf is inserted under **Calculating with…**, and the former **Rotation Matrix** entry is renamed **Move 3-D**. The new `multiplication_matrix_fact.py` uses QPainter to show matrix multiplication in a separate right-side teaching page.

New mathematics pages initially use a dark visual style, with coordinated backgrounds, tiles, headings, formulas, and text. Existing Stage-421 tests remain, and new tests verify node ordering, page registration, and rendering-related state. Qt presentation on Windows still needs visual validation.
