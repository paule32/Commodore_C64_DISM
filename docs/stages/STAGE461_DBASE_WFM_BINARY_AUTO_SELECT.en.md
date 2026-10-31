[Deutsch](STAGE461_DBASE_WFM_BINARY_AUTO_SELECT.md) | [English](STAGE461_DBASE_WFM_BINARY_AUTO_SELECT.en.md)

# Stage 461 – WFM .ui.bin and Automatic Selection of the Smaller EXE Payload

Introduces the compact **WUIB version 1** binary UI representation alongside `.ui.json`. With external UI components off, WFM compilation follows the legacy path. With external components on, settings choose readable JSON, Qt-compatible compressed JSON, or binary UI payload as appropriate. The compiler can compare representations and embed the smaller supported payload, including the Qt-style big-endian size prefix where required. Project settings, format converters, and size-analysis tests are provided. Existing WFM behavior should not change when these options are disabled.
