# d64_dism – Amiga CPU/FPU, Windows PE32, COFF32 und Grafikziel

## Basis

Die Erweiterungen basieren auf dem vom Benutzer hochgeladenen Archiv
`d64_dism(2).zip`. Die vorhandene monolithische Grundstruktur, das Startskript
`d64_dism.py` sowie die C64-/Amiga-/Editor-/Projektfunktionen bleiben erhalten.
Die neuen Funktionen wurden additiv in diese Struktur integriert.

## 1. Plattformwahl im Editor

Die bisherige Zielwahl wurde auf drei Ziele erweitert:

- C-64
- Amiga
- Windows PE32

Bei `Amiga` werden zusätzlich zwei ComboBoxen sichtbar:

### CPU

- mk68000
- mk68010
- mk68020
- mk68030
- mk68040
- mk68060

### FPU

- FPU: None
- FPU: 68881
- FPU: 68882

Bei `Windows PE32` wird stattdessen die Grafik-ComboBox eingeblendet:

- Direct2D
- Direct3D

Die Auswahl ist sowohl über dem Quelltext als auch über dem erzeugten ASM-Tab
vorhanden. Eine Änderung invalidiert ein bereits assemblierter Ergebnis.

## 2. CPU-abhängiger Amiga-Assembler

Alle bereits vorhandenen 68000-Befehle bleiben verfügbar. Zusätzlich wird die
CPU-Stufe an den Encoder weitergegeben und bei CPU-spezifischen Instruktionen
geprüft.

Aktuell direkt implementierte Erweiterungen:

### mk68010+

- RTD
- BKPT
- MOVEC
  - SFC
  - DFC
  - USP
  - VBR

### mk68020+

- lange Bcc/BRA/BSR-Displacements (`.L`)
- `LINK.L`
- `EXTB.L`
- zusätzliche MOVEC-Register
  - CACR
  - CAAR (bis mk68030)
  - MSP
  - ISP

### mk68040+

MOVEC unterstützt zusätzlich:

- TC
- ITT0 / ITT1
- DTT0 / DTT1
- MMUSR
- URP
- SRP

### mk68060

MOVEC unterstützt zusätzlich:

- PCR

Zusätzlich wurden die allgemeinen Systeminstruktionen RESET, RTE, RTR, TRAP,
TRAPV, STOP, LINK.W und UNLK ergänzt.

Die CPU-Profile mk68030/mk68040/mk68060 erben alle kompatiblen Instruktionen
der niedrigeren Profile. Die vollständigen PMMU-/Cache-/Bitfield-Spezialgruppen
aller 68020/030/040/060-Varianten sind noch nicht vollständig abgebildet;
dafür ist das Profilmodell jetzt vorbereitet.

## 3. 68881/68882-FPU

`FPU: None` weist FPU-Instruktionen zurück. Mit 68881 oder 68882 stehen derzeit
folgende direkt codierten FP-Registeroperationen bereit:

- FNOP
- FMOVE
- FADD
- FSUB
- FMUL
- FDIV
- FCMP
- FTST
- FABS
- FNEG
- FSQRT
- FINT
- FINTRZ

Die arithmetischen Routinen akzeptieren in dieser Stufe FP0..FP7 als Quelle
und Ziel. Speicherformate, FMOVEM und alle transzendenten 68881-Kommandos sind
noch nicht vollständig implementiert.

## 4. Integrierter Windows-PE32-Assembler

Der neue IA-32-Assembler arbeitet mit Intel-Syntax. Er erzeugt entweder direkt
eine PE32-EXE oder ein relocierbares Microsoft-COFF32-Objekt.

Unter anderem implementiert:

- MOV, LEA
- PUSH, POP
- CALL, JMP
- JE/JNE/JZ/JNZ/JL/JLE/JG/JGE und weitere Jcc
- ADD, SUB, CMP
- XOR, AND, OR, TEST
- IMUL, DIV, IDIV
- SHL/SAL, SHR, SAR
- INC, DEC
- NEG, NOT
- MOVZX, MOVSX
- SETcc
- XCHG
- CDQ, LEAVE, RET
- INT, INT3
- PUSHAD, POPAD
- CLI/STI/CLD/STD

### Speicheradressierung

Compilerrelevante 32-Bit-Adressierungen sind enthalten:

- `[eax]`
- `[ebp-4]`
- `[esp+8]`
- `[eax+ecx*4]`
- `[eax+ecx*4+16]`
- `[global_symbol]`
- `byte ptr [...]`
- `word ptr [...]`
- `dword ptr [...]`

Dadurch lassen sich normale IA-32-Stackframes und lokale Variablen direkt
assemblieren.

## 5. PE32-Importtabelle

Nicht durch COFF-Objekte definierte bekannte Win32-Symbole werden vom Linker
automatisch in `.idata` eingetragen. Pro externem Symbol wird ein
`JMP DWORD PTR [IAT]`-Thunk in `.text` erzeugt.

Vorbereitet sind unter anderem Imports aus:

- kernel32.dll
- user32.dll
- msvcrt.dll
- d2d1.dll
- d3d9.dll

Auch führende Unterstriche und stdcall-Dekorationen wie `_ExitProcess@4`
werden auf den eigentlichen Importnamen zurückgeführt.

## 6. COFF32-Objekte, PUI und Archive

Pascal behält die bestehende PUI-Erzeugung. Beim Ziel Windows PE32 erscheint
im erzeugten ASM-Tab zusätzlich der Button:

`COFF32 .o`

Damit wird der sichtbare ASM-Stand als relocierbares i386-COFF-Objekt erzeugt.

Werkzeuge enthält zusätzlich:

- COFF32-Archiv (.a) erstellen …
- Windows PE32 Linker …

Der integrierte Archivierer erzeugt ein `ar`-kompatibles `.a`. Der Linker kann
eigene `.o`/`.obj` und `.a`-Archive zusammenführen, REL32/DIR32-Relocations
auflösen und eine PE32-EXE erzeugen.

CLI:

```text
--write-pe32 QUELLE
--write-coff32 PASCAL
--archive-coff32 ARCHIV --object a.o --object b.o
--link-pe32 PROGRAMM.EXE --object main.o --object lib.a
--amiga-cpu mk68020
--amiga-fpu "FPU: 68882"
--windows-graphics Direct2D|Direct3D
```

## 7. Windows-Grafikziel

Die öffentliche Grafik-API bleibt plattformunabhängig und arbeitet logisch mit
320x200 Pixeln. Für Windows werden folgende Präprozessor-Symbole gesetzt:

- `__D64_TARGET_PE32__`
- `__D64_GRAPHICS_WINDOWS__`
- `__D64_GRAPHICS_DIRECT2D__` oder `__D64_GRAPHICS_DIRECT3D__`

Die Windows-Runtime öffnet ein Win32-Fenster und skaliert 320x200 auf 640x400.
Je nach Auswahl wird Direct2D oder Direct3D9 verwendet. Implementiert sind:

- SetTextColor
- ClearScreen
- InitGraphics / DoneGraphics
- SetPixel / GetPixel
- DrawLine
- DrawRect / FillRect
- DrawCircle / FillCircle
- FloodFill
- DrawTriangle / FillTriangle
- DrawTriangleAngles

`System.Graphics.pui` besitzt nun ein PE32-Implementierungsmodul
`Graphics.pe32.asm`. Dieses stellt die Pascal-PUI-Symbole bereit und leitet sie
auf die C-Exports der Runtime `d64graphics.dll` weiter. Der interne PE32-Linker
erzeugt dafür automatisch die Importtabelle.

Unter **Werkzeuge** stehen zwei Funktionen bereit:

- Windows Direct2D/Direct3D Runtime schreiben …
- Windows Direct2D/Direct3D Runtime DLL bauen …

Der bereits vorhandene Grafik-Runtime-Quellcode ist von der eigentlichen
PE32-Toolchain getrennt. Pascal-/C-Kompilierung, IA-32-Assemblierung, COFF32,
Archive sowie EXE-/DLL-Linken rufen **keinen** MinGW-/GCC-/MSVC-/NASM-Linker
auf. `d64graphics.dll` bleibt eine eigenständige Runtime-Komponente und muss
neben einer Grafik-EXE liegen.

## 8. Pascal- und C-Compilerintegration

Die Frontends akzeptieren jetzt zusätzlich das Ziel `pe32` beziehungsweise die
Aliase `win32`, `windows` und `windows-pe32`. Damit ist der zuvor auftretende
Fehler `Unbekanntes Compilerziel: pe32` beseitigt.

### Pascal

Der Pascal-Generator erzeugt IA-32-Assembler mit 8-, 16- und 32-Bit-Zugriffen,
Kontrollfluss, arithmetischen Operationen, Vergleichen, externen cdecl-Aufrufen
und den bestehenden Unit-/PUI-Verknüpfungen. PE32-Units erhalten einen eigenen
Unit-Anker; PUI-C-Implementierungen werden als `.generated.pe32.asm` abgelegt.

### C

Das C-Frontend besitzt einen PE32-Codegenerator mit IA-32-Stackframes, lokalen
Variablen, Parametern ab `[ebp+8]`, cdecl-Aufrufen sowie dynamischen Shifts über
`CL`. Auch getrennte `#pragma link`-C-Module werden für PE32 erneut mit dem
PE32-Generator und nicht mehr mit dem Amiga-Fallback übersetzt.

## 9. Windows-Textprogramme

Wenn kein `InitGraphics(...)` im Quelltext benutzt wird, erzeugen Pascal und C
automatisch eine Konsoleninitialisierung:

1. `AllocConsole`
2. `GetStdHandle(STD_OUTPUT_HANDLE)`
3. sichtbares Fenster auf 80 Spalten × 25 Zeilen
4. Konsolenpuffer auf exakt 80 × 25
5. Virtual-Terminal-Ausgabe für `ClrScr` aktivieren

Die Textausgabe verwendet `WriteFile` auf den durch `GetStdHandle` erhaltenen
Handle. Sie hängt damit bei einer GUI-Subsystem-PE nicht von der initialen
`stdout`-Verdrahtung der C-Runtime ab. Ganzzahlen werden vor der Ausgabe mit
`wsprintfA` formatiert.

## 10. Validierung

Direkt geprüft wurden:

- Python-Syntax von `d64_dism.py`, `c64pascal/compiler.py`, `c64c/compiler.py`
- generierter Pascal-PE32-Assembler durch den internen IA-32-Assembler
- Erzeugung einer PE32-EXE mit `MZ`-/PE-Header
- Erzeugung eines relocierbaren i386-COFF32-Objekts
- Pascal-`System.Graphics`-Aliasmodul und automatische
  `d64graphics.dll`-Importtabelle
- neue IA-32-Encoderformen für Byte-/Word-Stores, `CL`-Shifts und bitweise
  Immediate-Operationen

Für einen vollständigen ANTLR-Frontendtest wird, wie im Projekt bereits
dokumentiert, `antlr4-python3-runtime==4.13.2` benötigt. Die Prüfungsumgebung
hier enthält 4.9.3; deshalb wurden die PE32-Codegeneratoren zusätzlich direkt
über ihre AST-Schicht validiert.

## 11. Vollstaendig interne PE32/COFF32 Build-Kette

Fuer Windows PE32 wird kein externer Assembler und kein externer Linker benoetigt.
Der Compilerpfad in `d64_dism.py` ist jetzt bewusst mehrstufig aufgebaut:

```text
Pascal/C
   -> PE32 IA-32 Assemblertext
   -> interner PE32 Assembler
   -> Microsoft COFF32 .o
   -> interner COFF32 Linker
   -> Windows PE32 EXE oder DLL
```

Auch das Hauptmodul wird vor dem Linken immer zuerst als COFF32-Objekt erzeugt.
PE32-Module aus Pascal-Units, C-`#pragma link`-Quellen und explizit gelinkte
Assemblerdateien werden getrennt assembliert und als einzelne `.o`-Dateien an
den Linker uebergeben. Archive `.a` koennen dieselben COFF32-Objekte enthalten.

### Link-Metadaten in COFF32

Damit eine `.o`-Datei auch spaeter ohne den urspruenglichen Quelltext gelinkt
werden kann, schreibt der interne COFF32-Writer eine `.drectve`-Sektion mit
d64-Link-Metadaten. Darin koennen gespeichert werden:

- DLL-Imports (lokales Symbol, DLL-Name, Member-Name)
- DLL-Exports (oeffentlicher Name, internes Symbol)
- DLL-Name
- Entry-Symbol

Der interne Assembler versteht dazu unter anderem:

```asm
import MessageBoxA, "user32.dll", "MessageBoxA"
extern MessageBoxA

export Add, add_impl
dllname "demo.dll"
```

Der Linker erzeugt daraus die echte PE32 Import Directory / IAT beziehungsweise
die echte PE32 Export Directory. Die Metadaten bleiben auch beim Verpacken der
Objekte in einem `.a`-Archiv erhalten.

### Hauptprogramme

Ein Pascal-`PROGRAM` oder ein C-Hauptprogramm wird zu einem Hauptobjekt
assembliert. Dieses Objekt wird zusammen mit allen zugehoerigen `.o`- und
`.a`-Eingaben intern zu einer EXE gelinkt. Nicht intern definierte und als
DLL-Import deklarierte Symbole erhalten einen IAT-basierten Import-Thunks.

### Pascal LIBRARY

Ein Pascal-Quelltext mit

```pascal
library Demo;
```

wird fuer das Ziel PE32 als DLL behandelt. Ein einfacher Exportabschnitt wird
unterstuetzt:

```pascal
exports
  Add,
  Subtract name 'Sub';
```

Fuer jeden Export erzeugt der PE32-Codegenerator einen cdecl-Exportwrapper.
Der COFF32-Writer speichert die Exportzuordnung und der interne PE32-Linker
schreibt daraus die `IMAGE_EXPORT_DIRECTORY`. Als DLL-Einstieg wird
`__d64_dll_entry` erzeugt; der Entry liefert fuer den Windows-DLL-Loader TRUE
zurueck und fuehrt die Pascal-Initialisierung beim Process-Attach aus.

Aktuell sind fuer diese automatisch erzeugten Exportwrapper skalare
32-Bit-kompatible Parameter vorgesehen. Komplexere ABI-Faelle wie Records by
value, 64-Bit-Werte und spezielle Calling-Conventions muessen separat erweitert
werden.

### Keine MinGW-Abhaengigkeit fuer Compiler/Assembler/Linker

Die komplette oben beschriebene Pascal-/C-/Assembler-/COFF32-/EXE-/DLL-Kette
wird durch Python-Code innerhalb von `d64_dism.py` und den vorhandenen
Frontends ausgefuehrt. Weder MinGW, GCC, MSVC, NASM noch ein externer PE-Linker
werden dafuer aufgerufen.

### DLL-ImageBase und Basisrelokationen

Interne DLLs erhalten standardmäßig die ImageBase `0x10000000` statt der
EXE-Basis `0x00400000`. Für absolute `IMAGE_REL_I386_DIR32`-Adressen sowie
absolute IAT-Thunks erzeugt der Linker eine echte `.reloc`-Sektion mit
`IMAGE_REL_BASED_HIGHLOW`-Einträgen. Bei vorhandenen Relokationen wird im
PE32-Optional-Header `DYNAMIC_BASE` gesetzt. Dadurch kann der Windows-Loader
die erzeugte DLL auf eine andere freie Basisadresse verschieben.
