[Deutsch](STAGE458_DBASE_WFM_UTF8_RUNTIME_UI_PAYLOAD.md) | [English](STAGE458_DBASE_WFM_UTF8_RUNTIME_UI_PAYLOAD.en.md)

# Stage 458 – UTF-8 WFM Runtime Strings and PE Form JSON

The Qt5 bridge runtime `libd64_qt5.dll` now handles UTF-8 WFM strings consistently. The documentation clarifies where `Form1.ui.json` lives inside a compiled PE form: with **compress json off**, uncompressed JSON bytes are stored in `.data`; when enabled, a Qt `qCompress`-compatible format is embedded (big-endian 32-bit original length followed by zlib data). The separate D64Z/MSZIP EXE packer compresses `.text` and does **not** automatically compress this JSON block. Tests check encoding, payload structure, and runtime access without conflating two compression layers.

## Source code and command examples (unchanged)

```powershell
python -m d64dbase.wfm_external_ui "T:\\Pfad\\MeinProgramm.exe"
```

