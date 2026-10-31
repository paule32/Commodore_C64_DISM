[Deutsch](STAGE485_NATIVE_LINUX_TITLEBAR.md) | [English](STAGE485_NATIVE_LINUX_TITLEBAR.en.md)

# Stage 485 – Native Linux Title Bar, Existing Custom Windows Title Bar

Platform-specific window decoration is introduced. On **Windows** (`sys.platform == "win32"`), the custom `GreenBeigeTitleBar`, `Qt.FramelessWindowHint`, 3-pixel window border, and manual resize controls remain unchanged. On **Linux**, the main Qt window uses the window manager's native title bar, explicitly removing frameless hints and custom border margins; other platforms likewise prefer native decoration. This avoids fake Windows title-frame behavior under Linux while keeping Windows UI expectations. Source-based checks cover the branching; native desktop validation is still needed.

## Source code and command examples (unchanged)

```python
self._use_custom_main_title_bar = sys.platform == "win32"
```

