[Deutsch](STAGE516_WINDOWS_RESOURCE_MAPPING.md) | [English](STAGE516_WINDOWS_RESOURCE_MAPPING.en.md)

# Stage 516 – Windows Resource Mapping Project Settings

The Project Settings tree gains **Windows → 32-Bit/64-Bit → Environment → Resources**, with a **Mapping** group. ASCII and UTF-8 each have two choices, **without UTF-16 LE Copy** (default) or **with UTF-16 LE Copy**; Unicode always displays **UTF-16 LE Windows Standard**. Win32 and Win64 settings are independent and saved in `.pro` sections `[Settings.Windows.32Bit.Environment]` and `[Settings.Windows.64Bit.Environment]` using `ResourceASCIINativeUTF16Copy` and `ResourceUTF8NativeUTF16Copy` booleans.

**Without** emits only the custom, codepage-encoded types `0xF004`, `0xF005`, `0xF006`, and `0xF010`. **With** adds native Windows RT_MENU/RT_DIALOG/RT_STRING/RT_VERSION copies alongside them, permitting `LoadStringW`, `LoadMenu`, and related APIs to use the native data. Existing projects default to no copy. Tests cover serialization, per-architecture differences, and RES/COFF/DLL generation.
