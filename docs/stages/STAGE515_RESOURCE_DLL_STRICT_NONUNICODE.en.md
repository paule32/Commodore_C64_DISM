[Deutsch](STAGE515_RESOURCE_DLL_STRICT_NONUNICODE.md) | [English](STAGE515_RESOURCE_DLL_STRICT_NONUNICODE.en.md)

# Stage 515 – Strict Non-UTF-16 Resource DLLs for ASCII and UTF-8

When building ASCII or UTF-8 resource DLLs, native Windows UTF-16LE text resources are **removed instead of duplicated**. The output still goes to the six architecture/codepage directories and includes `.res`, `.o`, and `.dll`. `UTF-8` is a Unicode encoding, but “no Unicode copies” here specifically means no **extra UTF-16LE standard-format text**.

For non-Unicode builds, the compiler uses compact **numeric custom resource types** (including `0xF004` for MENU, `0xF005` for DIALOG, `0xF006` for STRINGTABLE, and `0xF010` for VERSION). Text bytes use the requested codepage; explicit wide strings are rejected where they would defeat strict output. Standard Unicode builds retain `RT_STRING (6)`, `RT_MENU (4)`, `RT_DIALOG (5)`, and `RT_VERSION (16)` in Windows format. Custom types must be read explicitly using resource APIs; functions such as `LoadStringW` cannot read those formats directly. Tests inspect `.res`, COFF, and DLL payload bytes.

## Source code and command examples (unchanged)

```c
HMODULE mod = LoadLibraryExW(L"Resource32.dll", NULL, LOAD_LIBRARY_AS_DATAFILE);
HRSRC res = FindResourceW(mod, MAKEINTRESOURCEW(1), MAKEINTRESOURCEW(0xF006));
if (res) {
    HGLOBAL loaded = LoadResource(mod, res);
    const unsigned char* raw = (const unsigned char*)LockResource(loaded);
    DWORD count = SizeofResource(mod, res);
    /* raw[0..7] == "D64STR01"; DWORD Codepage ab Offset 8. */
}
FreeLibrary(mod);
```

