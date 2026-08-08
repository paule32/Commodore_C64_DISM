# Windows PE64 / AMD64

`d64_dism.py` besitzt neben C-64, Amiga und Windows PE32 nun das Ziel
`Windows PE64`.

## Build-Pipeline

Für Pascal und C ist der vorgesehene interne Weg:

```text
Pascal / C
  -> AMD64-Assemblertext (`bits 64`)
  -> interner AMD64-Assembler
  -> Microsoft AMD64 COFF64 `.o` (`Machine = 0x8664`)
  -> optional internes `.a`-Archiv
  -> interner PE64-Linker
  -> Windows PE32+ EXE oder DLL (`Magic = 0x20B`)
```

Es wird dafür kein externer C/C++-Compiler, Assembler oder Linker benötigt.

## GUI

Die Target-ComboBox enthält:

- `C= 64`
- `Amiga`
- `Windows PE32`
- `Windows PE64`

Bei `Windows PE64` wird wie bei PE32 die Windows-Modus-ComboBox angezeigt:

- `Console`
- `GUI`
- `Direct2D`
- `Direct3D`

Für PE64 heißt der Objekt-Button `COFF64 .o`.

## AMD64 / PE32+

Der interne Writer verwendet:

- `IMAGE_FILE_MACHINE_AMD64 = 0x8664`
- PE Optional Header `PE32+`, Magic `0x20B`
- 64-Bit ImageBase
- 64-Bit ILT/IAT-Einträge
- `IMAGE_REL_AMD64_REL32` für relative Calls/Jumps
- `IMAGE_REL_AMD64_ADDR64` für absolute 64-Bit-Adressen
- `IMAGE_REL_BASED_DIR64` in der PE-Basisrelokationstabelle

DLLs können wie bei PE32 eine Export Directory und Import Directory besitzen.

## Calling Convention

Compilerintern wird weiterhin ein einfaches Stack-ABI mit einem 8-Byte-Slot
pro Argument verwendet. Für Windows-DLL-Imports erzeugt der interne Linker
Adapter-Thunks auf die Microsoft-x64-Calling-Convention:

- RCX: Argument 1
- RDX: Argument 2
- R8: Argument 3
- R9: Argument 4
- mindestens 32 Byte Shadow Space
- weitere Argumente auf dem Stack

Damit muss die Sprach-Frontend-Semantik nicht dupliziert werden, während der
Aufruf in die Windows-API dem Win64-ABI entspricht.

## OOP und Exceptions

Für PE64 sind Zeiger-/Referenzwerte 8 Byte breit. Das betrifft insbesondere:

- Klassenreferenzen
- VMT-Zeiger und VMT-Slots
- Exception-Objekte und Exception-Frames
- String-Referenzen
- Windows-Handles

Pascal-Skalartypen wie Integer/Boolean/Char behalten ihre bisherigen
Sprachgrößen; nur Referenz-/Pointerwerte werden auf 64 Bit verbreitert.

## CLI

Zusätzlich stehen bereit:

```text
--write-pe64 QUELLE
--write-coff64 QUELLE
--archive-coff64 ARCHIV --object MODUL.o [...]
--link-pe64 PROGRAMM.exe --object MODUL.o [--object LIB.a ...]
```

Bei einem `.dll`-Ziel von `--link-pe64` wird eine PE64-DLL geschrieben.

## Beispiele

- `examples/pe64/hello64.asm`
- `examples/pe64/library64.asm`
