# Stage 36 GDI link fix

The EXIT icon in `d64_workstation.cpp` draws with Win32 GDI.
MinGW32 therefore needs `-lgdi32`.

Updated qmake line:

```qmake
win32:LIBS += -luser32 -lgdi32 -ladvapi32 -lodbc32
```

The standalone smoke-test build command was updated in the same way.
