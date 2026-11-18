# Stage 594: dBASE-Präprozessorfarben und externe DLL-Prozeduren

Basis: hochgeladene `d64_dism_stage593.zip`.

## Syntax-Highlighter

In `d64_dism.py` / `AssemblerSyntaxHighlighter` färbt der dBASE-Modus
`#ifndef`, `#ifdef`, `#if`, `#elif`, `#else`, `#endif`, `#define`,
`#undef`, `#include`, `#pragma`, `#warning`, `#warn`, `#error` und `#info`
**orange** (nur das Schlüsselwort inklusive `#`). Die Bezeichner und
Stringliterale dahinter behalten ihre bisherigen Farben.

Alle im dBASE-FFI-Typregister `d64dbase/ffi_types.py` enthaltenen Typen,
u. a. `PVOID`, `CINT`, `LPCSTR`, `LPCWSTR`, `DWORD`, `CVOID`, sind orange.
Die dBASE-Kommentar- und String-Lexik übersteuert den Typ-Highlighter:
Typnamen innerhalb von `/* ... */`, `//`, `**`, `&&` oder Stringliteralen
bleiben Kommentare bzw. Strings. Orange im Dunkelmodus: `#FFA630`,
im hellen Modus für ausreichenden Kontrast: `#B65A00`.

## Externe Prozeduren

`extern` verwendete bisher obligatorisch einen Rückgabetyp. Der Typ
`CVOID` war bereits für Funktionen ohne Rückgabe möglich. Ab Stage 594
werden zusätzlich `PROCEDURE`, `PROC`, `VOID` und das Weglassen des
Rückgabetyps als **`CVOID`** interpretiert:

```dbase
extern CVOID OutputDebugStringA(LPCSTR) stdcall "kernel32.dll" from "OutputDebugStringA"
extern PROCEDURE OutputDebugStringA(LPCSTR) stdcall "kernel32.dll" from "OutputDebugStringA"
extern PROC OutputDebugStringA(LPCSTR) stdcall "kernel32.dll" from "OutputDebugStringA"
extern OutputDebugStringA(LPCSTR) stdcall "kernel32.dll" from "OutputDebugStringA"
```

Dies sind vier Alternativen für **dieselbe** Deklaration, nicht vier
Deklarationen, die nebeneinander stehen sollen! Der Name links neben der
Klammer ist der in dBASE sichtbare Name. Hinter `from` steht der echte
DLL-Exportname. Die DLL wird als PE-Import eingebunden (kein dynamisches
`LoadLibrary` zur Laufzeit).

Aufruf ohne Verwendung eines Rückgabewerts:

```dbase
OutputDebugStringA("Hallo aus dBASE")
```

`x = OutputDebugStringA("Hallo")` ist absichtlich unzulässig, weil die
externe Prozedur keinen Rückgabewert liefert. Der Compiler verwendet die
bereits in Stage 592 implementierte Stackbehandlung: bei PE32 `cdecl`
bereinigt der Aufrufer ESP, bei `stdcall` die aufgerufene DLL-Funktion.
Bei PE64 gelten die Microsoft-x64-Aufrufregeln.

## Präprozessormakros

```dbase
#ifndef RUNTIME_DLL
#define RUNTIME_DLL "libd64_runtime.dll"
#else
#undef RUNTiME_DLL
#define RUNTIME_DLL "libd64_runtime.dll"
#endif
extern PVOID jit_object_instance_new(PVOID); cdecl; RUNTIME_DLL; from "jit_object_instance_new"
```

Diese Sequenz wurde gegen den Compiler-Präprozessor getestet. dBASE-Makros
sind in diesem Projekt **ohne Beachtung der Groß-/Kleinschreibung**
implementiert, deshalb verweist `RUNTiME_DLL` auf dasselbe Makro wie
`RUNTIME_DLL`. Der Typ `PVOID` bleibt korrekt, denn `jit_object_instance_new`
**liefert einen Pointer**; ein `PROCEDURE`-Alias wäre hier falsch.

## Technische Änderungen

- `d64dbase/ffi.py`: drei zusätzliche Deklarationsformen für void-Prozeduren.
- `d64_dism.py`: neue orange Syntaxformate und FFI-Typregeln in beiden Themes.
- `test_stage594.py`: 10 gezielte Tests für Syntax, Makros, PE32/PE64-Aufrufe
  und editorseitige Tokenformate ohne PyQt-Runtime.
- `examples/dbase/ffi_external_procedures.prg`: ausführbares Beispiel für
  `OutputDebugStringA` aus `kernel32.dll`.

Teststatus: unit tests auf Linux, keine native Windows-GUI-/DLL-Ausführung.
Für `d64_dism.py` erfolgt der Syntaxcheck unter Python 3.13 mit einer rein
temporären Ersetzung des in Python 3.15 vorhandenen `lazy from`-Präfixes.
