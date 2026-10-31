[Deutsch](STAGE519_RESOURCE_EDITOR_PROJECT_SETTINGS_BUILD.md) | [English](STAGE519_RESOURCE_EDITOR_PROJECT_SETTINGS_BUILD.en.md)

# Stage 519 – Resource Editor DLL Buttons Honor Live Project Settings

Fixes the wiring between the open Resource Editor and **Project Settings → Windows → Environment → Resources**. When clicking **win32 DLL** or **win64 DLL**, the editor freshly reads the current mapping and compression options for the **corresponding architecture**, even if settings changed after the resource editor was opened or have not yet been explicitly saved.

A unified architecture-specific build configuration replaces fragmented callbacks, with backward-compatible fallback for older editor integrations. The build uses ASCII/UTF-8 optional native UTF-16LE copies, Unicode defaults, and **Compress DLL enable/transparent/custom** selections. Output paths remain under the chosen architecture/codepage directory. The status message reports the actual applied settings. Tests use differing Win32/Win64 settings and verify live updates, compression arguments, and old call routes.
