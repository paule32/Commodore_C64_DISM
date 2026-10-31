[Deutsch](STAGE435_DESKTOP_PROPERTIES_SEITLICHES_DOCKING.md) | [English](STAGE435_DESKTOP_PROPERTIES_SEITLICHES_DOCKING.en.md)

# Stage 435 – Desktop Properties Docking beside Project Information

**Basis:** `d64_dism_asm_434.zip` (see the German release notes for the exact baseline).

The **Desktop Properties** panel can dock horizontally beside the Project Information area rather than disrupting the existing project/file-system stack. Docking, splitting, and restoring are coordinated with the application's saved workspace layout.

The change preserves the user's preferred geometry unless a docking operation is explicitly requested. Tests examine position/state restoration, while full Qt drag-and-drop behavior requires interactive validation.
