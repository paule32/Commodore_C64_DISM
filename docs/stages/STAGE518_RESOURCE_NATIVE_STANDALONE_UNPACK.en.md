[Deutsch](STAGE518_RESOURCE_NATIVE_STANDALONE_UNPACK.md) | [English](STAGE518_RESOURCE_NATIVE_STANDALONE_UNPACK.en.md)

# Stage 518 – Native Custom Resource Decoder for Standalone EXEs and DLLs

Adds `native/d64resource/d64resource.c` and `.h`, a C-ABI decoder for the Stage-517 `D64PK001` format. It can be linked statically into a Windows standalone EXE or built as an external `d64resource.dll` for PE32/PE32+. Python is **not required** at runtime. Public functions include `D64ResourceInspect(record,size,info)`, `D64ResourceDecode(record,size,buffer,capacity,info)`, and `D64ResourceReadModuleW(module,original_type,original_id,language,buffer,capacity,info)`.

The decoder parses the header, validates lengths, uses zlib, and checks CRC32, working with caller-owned buffers. Windows resource lookup can find a packed entry by its **original type/ID/language**, without knowing the internal `0xF117` ID, and can also return uncompressed resources. The project includes Windows MSYS2/MinGW build instructions, a C example, and Pascal import declarations. Linux-native C compatibility tests passed; an actual Windows 32-/64-bit DLL build and LoadLibrary integration test remain outstanding.
