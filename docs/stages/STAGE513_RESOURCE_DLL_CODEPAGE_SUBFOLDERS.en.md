[Deutsch](STAGE513_RESOURCE_DLL_CODEPAGE_SUBFOLDERS.md) | [English](STAGE513_RESOURCE_DLL_CODEPAGE_SUBFOLDERS.en.md)

# Stage 513 – Architecture- and Codepage-Specific Resource DLL Directories

Resource DLL output is organized by architecture and selected codepage: `win32/unicode`, `win32/utf8`, `win32/ascii`, and corresponding `win64/...` directories. Each build writes `<source>.res`, `<source>.o`, and `<source>.dll` in that subdirectory. `resource_dll_codepage_directory()` maps codepage 1200 to Unicode, 65001 to UTF-8, and 20127 to ASCII, rejecting unsupported explicit selections. The editor captures the selected combo-box value before source recompilation can reset the UI. At this stage, directory selection alone did not yet guarantee that every payload was reencoded; Stage 514 addresses that.
