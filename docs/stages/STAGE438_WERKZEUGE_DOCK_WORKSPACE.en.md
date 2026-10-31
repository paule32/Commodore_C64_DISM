[Deutsch](STAGE438_WERKZEUGE_DOCK_WORKSPACE.md) | [English](STAGE438_WERKZEUGE_DOCK_WORKSPACE.en.md)

# Stage 438 – Tools as a Restorable Full-Area Dock Workspace

**Basis:** `d64_dism_asm_437.zip` (see the German release notes for the exact baseline).

Opening integrated tools (C64 character/palette/text-screen/pixel-screen editors, PO/MO localization, Doxygen documentation, etc.) temporarily hides competing docks and gives the selected tool the available workspace. Closing it restores the previous dock visibility and arrangement rather than permanently changing the user's layout.

The Resource Builder is integrated into the same mechanism. The code keeps a snapshot of the original workspace during tool switches and avoids inconsistent repeated snapshots. Tests inspect the dock switching and restoration paths.
