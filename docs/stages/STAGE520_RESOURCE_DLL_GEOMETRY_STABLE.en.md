[Deutsch](STAGE520_RESOURCE_DLL_GEOMETRY_STABLE.md) | [English](STAGE520_RESOURCE_DLL_GEOMETRY_STABLE.en.md)

# Stage 520 – Keep Main-Window and Dock Geometry Unchanged during DLL Build

Fixes an issue where clicking **win32 DLL** (and potentially **win64 DLL**) could alter the main-window width, Resource Editor dock size, or splitter layout. The build previously rebuilt the resource tree/preview, switched displayed compiler targets, and placed an overly long output path into a dock `QLabel`; Qt could interpret that text as a larger minimum width.

`WindowsResourceEditorWidget._resource_dll_source_entries()` now compiles `.rc` or loads `.res` entries **for the build only**, without `_populate_tree()` or re-layout of tree/properties/hex views; unsaved RC text is persisted as before. `compile_to_resource_dll()` passes these temporary entries to `build_resource_dll_files()` without calling `set_target()`. Status/path labels use `QSizePolicy.Ignored`, `minimumWidth=0`, and `Qt.ElideMiddle` to stay within the current width; full paths remain in tooltips and the main status bar. Older integrations retain a compatibility fallback, and the toolbar's 14-pixel spacing remains. Focused geometry/regression tests passed, but live Windows/PyQt5 visual validation is still needed.
