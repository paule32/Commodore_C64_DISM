# Stage 583 – Pascal-Stack-Cookie nach PE32-Runtime verschoben; CES/MSZIP-Loader geprüft

**Verbindliche Basis:** `d64_dism_stage582.zip`.

## 1. Analyse: Was ist wirklich im Loader?

Der PE32-Loader in `d64_dism.py` ruft über die Windows Compression API (`CreateDecompressor`, `Decompress`, `CloseDecompressor`) die MSZIP-Dekompression auf, passt Speicherschutz an, stellt das gepackte `.text`-Image wieder her und löst D64I-Imports auf. Er enthält **keinen selbst implementierten MSZIP-Algorithmus**. Diese Bootstrap-Arbeit muss vor dem normalen Programmstart laufen. Eine Verlagerung in `libd64_runtime.dll` würde eine zirkuläre Abhängigkeit erzeugen, wenn diese DLL erst über den D64I-Resolver geladen werden soll.

Bei einer zusätzlichen Kompression des Second-Stage-Loaders (Stage 539) wird **nur dann** ein eigener Bootstrap aufgenommen, wenn dies in der ausgerichteten PE-Datei tatsächlich wenigstens einen Dateialignment-Block einspart. Sonst bleibt der bereits vorhandene Loader unkomprimiert.

CES ist dagegen optional: `_build_pe32_mszip_loader(..., ces_enabled=False)` baut keine CES-Fehlermeldungsroutine ein. Ein Stage-583-Test mit absichtlich global aktiviertem CES und explizit deaktivierter Build-Option ergibt:

| CES | Größe eines repräsentativen PE32-Loaders | Kennzeichnungen / Dialog |
|---|---:|---|
| OFF | 733 Byte | weder `CES:` noch `MessageBoxA`, `user32.dll` |
| ON | 959 Byte | CES-Fehlerdialog-Routinen enthalten |

Das sind Größen **nur dieses synthetischen Test-Loadercodes**, nicht die gesamte fertige EXE. Der D64I-Importresolver und die generelle Fehlerbehandlung bleiben auch bei CES OFF technisch erforderlich. Die bestehende CES-Link-Snapshot-Logik von Stage 581 wird unverändert beibehalten.

## 2. Pascal-PE32-Stack-Cookie (Stage 583)

Der bisher pro COFF-Modul erzeugte Inline-Code rief direkt Windows-APIs `BCryptGenRandom`, `InterlockedCompareExchange`, `RaiseFailFastException` und `ExitProcess` auf. Dies wird für **PE32** durch zwei Imports aus `libd64_runtime.dll` ersetzt:

```
import __d64_pas_cookie_initialize32, "libd64_runtime.dll", "jit_pas_cookie_initialize32"
import __d64_pas_cookie_failure32, "libd64_runtime.dll", "jit_pas_cookie_failure32"
```

Übrig bleiben modulinterne, kleine Trampoline:

```asm
__pas_cookie_initialize:
    push __pas_cookie_secret
    call __d64_pas_cookie_initialize32
    add esp, 4
    ret
__pas_cookie_failure:
    jmp __d64_pas_cookie_failure32
```

Die mit dem Frame (`EBP`) verknüpfte Guard-Berechnung und die Kontrolle **vor jedem normalen `ret` und expliziten `Exit`** bleiben im jeweils generierten Pascal-Funktionskörper. Das `__pas_cookie_secret: resd 1` bleibt pro COFF-Modul erhalten, damit unterschiedliche Module unabhängige Geheimnisse besitzen und parallele Erstaufrufe atomar denselben Wert erhalten. Das Initialisierungsverhalten bei `ProtectorCookie=false` bleibt unverändert: keine Guard-Routinen oder neuen DLL-Imports.

Die zentralen Funktionen sind in `runtime/pascal/cookie32.asm` als x86-cdecl-Routinen mit 32-Bit-Stackargumenten implementiert. Die CSPRNG-Rückgabe wird als NTSTATUS geprüft, das Geheimnis wird per `InterlockedCompareExchange` nur einmal gesetzt, und ein Scheitern endet weiterhin über `RaiseFailFastException`/`ExitProcess(STATUS_STACK_BUFFER_OVERRUN)`.

**PE64 bleibt vorerst unverändert.** Das bisherige `runtime/compiler/build.win64.sh` baut keine gleichnamige, passende PE64-Variante von `libd64_runtime.dll`. Eine stille Umstellung des 64-Bit-Compilers auf einen nicht existierenden Export würde bestehende Projekte brechen.

## 3. Dateien

- `c64pascal/compiler.py` – PE32-Cookie-Runtime und -Imports umgestellt.
- `runtime/pascal/cookie32.asm` – neue native PE32-Funktionen.
- `runtime/build.win32.sh` und `runtime/compiler/build.win32.sh` – NASM-Einbindung und Windows-Importbibliotheken `-lbcrypt -lkernel32`.
- `runtime/win32/libd64_runtime.def`, `runtime/compiler/win32/libd64_runtime.def` – neue Exporte.
- `runtime/exports/strings.def`, `runtime/compiler/exports/strings.def` – Exportquellen synchronisiert.
- `runtime/pascal/verify_cookie_runtime.py` – Prüft Maschinenarchitektur und die beiden DLL-Exporte.
- `test_stage583.py` – kompakte Regressionstests einschließlich CES OFF.

## 4. Kritisch: vorhandene DLL ist ALT

Die in Stage 582 mitgelieferte vorkompilierte `runtime/win32/libd64_runtime.dll` ist zwar PE32, **besitzt aber weder** `jit_pas_cookie_initialize32` noch `jit_pas_cookie_failure32`. Sie besitzt bereits die Stage-578-Exports nicht. Diese Datei darf nicht als neu gebaute DLL behandelt werden.

**Vor dem Test eines geschützten Pascal-PE32-Programms müssen die Runtime-DLL und alle betroffenen EXE/Unit-Objekte neu gebaut werden:**

```bash
# In einer MSYS2 MINGW32-Shell mit GCC und NASM:
cd runtime
bash build.win32.sh
```

Alternativ gibt es den zweiten Runtime-Buildbaum:

```bash
cd runtime/compiler
bash build.win32.sh
```

Danach, ausgehend vom Projektstamm, die tatsächlichen neuen Exporte prüfen:

```bash
python runtime/pascal/verify_cookie_runtime.py runtime/win32/libd64_runtime.dll
```

Oder für den anderen Buildbaum `runtime/compiler/win32/libd64_runtime.dll` prüfen. Die **neu erzeugte** DLL muss ins tatsächliche EXE-Ausgabeverzeichnis (neben die EXE) und ältere Kopien müssen dort ersetzt werden. Die `libd64_console.dll` ist eine andere DLL; sie wird durch diese Änderung nicht ersetzt.

## 5. Tests, Einschränkungen

- `python test_stage583.py`: 4 von 4 gezielten Tests erfolgreich.
- `python test_stage532.py`: 4 von 4 geprüften Generator-Regressionstests erfolgreich.
- Gezielt ausgewählte ältere Generator-/Importtests: PE32 und PE64, einschließlich Funktionsrückkehr und Import-Pruning, erfolgreich.
- Shell-/Python-Syntaxprüfung erfolgreich.
- **Nicht bestätigt:** ein nativer NASM-/MinGW32-DLL-Build oder Windows-Laufzeittest; die nötigen Werkzeuge fehlen in dieser Umgebung. Es wurde keine aktualisierte Binär-DLL vorgetäuscht.

Die DLL-Änderung ist eine neue ABI-Anforderung, falls die PE32-Stack-Protector-Option aktiv ist. Bei deaktivierter Stack-Protector-Option wird sie nicht benötigt; bestehende Pascal-Imports können unabhängig davon die Runtime-DLL benötigen.
