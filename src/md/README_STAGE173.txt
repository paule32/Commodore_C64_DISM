Stage 173 – konservativer PE32 Compactor Fix
=============================================

Grund für Stage 173
-------------------
Die aggressive Stage-172-Variante entfernte den .ztext-Sectionheader vollständig.
Auf dem realen Windows-System wurde die resultierende Datei mit ERROR_BAD_EXE_FORMAT
("keine zulässige Windows Anwendung") abgewiesen.

Stage 173 behält deshalb die komplette virtuelle PE-Struktur bei.

Original test.exe:
  4 Sections: .text / .loader / .ztext / .idata
  Größe 2048 Byte

Stage 173:
  4 Sections: .text / .loader / .ztext / .idata
  Größe 1536 Byte

Nur physisch ändert sich:
  .loader RawSize = 0x200, enthält Loader + eingebettetes D64Z
  .ztext  RawSize = 0, RawPtr = 0, RVA/VirtualSize bleiben erhalten
  .idata  RawPtr  = 0x400 statt 0x600; RVA bleibt 0x5000

Explizit unverändert gegenüber dem Original:
  NumberOfSections = 4
  EntryPoint        = 0x2000
  BaseOfCode        = 0x1000
  BaseOfData        = 0x3000
  SizeOfCode        = 0x200
  SizeOfInitData    = 0x400
  SizeOfImage       = 0x6000
  SizeOfHeaders     = 0x200
  sämtliche DataDirectories inkl. Import/IAT
  sämtliche Section-RVAs

Geändert werden nur:
  .loader VirtualSize 0xB8 -> 0x1BC
  .ztext RawSize/RawPtr -> 0
  .idata RawPtr 0x600 -> 0x400
  x86 Loader PackedVA 0x00403020 -> 0x004020D8

D64Z liegt weiterhin byte-identisch vor, nur eingebettet in .loader bei Offset 0xB8.

CLI:
  py d64_dism.py --compact-pe32 test.exe

Wichtig:
Der echte Windows-Starttest konnte hier nicht durchgeführt werden, da weder Windows
noch Wine in der Testumgebung vorhanden sind. Die korrigierte EXE sollte deshalb
auf dem realen Windows-System erneut getestet werden.

Quellerhaltung:
  Stage172: 2426290 Bytes / 55033 Zeilen
  Stage173: 2441317 Bytes / 55449 Zeilen
  Diff: +416 / -0
