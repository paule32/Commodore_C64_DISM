[Deutsch](STAGE455_DBASE_DLL_PAYLOAD_LOADER.md) | [English](STAGE455_DBASE_DLL_PAYLOAD_LOADER.en.md)

# Stage 455 – D64Z/MSZIP Payload in the dBASE Runtime DLL

The meaning of the dBASE runtime **pack dll** option expands beyond transparent filesystem compression: `d64dbase/pe_dll_payload.py` handles PE analysis, a D64Z-compressed payload, loader logic, and relocation processing. `d64dbase/console_runtime.py` emits additional loader imports only when packing is enabled, and `runtime_builder.py` integrates the payload loader into manual builds. The architecture must still produce a valid PE image which Windows can load. The source documentation distinguishes payload placement, size measurements, and tests from Windows runtime verification; merely compressing an entire DLL with zlib would not be loadable.

## Source code and command examples (unchanged)

```
python -m pytest -q test_stage455_d64z_runtime_dll_payload.py
```

