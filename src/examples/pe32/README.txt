PE32 intern in d64_dism.py
==========================

Build-Kette:
  Pascal/C -> IA-32-ASM -> COFF32 .o -> interner Linker -> EXE/DLL

library_demo.pas
  Demonstriert Pascal LIBRARY + EXPORTS. Das Ergebnis ist eine DLL mit echter
  IMAGE_EXPORT_DIRECTORY. Es wird kein externer Assembler oder Linker benutzt.

import_demo.asm
  Demonstriert die d64-Assemblerdirektive IMPORT. Sie wird beim Erzeugen der
  .o-Datei in .drectve gespeichert und beim Linken in eine echte PE32-IAT und
  Import Directory umgesetzt.
