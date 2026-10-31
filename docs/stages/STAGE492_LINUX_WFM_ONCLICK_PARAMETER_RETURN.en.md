[Deutsch](STAGE492_LINUX_WFM_ONCLICK_PARAMETER_RETURN.md) | [English](STAGE492_LINUX_WFM_ONCLICK_PARAMETER_RETURN.en.md)

# Stage 492 – Linux WFM: OnClick Parameters and RETURN

Improves Linux form event compilation so `OnClick` procedures/functions accept parameters and return values. The Qt signal `QAbstractButton::clicked(bool)` supplies its Boolean state as the first callback parameter when declared; parameter names are arbitrary because mapping is positional. Event expressions such as `? Sender` and `LOCAL X = Checked` resolve in the proper event scope. `RETURN` from event routines follows the generated Linux calling convention and must not corrupt the form event loop. Tests cover declaration variants, argument mapping, and generated ELF32/ELF64 code; actual GUI event delivery needs native Qt validation.

## Source code and command examples (unchanged)

```dbase
CLASS Form1 OF FORM
THIS.PushButton1 = NEW BUTTON()
THIS.PushButton1.OnClick = CLASS::PushButton1_onClick

PROCEDURE PushButton1_onClick(Sender, Checked)
    ? "Hallo aus dem Qt5-Terminal"
    ? Sender
    LOCAL Zustand = Checked
    ? Zustand
    RETURN
ENDCLASS
```

