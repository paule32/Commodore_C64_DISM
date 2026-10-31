[Deutsch](STAGE421_MATHE_MATRIZEN_ROTATION.md) | [English](STAGE421_MATHE_MATRIZEN_ROTATION.en.md)

# Stage 421 – Matrix Types, Calculations, and Rotation Learning Page

**Basis:** `d64_dism_asm_420.zip` (see the German release notes for the exact baseline).

Based on `d64_dism_asm_420(1).zip`. The Mathematics → Facts → Matrices tree is reorganized into the branches **Types of…** and **Calculating with…**. All 38 existing matrix types remain unchanged under the first branch. **Rotation Matrix** opens a dedicated right-side Qt5/QPainter educational page implemented in `rotation_matrix_fact.py`.

The page illustrates elementary transformations, matrix notation, and a three-dimensional cube with improved placement of explanatory text. The implementation retains existing mathematics modules. Automated layout and integration tests are included; the Windows interactive appearance still requires a native check.

## Source code and command examples (unchanged)

```sh
python -m py_compile d64_dism.py rotation_matrix_fact.py
python -m pytest -q test_stage421_rotation_matrix.py
```

