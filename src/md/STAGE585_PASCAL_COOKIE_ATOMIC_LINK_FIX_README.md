# Stage 585 – MinGW32 Linkfehler `InterlockedCompareExchange@12` korrigiert

**Verbindliche Basis:** `d64_dism_stage584.zip`.

## Gemeldeter Fehler

Beim Bau der PE32-Runtime in MSYS2 MINGW32 / GCC 16.1.0:

```text
win32/obj/pas_cookie32.o:pascal/cookie32.as:(.text+0x32):
undefined reference to `InterlockedCompareExchange@12'
collect2.exe: error: ld returned 1 exit status
relocation link error.
```

## Ursache

Die Stage-583-Routine `runtime/pascal/cookie32.asm` deklarierte
`extern _InterlockedCompareExchange@12` und verwendete einen direkten `call`.
Die aktuelle Windows/MinGW32-Importbibliothek löst diesen Namen nicht auf.
In C wird `InterlockedCompareExchange` häufig als Compiler-Intrinsic oder
Makro umgesetzt, sodass ein identischer externer NASM-Funktionsaufruf
nicht vorausgesetzt werden darf.

## Umsetzung

Die Initialisierung des 32-Bit-Stack-Cookies bleibt in der Runtime DLL;
allein der atomare **First-Writer** nutzt jetzt die native x86-Anweisung:

```asm
    mov edx, [ebp-4]             ; 32-Bit-CSPRNG-Ergebnis
    or edx, 1                    ; niemals Null als Guard speichern
    mov ecx, [ebp+8]             ; Pointer nach BCryptGenRandom neu laden
    xor eax, eax                 ; erwarteter alter Wert: 0
    lock cmpxchg dword [ecx], edx
```

`CMPXCHG` schreibt den neuen Wert `EDX` nur dann, wenn der Guard bisher
Null war. Andernfalls bleibt der bereits von einem anderen Thread gesetzte
Wert bestehen. Das `LOCK`-Präfix macht diesen Vergleich/Schreibzugriff
atomar. `EAX` und `ECX` sind im 32-Bit-cdecl-ABI volatile, daher sind
keine zusätzlichen Callee-Saved-Register betroffen.

**Nicht verändert:** DLL-Exportnamen, Pascal-Codegenerator, 4-Byte-Guard
pro Modul, `BCryptGenRandom`, Fail-Fast (`RaiseFailFastException`,
`ExitProcess`), PE64, CES und die MSZIP-Loaderlogik. Die Optionen aus
Stage 584 zum Vermeiden von Runtime-Pseudo-Relocations bleiben erhalten.

**Dateien:**

- `runtime/pascal/cookie32.asm`: extern/call entfernt, `lock cmpxchg` eingefügt.
- `test_stage583.py`: bisherige API-Annahme an die neue Architektur angepasst.
- `test_stage585.py`: neue Regressionstests zu Symbolen, ABI und beiden Buildpfaden.

## Erneuter Build unter Windows

In der **MSYS2 MINGW32**-Shell im Projektstamm:

```bash
cd runtime
bash build.win32.sh
```

Optional für den alternativen Buildbaum:

```bash
cd runtime/compiler
bash build.win32.sh
```

Danach aus dem Projektstamm:

```bash
python runtime/pascal/verify_cookie_runtime.py runtime/win32/libd64_runtime.dll
```

Für den alternativen Buildbaum stattdessen
`runtime/compiler/win32/libd64_runtime.dll` angeben. Für Runtime-Tests muss
die neue DLL in den tatsächlichen EXE-Ausgabeordner bereitgestellt werden.

## Validierungsgrenze

Quellcode-/Regressionstests sind automatisiert möglich; eine native
Windows-Link-/Laufzeitbestätigung mit exakt MSYS2 MINGW32 GCC 16.1.0
und NASM ist in der hier verwendeten Umgebung nicht verfügbar.

Die im Archiv mitgelieferte ältere `libd64_runtime.dll` wurde **nicht**
als neu kompilierte Version ausgegeben. Sie muss durch den erfolgreichen
Windows-Build ersetzt werden.
