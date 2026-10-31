[Deutsch](STAGE514_RESOURCE_DLL_REAL_CODEPAGE_DATA.md) | [English](STAGE514_RESOURCE_DLL_REAL_CODEPAGE_DATA.en.md)

# Stage 514 – Resource DLL Payloads Actually Follow the Codepage

Fixes Stage 513's directory-only behavior. The compiler now overrides stale `#pragma code_page(...)` for an **in-memory build** without changing the user's source. `RCDATA` and `DLGINCLUDE` text receive actual ASCII, UTF-8, or UTF-16LE bytes as selected, and the PE resource metadata reflects the codepage. Characters not representable in ASCII raw data cause errors before writing invalid output.

Windows-native STRINGTABLE and MENU structures are required to use UTF-16LE internally. For non-Unicode builds Stage 514 therefore also generates separate codepage-encoded text resources named `D64_STRING_CP` and `D64_MENU_CP`; this preserves the native copies at this stage. A precompiled `.res` lacking source cannot always be losslessly recoded. Tests verify the six output combinations, native formats, byte differences, and error cases.
