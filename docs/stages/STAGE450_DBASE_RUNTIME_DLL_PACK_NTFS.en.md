[Deutsch](STAGE450_DBASE_RUNTIME_DLL_PACK_NTFS.md) | [English](STAGE450_DBASE_RUNTIME_DLL_PACK_NTFS.en.md)

# Stage 450 – dBASE Runtime DLL: Transparent NTFS Packing

A **pack dll** checkbox is added to the dBASE Runtime group in Windows → 32-bit / 64-bit → Environment → Input. The two architectures save independent `DBaseRuntimeDLLPack` booleans under their existing `.pro` INI sections; the default is false. All manual and automatic runtime-DLL build paths read the same setting. Stage 450 chooses **transparent NTFS compression** with `FSCTL_SET_COMPRESSION` via `DeviceIoControl`, not a zlib-replaced DLL or an EXE unpacking stub. PE headers, imports/exports, and instructions remain byte-identical and usable by `LoadLibrary`. NTFS permissions and a suitable volume are required; a small 4–5 KB DLL might not save any space, and ZIP/copy operations need not preserve the NTFS compression attribute.
