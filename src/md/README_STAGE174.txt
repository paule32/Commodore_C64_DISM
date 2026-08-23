Stage 174 – Pascal-Projektziele PE32 / PE32+
=============================================

Projektbaum
-----------
Unter der bestehenden geschützten Kategorie `Pascal-Programme` werden jetzt
zusätzlich folgende geschützte Zielzweige erzeugt:

Pascal-Programme
├─ Windows PE32
│  ├─ Module
│  └─ Units
└─ Windows PE32+
   ├─ Module
   └─ Units

Die bisherige flache Pascal-Projektliste bleibt aus Kompatibilitätsgründen
unverändert bestehen.

Kontextmenü auf Windows PE32 / Windows PE32+
---------------------------------------------
Programm erstellen
DLL erstellen
----------------
Starten

`Programm erstellen`
--------------------
* sucht unter Module genau das Pascal-Hauptmodul mit `PROGRAM`
* baut alle Einträge unter Units zuerst
* Pascal-Units werden zielabhängig zu `.coff32.o` bzw. `.coff64.o` gebaut
* zusätzliche COFF/Archive unter Module/Units werden als interne Linkinputs
  übernommen
* das Hauptprogramm wird danach kompiliert, assembliert und mit genau diesen
  Inputs über den vorhandenen internen PE32/PE32+-Linker gelinkt
* es wird kein mingw32-make / externer GCC-Linker gestartet

`DLL erstellen`
---------------
* sucht unter Module das Pascal-Hauptmodul mit `LIBRARY`
* verwendet dieselben Units/COFF-Inputs
* linkt über den vorhandenen internen DLL-Pfad mit `__d64_dll_entry`
* Ausgabedatei ist `.dll`

Ein PROGRAM- und ein LIBRARY-Hauptmodul dürfen gleichzeitig unter Module
liegen. Beim EXE-Build wird das LIBRARY-Hauptmodul übersprungen, beim DLL-Build
das PROGRAM-Hauptmodul. Units werden in beiden Fällen gemeinsam benutzt.

`Starten`
---------
Startet ausschließlich die zuletzt erzeugte EXE des gewählten PE-Ziels.
Wenn noch kein Build in der aktuellen Sitzung gespeichert ist, wird zusätzlich
die erwartete `<Program>.exe` neben dem PROGRAM-Hauptmodul gesucht. Der Start
läuft über `_launch_assembled_document()` und damit über den bereits vorhandenen
Windows-PE-Startpfad; es wird kein Buildwerkzeug gestartet.

Module / Units verwalten
------------------------
Rechtsklick auf Module oder Units:

Hinzufügen …
Einträge löschen

Akzeptiert werden:
  *.pas *.pp *.o *.obj *.a *.lib

Rechtsklick auf einen eingefügten Eintrag:
  Öffnen
  --------
  Aus Knoten entfernen

Projektdatei (*.pro)
--------------------
Die vier neuen Listen werden in separaten, optionalen INI-Sections gespeichert:

Category.pascal.pe32.modules
Category.pascal.pe32.units
Category.pascal.pe64.modules
Category.pascal.pe64.units

Alte Projekte besitzen diese Abschnitte nicht und werden unverändert geladen.
Die alten Category.pascal-Einträge bleiben weiterhin erhalten.

Build-Reihenfolge
-----------------
Units -> PUI/ASM -> COFF32/COFF64
       ↓
weitere COFF/Archive
       ↓
PROGRAM oder LIBRARY Hauptmodul
       ↓
interner COFF-Linker
       ↓
PE32 EXE/DLL oder PE32+ EXE/DLL

Quellerhaltung
---------------
Stage 173:
  2441317 Bytes / 55449 Zeilen
  SHA-256 405434fc1926ccaed799b7d92761f6afeca2836aaf2c3e41f89558bb446efded

Stage 174:
  2472709 Bytes / 56169 Zeilen
  SHA-256 098d3ea4a1cdc72dfb7ce9c8fb9cb0de3a36bc5ae62fe07e12641f4710c2faf7

Unified Diff:
  +720
  -0

Alle Stage-173-Zeilen sind unverändert und in Originalreihenfolge erhalten.

Testhinweis
-----------
PyQt5 ist in der Linux-Testumgebung nicht installiert, deshalb konnte kein
echter visueller GUI-Klicktest durchgeführt werden. Syntax, Projekt-INI-
Roundtrip, Kontextmenü-Reihenfolge, PROGRAM/LIBRARY-Auswahl, Build-Orchestrierung
und Startpfad wurden statisch bzw. mit isolierten Mocktests geprüft.
