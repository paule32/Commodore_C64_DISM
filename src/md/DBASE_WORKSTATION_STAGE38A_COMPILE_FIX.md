# Stage 38A - Workstation DB callback compile fix

Stage 38A is a minimal compile correction on Stage 38.

The DB icon callback calls `enforce_console_80x25_grid()` before the function definition.
The function is now forward-declared with the other runtime helpers before the callback is compiled.

No C ABI, Workstation behavior, EXIT/JA-NEIN logic, BTX.exe launch logic, DATABASE behavior, or project/compiler behavior changes.

The old internal `show_btx_dialog()` helper remains as legacy code in this minimal fix; it is not called by the BTX Workstation callback. Its `-Wunused-function` diagnostic is a warning only and does not affect the DLL build.
