# LISP READ + ASM-Farben

- `(read)` liefert im Windows-Console-Modus einen String zurück.
- `ReadFile` wartet durch den normalen Windows-Console-Line-Input bis ENTER.
- CR/LF wird aus dem Rückgabestring entfernt.
- Der 4096-Byte-Eingabuffer wird einmalig mit `VirtualAlloc` erzeugt.
- PE32 und PE32+ verwenden den vorhandenen internen d64_dism Assembler/Linker.
- GUI-LISP weist `(read)` beim Kompilieren mit einer klaren Fehlermeldung zurück.
- ASM auf Navy: Grundtext gelb, Mnemonics weiß/fett, Kommentare grau, Sprungziele hellblau.
