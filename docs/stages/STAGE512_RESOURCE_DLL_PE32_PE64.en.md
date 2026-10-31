[Deutsch](STAGE512_RESOURCE_DLL_PE32_PE64.md) | [English](STAGE512_RESOURCE_DLL_PE32_PE64.en.md)

# Stage 512 – Build Win32 and Win64 Resource DLLs from the Editor

Two buttons, **win32 DLL** and **win64 DLL**, are added to the Resource Editor immediately after Refresh with a **14-pixel** gap. They build a Windows PE32 i386 or PE32+ AMD64 resource-only DLL, plus accompanying Microsoft `.res` and architecture-specific COFF `.o` files. `write_res()` and `write_resource_coff()` are reused, while the internal PE writer builds a valid `.rsrc` directory and sets a zero entry point rather than linking an executable code section. The custom dock title bar uses white decoration in dark mode and black in light mode. Tests validate PE headers, resource types, and both architectures; live Windows loading is a separate check.

## Source code and command examples (unchanged)

```
Quellverzeichnis/
  Resource32.rc
  win32/
    Resource32.res
    Resource32.o
    Resource32.dll
  win64/
    Resource32.res
    Resource32.o
    Resource32.dll
```

