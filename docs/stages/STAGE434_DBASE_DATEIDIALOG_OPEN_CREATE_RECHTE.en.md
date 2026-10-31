[Deutsch](STAGE434_DBASE_DATEIDIALOG_OPEN_CREATE_RECHTE.md) | [English](STAGE434_DBASE_DATEIDIALOG_OPEN_CREATE_RECHTE.en.md)

# Stage 434 – dBASE File Dialog: Create, Open, and Cancel

**Basis:** `d64_dism_asm_433.zip` (see the German release notes for the exact baseline).

Based on Stage 433, the dBASE project file dialog gains explicit **Create**, **Open**, and **Cancel** workflows with corresponding access checks. Existing files should be opened rather than silently overwritten; creating a new file requires a valid destination and permissions.

The dialog distinguishes user cancellation from errors, validates paths and extension/type choices, and updates the project tree only after a successful file operation. Tests cover file-dialog behavior and permission handling.
