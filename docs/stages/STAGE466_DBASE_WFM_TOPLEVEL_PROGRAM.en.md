[Deutsch](STAGE466_DBASE_WFM_TOPLEVEL_PROGRAM.md) | [English](STAGE466_DBASE_WFM_TOPLEVEL_PROGRAM.en.md)

# Stage 466 – Executable dBASE Code outside CLASS Form1

Fixes WFM projects containing executable top-level statements before the form class. `wfm_executable_preamble()` in `d64dbase/wfm.py` extracts the program preamble; `d64_dism.py` emits the remaining executable top-level code as an internal method called in the correct startup sequence. Global typed variables are shared consistently between preamble and event methods. The fix distinguishes declarations, class structure, and executable code so statements are not silently ignored or moved into the wrong scope. Tests address compilation and initialization order.
