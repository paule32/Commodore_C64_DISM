# Stage 37A - Dialog DPI compile fix

This corrective stage keeps the Stage 37 DPI/grid behaviour and fixes two C++ build regressions in `d64qt5_bridge.cpp`.

## Fixed

- `AsciiPopupMenu::paintEvent()` now defines `ch` and `topBaseline` before use.
- `grid_text_baseline(...)` has a forward declaration before `AsciiPopupMenu`, while the shared definition remains with the common grid helpers.
- `LoginDialog::paintEvent()` now consistently draws the top and side borders using `topBaseline` / `grid_text_baseline(...)`; stale references to an undeclared `ascent` variable were removed.

No one-pixel fine-tuning was restored. Dialog geometry and border baselines continue to derive from the actual 80x25 console font metrics.

## Windows rebuild

From the `d64qt5` directory:

```text
mingw32-make clean
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

`-lgdi32` remains present in the qmake project for the Workstation panel/EXIT/BTX drawing code.
