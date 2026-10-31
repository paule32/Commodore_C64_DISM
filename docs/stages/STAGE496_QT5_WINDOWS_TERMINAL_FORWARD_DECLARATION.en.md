[Deutsch](STAGE496_QT5_WINDOWS_TERMINAL_FORWARD_DECLARATION.md) | [English](STAGE496_QT5_WINDOWS_TERMINAL_FORWARD_DECLARATION.en.md)

# Stage 496 – Qt5 Windows DLL: Missing Forward Declaration

Fixes a MinGW C++ build error in the Windows Qt5 bridge caused by a missing forward declaration. The necessary type/function declaration is made visible before first use without changing ABI-facing exports. The documentation gives the MSYS2 MinGW32 build invocation and identifies remaining target-environment limitations. This addresses a specific compilation failure rather than claiming all Qt runtime issues are resolved.

## Source code and command examples (unchanged)

```
'append_dbase_qt_terminal' was not declared in this scope
```


```cpp
static void show_wfm_output_dialog(QWidget *reference);
static void append_wfm_output(const QString &value, bool newline);
static void append_dbase_qt_terminal(const QString &text, bool newline);
static void apply_wfm_debug_theme();
```


```sh
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

