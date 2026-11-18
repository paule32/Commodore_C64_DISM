# Stage 592 – dBASE-FFI: cdecl und stdcall bei DLL-Imports

Verbindliche Ausgangsdatei: `d64_dism_stage591(1).zip`.

## Ausgangssituation

Seit Stage 477 kennt der dBASE-Compiler typisierte `extern`-DLL-Imports. PE32-Routinen wurden jedoch immer als `stdcall` behandelt. Für C-Exportfunktionen wie `jit_object_instance_new` führt dies zur falschen Stackbereinigung, falls Argumente übergeben werden.

## Neue Deklaration

```dbase
extern PVOID jit_object_instance_new(PVOID) ;
    cdecl ;
    "libd64_runtime.dll" ;
    from "jit_object_instance_new"
```

Alternativ ist eine einzeilige Deklaration möglich:

```dbase
extern CINT CAbs(CINT) cdecl "msvcrt.dll" from "abs"
extern DWORD CurrentProcessId() stdcall "kernel32.dll" from "GetCurrentProcessId"
```

Ohne Konventionsangabe bleibt der bisherige Standard `stdcall` erhalten. Die Namen sind unabhängig von Groß-/Kleinschreibung.

### PE32-Codegenerierung

- Die Argumente werden in umgekehrter Reihenfolge auf den Stack gelegt.
- Ein 32-Bit-Wert oder Zeiger belegt 4 Byte; ein `INT64`/`UINT64` belegt 8 Byte.
- Bei `cdecl` folgt nach `call` ein `add esp, N`, wobei N die Gesamtzahl der übergebenen Bytes ist. Bei `stdcall` entfällt dies, weil die DLL-Funktion mit `ret N` zurückkehrt.
- Nullparameter-Aufrufe erzeugen kein überflüssiges `add esp, 0`.
- Der Rückgabewert wird unverändert aus EAX bzw. EDX:EAX aufbereitet.

### PE64-Codegenerierung

Die Schlüsselwörter werden eingelesen, aber beide verwenden unter Windows PE64 die Microsoft-x64-Aufrufkonvention. Die Shadow-Space-Behandlung bleibt unverändert; es gibt **kein** zusätzliches `add esp, N`.

### Integration

- `d64dbase/ffi.py`: optionale Konventionsangabe am `extern`-Prototyp, Stack-Größenberechnung.
- `d64dbase/compiler.py`: PE32-`cdecl`-Stackbereinigung in PRG-Aufrufen.
- `d64_dism.py`: dieselbe PE32-`cdecl`-Behandlung für FFI-Aufrufe aus WFM-Methoden.
- `test_stage592.py`: Parser-, ABI-, Kompatibilitäts- und Codegenerierungsregressionen.
- `examples/dbase/ffi_calling_conventions.prg`: Anwendungsbeispiel.

### Grenzen

Es sind weiterhin **statische PE-Imports**. Dynamisches `LoadLibrary`/`GetProcAddress` mit Funktionszeiger-Aufrufen ist hier nicht implementiert.

`jit_object_instance_new` erwartet eine **gültige `JitVmt`-Adresse**: `0` oder ein zufälliger Zahlenwert ist kein verwendbarer VMT-Zeiger. Pointer werden über die bestehende numerische dBASE-ABI transportiert; unter PE64 ist die exakte Darstellung großer Pointer-Werte im Double-basierten Runtime-Modell nicht generell gewährleistet.

Die Exportnamen müssen exakt mit der DLL-Exporttabelle übereinstimmen. Diese Änderung baut oder kopiert keine Runtime-DLL neu.

## Prüfungen

Die Tests prüfen die Quelltextvorverarbeitung und konkret erzeugte PE32-/PE64-Assembly. Ein nativer Windows-Laufzeittest steht noch aus.
