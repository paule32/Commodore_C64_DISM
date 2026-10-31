[Deutsch](STAGE448_DBASE_UNIFIED_RUNTIME_DLL.md) | [English](STAGE448_DBASE_UNIFIED_RUNTIME_DLL.en.md)

# Stage 448 – Unified dBASE Runtime DLL

The previous console runtime is consolidated under the single filename **`c64_dbase_runtime.dll`**, built separately as `d64dbase/bin/pe32/c64_dbase_runtime.dll` and `d64dbase/bin/pe64/c64_dbase_runtime.dll`. Internal builders `d64dbase.console_runtime.build_dll` and `d64dbase.runtime_builder.create_runtime_dll` cooperate with the PE toolchain. Existing Tools menu actions and per-architecture output-directory settings remain. Common exported functions and their string ABI are documented, while later additions can extend the shared runtime without introducing more DLL names. Compatibility and actual loader behavior still need Windows integration checks.
