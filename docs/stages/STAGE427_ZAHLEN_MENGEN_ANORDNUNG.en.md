[Deutsch](STAGE427_ZAHLEN_MENGEN_ANORDNUNG.md) | [English](STAGE427_ZAHLEN_MENGEN_ANORDNUNG.en.md)

# Stage 427 – Corrected Number-Set Diagram Arrangement

**Basis:** `d64_dism_asm_426.zip` (see the German release notes for the exact baseline).

Stage 427 repairs placement problems in the Number Sets teaching page. A shared set of column boundaries, `COLUMN_EDGES`, defines a consistent grid of **three bands** and ordered number-set columns (including 0, natural numbers ℕ, and successive larger sets).

Examples and set notation are attached to their proper columns instead of positioned independently. The rational value `¾` no longer collides with `-15,7889`, and **imaginary part** appears only once as a vertical label. The result follows the user's diagram more closely while remaining a drawn Qt page. Targeted geometry tests verify positioning.
