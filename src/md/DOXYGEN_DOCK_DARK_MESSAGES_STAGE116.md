# Stage 116 - Doxygen Dock and complete MessageBox dark mode

The uploaded `doxygen(2).py` is the binding Doxygen basis. Existing source lines are preserved; Stage 116 adds a module-local QMessageBox adapter and a QDockWidget factory.

All existing `QMessageBox.critical`, `.warning`, `.information`, and `.question` calls resolve through the adapter without rewriting their call sites. The adapter reuses the main application's `_apply_message_box_theme()` when available and has dark/light fallback QSS.

The main window passes itself into the Doxygen module before `exec_module()`, so even import-time TranslationManager/locale errors already know the current theme. After import the host is rebound explicitly.

The Stage-115 QDockWidget embedding and its layout behavior remain intact, including hiding the filesystem dock before Doxygen takes the free left-side workspace. Runtime source files remain under `d64qt5/`.
