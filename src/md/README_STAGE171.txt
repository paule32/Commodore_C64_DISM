Stage 171 – Pascal UNIT -> COFF32 / COFF64 + EXE-Link
=========================================================

Basis / Erhaltung
-----------------
Stage 170 d64_dism.py:
  2392516 Bytes (2336.44 KiB)
  54115 Zeilen
  SHA-256 669ace99813b07c35300e508b1bc05517deb5cfa0b16755ff251ab3add974d18

Stage 171 d64_dism.py:
  2402830 Bytes (2346.51 KiB)
  54388 Zeilen
  SHA-256 162c17eb046b0d289c652d20e88c61d81d229e5aa276afa08706f2ea7b51c770

Alle Stage-170-Zeilen bleiben unverändert/in derselben Reihenfolge erhalten.
Unified Diff: +273 / -0 Quellzeilen.

Was bereits vorhanden war
--------------------------
Stage 170 konnte intern bereits:
  * Pascal source_kind == "unit" erkennen,
  * PE32-Assembly als Microsoft i386-COFF schreiben,
  * PE64-Assembly als Microsoft AMD64-COFF schreiben,
  * mehrere .o/.obj/.a/.lib-Dateien zu PE32 bzw. PE32+ linken,
  * F2 bei Pascal-Units auf Objekt- statt EXE-Erzeugung umschalten,
  * CLI --write-coff32 / --write-coff64 und --object verwenden.

Die zwei verbleibenden Lücken waren:
  1. PE32 und PE64 verwendeten standardmäßig beide denselben Namen Unit.o.
     Dadurch konnte ein Build der anderen Architektur das Objekt überschreiben.
  2. Der Projekt-/Abhängigkeitslink bevorzugte dieses neutrale Unit.o und
     verwendete ein bereits architekturgetrennt erzeugtes Unit-Objekt nicht.

Stage 171
---------
Pascal-UNITs bekommen zusätzlich architekturklare Objekte:

  MyUnit.pas -> MyUnit.coff32.o   für Windows PE32 / i386
  MyUnit.pas -> MyUnit.coff64.o   für Windows PE32+ / AMD64

Das bisherige .o-Verhalten bleibt aus Kompatibilitätsgründen erhalten.
Dadurch funktionieren ältere Projektdateien weiterhin.

GUI Compile
-----------
Beim normalen Kompilieren eines Pascal-UNITs wird unter Windows-Zielen nun
sofort das passende relocierbare Objekt erzeugt:

  Ziel PE32: MyUnit.coff32.o
  Ziel PE64: MyUnit.coff64.o

Es wird keine EXE für das Unit erzeugt und kein _start vorausgesetzt.
Das vorhandene .pui bleibt unverändert der Interface-/Compiler-Metadatenpfad.

F2 / Projektlink
----------------
Das bestehende F2-Verhalten bleibt bestehen. Ein Pascal-UNIT wird als Objekt
gebaut. Beim späteren F2 auf dem Pascal-Hauptprogramm wird für Projekt-Units
jetzt zielabhängig bevorzugt:

  PE32 -> MyUnit.coff32.o
  PE64 -> MyUnit.coff64.o

wenn das Objekt vorhanden und tatsächlich als passendes COFF parsebar ist.
Existiert kein architekturspezifisches Objekt, fällt der bisherige Unit.o-Pfad
weiterhin zurück.

Prebuilt Unit Reuse
-------------------
Wenn der Pascal-Compiler ein Unit-Modul über linked_assembly_files bzw. ein
separates Modul meldet, prüft der Objektwriter nun zuerst auf ein vorhandenes
passendes .coff32.o/.coff64.o. Ist es gültig, wird es direkt zum Linkerinput
hinzugefügt und das Unit-ASM nicht noch einmal assembliert.

Damit ist der gewünschte Ablauf möglich:

  Unit.pas
    -> Pascal Compiler
    -> Unit.generated.pe32.asm / Unit.generated.pe64.asm
    -> Unit.coff32.o / Unit.coff64.o

  Main.pas
    -> Main COFF
    + passendes Unit COFF
    -> interner COFF-Linker
    -> PE32 EXE / PE32+ EXE

CLI
---
PE32 Unit:
  py d64_dism.py --write-coff32 MyUnit.pas

PE64 Unit:
  py d64_dism.py --write-coff64 MyUnit.pas

Ohne -o bleibt aus Kompatibilitätsgründen Unit.o erhalten und Stage 171 legt
zusätzlich Unit.coff32.o bzw. Unit.coff64.o an.

Mit explizitem -o wird exakt die gewünschte Ausgabedatei respektiert:
  py d64_dism.py --write-coff32 MyUnit.pas -o build/MyUnit32.obj
  py d64_dism.py --write-coff64 MyUnit.pas -o build/MyUnit64.obj

Manuell linken:
  py d64_dism.py --link-pe32 App.exe --object Main.o --object MyUnit.coff32.o
  py d64_dism.py --link-pe64 App64.exe --object Main.o --object MyUnit.coff64.o

Archive bleiben ebenfalls möglich:
  --archive-coff32 ... --object MyUnit.coff32.o
  --archive-coff64 ... --object MyUnit.coff64.o

Technik
-------
COFF32:
  IMAGE_FILE_MACHINE_I386 = 0x014C
  Relocations bleiben im Unit-Objekt erhalten.

COFF64:
  IMAGE_FILE_MACHINE_AMD64 = 0x8664
  .text/.data/.bss und AMD64-Relocations bleiben im Objekt erhalten.

Der EXE-Linker löst Unit-Symbole genauso wie Symbole anderer COFF-Objekte auf.
Ein Unit-Objekt benötigt keinen Programmeinstieg; nur das Hauptprogramm stellt
_start bereit.

Tests
-----
Siehe STAGE171_TEST_RESULTS.txt.
