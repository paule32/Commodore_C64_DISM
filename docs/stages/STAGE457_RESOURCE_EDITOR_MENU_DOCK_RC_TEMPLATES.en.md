[Deutsch](STAGE457_RESOURCE_EDITOR_MENU_DOCK_RC_TEMPLATES.md) | [English](STAGE457_RESOURCE_EDITOR_MENU_DOCK_RC_TEMPLATES.en.md)

# Stage 457 – Resource Editor Menu, Dock Workspace, and RC Templates

Integrates a Windows Resource Editor into the Tools menu and the application's restorable full-area dock workspace. The editor supplies RC templates for **DIALOGEX** dialogs, `STRINGTABLE`, and file-based `ICON`, `BITMAP`, and `CURSOR` resources, including appropriate IDs and editable source text. Workspace switching hides/restores other docks without losing project state. Additional error handling addresses a crash when opening recently used projects. Tests check menu wiring, docking, template contents, and error paths; native GUI interaction remains to be verified.
