[Deutsch](STAGE459_QT5_ORDINAL_MAP_HASH_FIX.md) | [English](STAGE459_QT5_ORDINAL_MAP_HASH_FIX.en.md)

# Stage 459 – Qt5 Runtime ABI and Export-Hash Correction

Fixes mismatches between the compiler's imported Qt5 symbols and the bridge DLL ABI. The stable 64-export core is filtered consistently in `d64_dism.py`, and `d64qt5/generate_runtime_abi.py` adopts the same name/hash mapping. `d64qt5/README.md` documents the stable core ABI and additional name exports. This prevents ordinal or hash inconsistencies from silently targeting the wrong Qt5 function. The updated generator and integration paths are tested, while true native DLL loading must still be checked with the corresponding Windows binaries.
