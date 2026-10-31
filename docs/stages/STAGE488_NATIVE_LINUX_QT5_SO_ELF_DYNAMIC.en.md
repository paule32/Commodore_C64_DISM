[Deutsch](STAGE488_NATIVE_LINUX_QT5_SO_ELF_DYNAMIC.md) | [English](STAGE488_NATIVE_LINUX_QT5_SO_ELF_DYNAMIC.en.md)

# Stage 488 – Native Linux Qt5 Shared Library and Dynamic ELF Linker

Extends ELF32/ELF64 support to relocatable ET_REL objects and dynamically linked ET_EXEC executables, inspected with `readelf -d`. GNU AT&T and Intel assembly paths can produce WFM objects for dynamic linking. Linux Qt5 integration is designed to call `libd64_qt5.so` from generated forms. A real ELF64 test used a separate **dummy shared library**, not the full Qt5 bridge. The actual Qt form library could not be compiled in the available environment because Qt5 development components were missing. Documentation and tests keep this limitation explicit.

## Source code and command examples (unchanged)

```sh
sudo apt update
sudo apt install build-essential qtbase5-dev qt5-qmake
cd d64qt5
./build_linux.sh
```


```c
int DBaseQtRunFormJson(const char *utf8Json);
```

