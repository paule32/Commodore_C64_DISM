[Deutsch](STAGE429_TRIGONOMETRIE_SICHTBEREICH.md) | [English](STAGE429_TRIGONOMETRIE_SICHTBEREICH.en.md)

# Stage 429 – Further Geometry and Viewport Adjustments for Trigonometry

**Basis:** `d64_dism_asm_428.zip` (see the German release notes for the exact baseline).

Stage 429 modifies `trigonometry_right_triangle_fact.py` to improve the visibility and relative positioning of elements in the right-triangle educational diagram. The aim is to avoid clipping and keep labels within the available viewport while retaining the visual relationships.

The new `test_stage429_trigonometry_visibility_and_positions.py` checks placements, and syntax verification passed. The change is confined to the trigonometry teaching page.
