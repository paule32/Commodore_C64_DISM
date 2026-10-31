[Deutsch](STAGE425_ZAHLEN_MENGEN_SINGLE_CLICK.md) | [English](STAGE425_ZAHLEN_MENGEN_SINGLE_CLICK.en.md)

# Stage 425 – Number Sets, Single Click, and Collapsed Matrix Types

**Basis:** `d64_dism_asm_424.zip` (see the German release notes for the exact baseline).

A **Number Sets** leaf is inserted first under Mathematics → Facts → Basic Knowledge, opening a new educational QPainter page in `number_sets_fact.py`. The diagram uses filled QPainter paths/rounded rectangles and actual text rendering rather than a bitmap copy of the supplied reference.

Mathematics tree leaves now activate the corresponding right-hand page with a **single click**. Matrix-type groups start collapsed, reducing clutter on initial display. Existing matrix and mathematics navigation remain available. Tests cover the tree changes and page initialization; exact visual fidelity requires Windows/Qt validation.
