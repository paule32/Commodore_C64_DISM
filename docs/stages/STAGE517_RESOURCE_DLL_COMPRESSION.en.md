[Deutsch](STAGE517_RESOURCE_DLL_COMPRESSION.md) | [English](STAGE517_RESOURCE_DLL_COMPRESSION.en.md)

# Stage 517 – Resource DLL Compression: Transparent and Custom

Under Environment → Resources, a **Compress DLL** group offers **enable** (default off) and mutually exclusive **transparent** (default) / **custom** modes. Settings are saved independently for Windows 32-/64-bit and passed to DLL creation.

**Transparent** uses Windows NTFS/LZX via `compact.exe /C /EXE:LZX /F /I`. The PE bytes stay logically unchanged and standard Windows APIs keep working, but physical savings depend on filesystem support, and copying/archive operations may remove NTFS compression. **Custom** compresses eligible large custom resource payloads with zlib/DEFLATE, using resource type `0xF117` and a `D64PK001` header carrying original type/ID, sizes, and CRC information. Standard Windows resources remain uncompressed for `LoadStringW` and similar functions; tiny or poorly compressible resources are left uncompressed if packing would enlarge them. `.res` and `.o` remain normal build artifacts. Python decode/check functions are provided, with native support added in Stage 518.

## Source code and command examples (unchanged)

```ini
[Settings.Windows.32Bit.Environment]
ResourceDLLCompressEnabled = true
ResourceDLLCompressMode = custom

[Settings.Windows.64Bit.Environment]
ResourceDLLCompressEnabled = true
ResourceDLLCompressMode = transparent
```


```
Byte  Länge  Beschreibung
0     8     ASCII-Magic D64PK001
8     2     original resource type (uint16 LE)
10    2     original resource id (uint16 LE)
12    2     LANGID (uint16 LE)
14    4     codepage (uint32 LE)
18    4     original payload byte length (uint32 LE)
22    4     CRC32 of original bytes (uint32 LE)
26    ...   zlib compressed byte stream
```

