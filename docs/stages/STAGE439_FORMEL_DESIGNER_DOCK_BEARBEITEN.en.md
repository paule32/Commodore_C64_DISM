[Deutsch](STAGE439_FORMEL_DESIGNER_DOCK_BEARBEITEN.md) | [English](STAGE439_FORMEL_DESIGNER_DOCK_BEARBEITEN.en.md)

# Stage 439 – Formula Designer: Full-Area Dock and Edit Menu

**Basis:** `d64_dism_asm_438.zip` (see the German release notes for the exact baseline).

The Formula Designer becomes a full-workspace dock. Its opening saves other dock and central-editor visibility, hides them, and uses the free area; closing it restores the original workspace and main-window geometry. Switching between tools retains the initial snapshot.

The main **Edit** menu is connected to the active formula editor, including Undo/Redo and other applicable actions. Existing View → Zoom handling is preserved. Tests verify command routing and workspace restoration.
