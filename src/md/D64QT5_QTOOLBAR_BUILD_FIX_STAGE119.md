# Stage 119 — d64qt5 QToolBar build fix

The Stage 118 runtime creates a `QToolBar` in `DBaseQtControlCreate`, but included only `QMainWindow`, whose header forward-declares `QToolBar`.

Added exactly:

```cpp
#include <QToolBar>
```

No runtime logic was changed. The `show_btx_dialog()` unused-function warning is non-fatal and intentionally unchanged.
