[Deutsch](STAGE441_DBASE_LEN_LTRIM_RTRIM_TRIM.md) | [English](STAGE441_DBASE_LEN_LTRIM_RTRIM_TRIM.en.md)

# Stage 441 – LEN, LTRIM, RTRIM, and TRIM in the dBASE Compiler

The dBASE compiler gains `LEN(string_expression)` returning a numeric length; native dBASE string storage here uses CP1252 bytes. `LTRIM` removes only leading spaces (`0x20`). `RTRIM` removes trailing spaces, TAB (`0x09`), LF (`0x0A`), backspace (`0x08`), and CR (`0x0D`). `TRIM` applies that whitespace set at both ends. The implementation updates `d64dbase/compiler.py` and adds `d64dbase/string_length_trim.py` with runtime helpers for PE32 and PE32+. Analysis, constant evaluation, and generated assembly use consistent semantics. Test coverage is described in the source notes; the build does not constitute an end-to-end Windows GUI check.
