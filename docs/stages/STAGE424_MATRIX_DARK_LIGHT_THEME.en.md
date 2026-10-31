[Deutsch](STAGE424_MATRIX_DARK_LIGHT_THEME.md) | [English](STAGE424_MATRIX_DARK_LIGHT_THEME.en.md)

# Stage 424 – Matrix Pages Follow Dark and Light Themes

**Basis:** `d64_dism_asm_423.zip` (see the German release notes for the exact baseline).

Stage 424 makes the **Multiplication** and **Move 3-D** pages respond to the application's active dark/light mode. Backgrounds, gradient or flat panels, titles, text, formulas, and matrix cells receive matching colors, and a theme switch refreshes the pages.

A Qt-independent helper, `math_matrix_theme.py`, centralizes palette decisions. Both `rotation_matrix_fact.py` and `multiplication_matrix_fact.py` are updated. Existing functional tests continue; visual behavior should be checked with both themes and different viewport sizes.
