[Deutsch](STAGE437_UEBER_DIALOGE_DARKMODE.md) | [English](STAGE437_UEBER_DIALOGE_DARKMODE.en.md)

# Stage 437 – About and About Qt5 Dialogs in Dark and Light Modes

**Basis:** `d64_dism_asm_436.zip` (see the German release notes for the exact baseline).

Both Help → **About** and **About Qt5** now open a shared modal `D64AboutDialog`. The dialog has a custom frameless Qt5 window, a **3-pixel border**, draggable title bar, a painted close X in the upper-right, and an **OK** button.

In dark mode the title bar transitions from black (`#000000`) to gray (`#707070`); light mode uses bright backgrounds and dark readable text. The correct information is shown for each menu item. Tests check the dialog creation and the theme-dependent styles.
