# Stage 478 – Win32-API-Basistypen für dBASE-DLL-Aufrufe

**Verbindliche Basis:** `d64_dism_asm_477.zip` (Stage 477). Die Stage erweitert
`extern`-Prototypen in `.prg`/`.wfm` und den bestehenden FFI-Aufrufgenerator.

## Eingebaute Typgruppen

| Gruppe | Eingebaute Typen / Beispiele | Größe / Bedeutung |
| --- | --- | --- |
| Keine Rückgabe | `CVOID`, `VOID` | nur Rückgabe oder alleiniger Parameter (`f(VOID)`) |
| Logisch | `BOOL`, `BOOLEAN`, `CBOOL` | 32 Bit, **nicht** 1 Byte |
| 8-/16-Bit | `BYTE`, `UCHAR`, `CHAR`, `CCHAR`, `WORD`, `WCHAR`, `SHORT`, `USHORT`, `ATOM`, `LANGID` | Vorzeichen passend zum Typ |
| 32-Bit | `DWORD`, `DWORD32`, `UINT`, `UINT32`, `ULONG`, `ULONG32`, `COLORREF`, `LCID`, `LCTYPE`, `ACCESS_MASK`, `REGSAM` | vorzeichenlos |
| 32-Bit signed | `CINT`, `INT`, `INT32`, `LONG`, `LONG32`, `CLONG`, `HRESULT`, `NTSTATUS`, `LSTATUS` | vorzeichenbehaftet |
| 64-Bit | `LONGLONG`, `LONG64`, `INT64`, `ULONGLONG`, `UINT64`, `DWORD64`, `DWORDLONG`, `QWORD` | 64 Bit (mit dBASE-Zahlenpräzisionsgrenzen) |
| Pointergroße Ganzzahlen | `SIZE_T`, `SSIZE_T`, `WPARAM`, `LPARAM`, `LRESULT`, `INT_PTR`, `UINT_PTR`, `LONG_PTR`, `ULONG_PTR`, `DWORD_PTR` | 32 Bit in PE32, 64 Bit in PE32+ |
| Handles | `HANDLE`, `HWND`, `HINSTANCE`, `HMODULE`, `HDC`, `HICON`, `HMENU`, `HKEY`, `HBRUSH`, `HBITMAP`, `HFONT`, `HCURSOR`, `HMONITOR`, `SOCKET`, u. a. | pointergroß |
| Zeiger / native Puffer | `LPVOID`, `LPCVOID`, `PVOID`, `LPDWORD`, `LPWORD`, `LPBOOL`, `LPINT`, `LPBYTE`, `LPSTR`, `LPWSTR`, `PHANDLE`, u. a. | pointergroße Adresse (kein automatisch angelegter Ausgabepuffer) |
| C-Text als Eingabe | `LPCSTR`, `PCSTR`, `LPCWSTR`, `PCWSTR` | ANSI/CP1252 bzw. UTF-16LE, nullterminiert |

Vollständige Tabelle: `d64dbase/ffi_types.py`. `FFI_TYPES`, `ffi_type_info()` und
`WinAPIType` sind via `d64dbase` importierbar. Die Datentypen sind *in den
Compiler eingebaut*; separate `.h`-Dateien enthalten nur Prototypen.

## Beispiele

```dbase
#define kernel32 "kernel32.dll"
#define user32 "user32.dll"
extern DWORD GetLastError() kernel32 from "GetLastError"
extern HANDLE GetCurrentProcess() kernel32 from "GetCurrentProcess"
extern BOOL IsWindow(HWND) user32 from "IsWindow"
extern CINT MessageBoxW(HWND,LPCWSTR,LPCWSTR,UINT) user32 from "MessageBoxW"

handle = GetCurrentProcess()
valid = IsWindow(0)
result = MessageBoxW(0, "Grüße", "Unicode", 0)
```

Beispieldateien in `examples/winapi_stage478/` einschließlich eines über
`#include` einbindbaren Headers und einer `.wfm`-Quelle.

## ABI / Typprüfung

- Win32 `WINAPI` / `stdcall` und Microsoft Win64-ABI wie in Stage 477.
- Windows verwendet LLP64: `LONG` und `DWORD` bleiben **32 Bit** in PE64.
  `HANDLE`, `WPARAM`, `LPARAM`, `SIZE_T` und andere pointergroße Typen wachsen.
- 8-/16-Bit-Rückgaben werden passend maskiert bzw. sign-erweitert; 32-Bit-
  DWORD/UINT und 32-Bit-Handles werden vorzeichenlos erweitert.
- Auf PE64 übergibt der Codegenerator vorzeichenlose 32-Bit-Argumente über
  32-Bit-Register (Nullerweiterung).
- `LPCWSTR`-Konstanten werden als nullterminiertes UTF-16LE kodiert.
  Dynamische dBASE-Zeichenketten werden hierfür **noch nicht** automatisch
  konvertiert und verursachen eine Fehlermeldung.
- `LPSTR`, `LPWSTR`, `LPDWORD` usw. sind **schreibbare/native Zeiger**.
  Es wird ausdrücklich kein dBASE-String stillschweigend als beschreibbarer
  WinAPI-Puffer übergeben. Für Ausgabepuffer und `struct`-Argumente fehlen
  derzeit allgemeine Speicher-/Struktur-APIs.
- Die alte dBASE-Zahlrepräsentation (`double`) kann Integer nicht über den
  vollständigen 64-Bit-Bereich exakt halten (insbesondere jenseits 2^53).
  Die Stage führt noch keinen vollwertigen 64-Bit-Integer-/Pointer-Werttyp ein.
- Keine `FLOAT`-/`DOUBLE`-FFI-Signaturen: deren Gleitkomma-ABI benötigt
  XMM-Argumente. Keine Struktur-Übergabe per Wert (`RECT`, `POINT`, etc.).
- Keine unbestimmte `TCHAR`/`LPCTSTR`-Kodierung: für reproduzierbare Windows-
  Imports ausdrücklich `*A` mit `LPCSTR` oder `*W` mit `LPCWSTR` verwenden.
- Ein Qt-Widget-Zeiger ist weiterhin **kein** echtes HWND.
- DLL-Funktionen werden weiterhin durch die Import-Tabelle geladen, nicht
  dynamisch mit `LoadLibrary` / `GetProcAddress`.

## Tests

`test_stage478_winapi_base_types.py` prüft die Typ- und Größen-Metadaten,
argument- und rückgabeseitige Codeerzeugung sowie echte PE32-/PE64-COFF-
Assemblierung und Linking mit `.prg` und `.wfm` inklusive Unicode-String.
`test_stage477_dbase_winapi_ffi.py` und angrenzende dBASE-/WFM-Regressionen
sind in der Testsuite enthalten. Windows-Laufzeitausführung ist weiterhin
nicht in dieser Linux-Testumgebung verifiziert.
