# Stage 44A - Qt5/MinGW32 compile fix

Stage 44A is a compile-only correction on top of Stage 44.

## 1. Incomplete `ServerDialog` type

`RemoteClientEventFilter` is compiled before the full `ServerDialog` class
body. At that point only `class ServerDialog;` is known. Therefore GCC cannot
implicitly compare a `QWidget *` with `ServerDialog *`, because the inheritance
relationship is not visible yet.

The comparison now uses the same explicit QWidget reinterpretation already
used by the earlier Stage-44 remote-window filtering code:

```cpp
if (!top
    || top == reinterpret_cast<QWidget *>(g_server_dialog)
    || top == g_remote_cursor_marker)
```

No object ownership or runtime behavior is changed.

## 2. `make_zoom_button` declaration

`ServerDialog` uses the common client zoom helper before its definition later
in the translation unit. Stage 44A adds the forward declaration:

```cpp
QToolButton *make_zoom_button(bool plus, QWidget *parent);
```

The existing implementation remains unchanged.

## 3. Legacy warning

`show_btx_dialog()` is still unused legacy code. Its `-Wunused-function`
diagnostic is a warning and is intentionally not part of this minimal compile
fix.
