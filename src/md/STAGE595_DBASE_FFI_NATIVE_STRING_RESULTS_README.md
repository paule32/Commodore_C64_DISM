# Stage 595 – Automatische dBASE-String-Rückgabe von C-DLLs

**Verbindliche Basis:** die hochgeladene `d64_dism_stage594.zip`.

## Deklarationen

Eine DLL-Funktion, die einen nullterminierten ANSI-`char *` zurückgibt, wird
mit `LPSTR` oder `LPCSTR` als **Rückgabetyp** deklariert:

```dbase
extern LPSTR GetCommandLineA() stdcall "kernel32.dll" from "GetCommandLineA"
? GetCommandLineA()

extern LPCSTR get_greeting() cdecl "example.dll" from "get_greeting"
STORE get_greeting() TO greeting
? greeting + "!"
```

Beide Typen erzeugen einen **richtigen dBASE-String** mit Zeiger, Länge und
Laufzeit-Typ. `PVOID` bleibt ausdrücklich ein **roher numerischer Zeiger**;
niemals blind alle `PVOID`-Rückgaben als Text interpretieren. Ebenso bleiben
`CINT`, `CBOOL`, Handles und breite `LPCWSTR`-Zeiger numerisch; die automatische
UTF-16-Stringrückgabe ist nicht Teil dieser Stage.

`LPSTR` als **Funktionsparameter** wird weiterhin als beschreibbarer nativer
Pointer behandelt, nicht als automatischer dBASE-Ausgabepuffer. Für ein
`LPSTR`-Ausgabeargument ist weiterhin ein gültiger, beschreibbarer Puffer
notwendig. `LPCSTR` als Eingabeparameter bleibt eine Text-Pointer-Eingabe.

## Verhalten

- PE32: `cdecl` bereinigt nach dem DLL-Aufruf den Argumentstack; `stdcall`
  überlässt die Bereinigung der DLL. Die nachfolgende String-Kopie verändert
  die Aufrufkonvention nicht.
- PE64: einheitliche Microsoft-x64-ABI. Die String-Kopie beachtet Shadow Space
  und die 16-Byte-Stackausrichtung.
- Bei `NULL` wird der leere dBASE-String erzeugt (`ptr=0`, `len=0`).
- PRG/dBASE: Ausgabe im bestehenden **CP1252-Byteformat**. `lstrlenA` bestimmt
  die Länge; `malloc` stellt neuen Speicher bereit und `memcpy` kopiert auch
  das abschließende Nullbyte. Der ursprüngliche DLL-Pointer wird nicht freigegeben.
- WFM/Qt5-Formulare: derselbe ANSI-Pointer wird über
  `MultiByteToWideChar(CP1252)` und `WideCharToMultiByte(CP_UTF8)` in eine
  **separate UTF-8-Kopie** umgewandelt. Der temporäre UTF-16-Puffer wird mit
  `free` freigegeben. Der WFM-Stringtyp bleibt `3` (STRING).
- Maximale Eingabelänge: **16 MiB** (Schutz vor übergroßen Allokationen).
  PRG beendet sich bei Überschreitung oder fehlgeschlagener Allokation mit
  Exitcode 13; WFM liefert bei Konvertierungs-/Allokationsfehler einen leeren
  String. Ein ungültiger, nicht lesbarer C-Pointer kann dennoch einen Fehler
  auslösen; die DLL muss einen gültigen, nullterminierten Pointer liefern.

## Speicherverwaltung

Der Rückgabepointer der C-DLL wird **nie** mit `free` oder `LocalFree`
freigegeben, da der Speicher der DLL gehören kann. Die Kopie verwendet die
bestehende dBASE-Speicherverwaltung (`msvcrt.dll`), in WFM ebenso.

**Achtung:** Wenn die C-DLL einen vom *Aufrufer freizugebenden* Buffer
zurückliefert, benötigt sie zusätzlich ihre passende eigene `free`-Funktion.
Diese Stage ruft eine solche Funktion **nicht** automatisch auf, weil
unterschiedliche DLLs unterschiedliche Allocatoren nutzen. Der bestehende
dBASE-Compiler benutzt nicht für jede Zwischenzeichenkette ein Refcounting
oder sofortiges `free`; langfristige Memory-Lifetime bleibt von der
bisherigen Stringverwaltung abhängig.

## Geänderte Dateien

- `d64dbase/ffi_types.py`: Unterscheidung der ANSI-String-Rückgaben von allgemeinen
  nativen Zeigern ohne Änderung der Parameterklassifikation.
- `d64dbase/ffi_string_result.py`: neuer gemeinsamer PE32-/PE64-Codegenerator
  für C-ANSI-Rückgaben in PRG- und WFM-Stringslots.
- `d64dbase/compiler.py`: Analyse (`kind=string`), Ergebnis-Slot und
  ANSI-Kopie in normalen PRG-Programmen, bei Verwendung des Typs zusätzlicher
  Kernel32-Import `lstrlenA`.
- `d64_dism.py`: WFM-FFI-Rückgabe einschließlich ANSI→UTF-8, Imports und
  `.bss`-Konvertierungspuffer; String-Variablen werden als Text klassifiziert.
- `test_stage595.py`: Codegenerierungs-/Regressionstests.
- `examples/dbase/ffi_native_string_results.prg`: verwendbares Windows-Beispiel.

## Prüfstand

Geprüft wurden PE32/PE64 generierter ASM-Code, Rückgabetypen,
String-Zuweisungen/-Ausgaben/-Verkettungen, Nullpointer, Größenbegrenzung,
WFM-UTF-8-Codegenerierung und unveränderte `PVOID`-Rückgaben. Eine native
Windows-Ausführung über `LoadLibrary`/`GetProcAddress` oder reale Exporte
ist in der Linux-Umgebung noch **nicht** bestätigt.
