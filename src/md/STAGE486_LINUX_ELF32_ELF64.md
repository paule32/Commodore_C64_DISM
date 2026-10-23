# Stage 486 – Linux Ubuntu 22.04, ELF32 und ELF64 (erste interne Ausbaustufe)

Verbindliche Ausgangsbasis: d64_dism_asm_485.zip.

## Hauptmenü Erstellen

- Kompilieren + Linken
- Kompilieren
- Separator
- Windows PE 32-Bit / Windows PE 64-Bit (exklusiv auswählbar)
- Separator
- Linux Ubuntu 22.04  32-Bit / Linux Ubuntu 22.04  64-Bit (selbe exklusive QActionGroup)
- Separator
- Commodore C= 64 / AMIGA 500
- Separator
- Starten

Die Linux-Ziele stehen außerdem in den Architektur-Comboboxen des Dokumenteditors.

## Umfang der neuen Linux-Werkzeugkette

`linux_elf.py` schreibt auf jeder Python-fähigen Hostplattform (Windows/Linux):

- ELF32/i386 ET_REL `.o` mit `.text`, `.data`, `.bss`, Symboltabelle, `.rel.text` und `.rel.data`.
- ELF64/x86-64 ET_REL `.o` mit `.text`, `.data`, `.bss`, Symboltabelle, `.rela.text` und `.rela.data`.
- Eigenen ELF32- und ELF64-Linker für ein oder mehrere dieser Objektdateien.
- ELF ET_EXEC mit Lade-Segmenten RX für Code und RW für Daten/BSS ohne dynamischen Linker.
- COFF-Encoder als bereits vorhandenen Instruktions-Byte-Encoder; es wird **kein** COFF-Objekt in die ELF-Datei eingebettet. Relocation-Einträge und Dateiformat sind ELF.
- Symboldefinitionen und symbolische Referenzen, absolute Adressen, 32-Bit-PC-relative Relocations, 64-Bit-Adressen sowie `.bss`.
- `syscall` und `sysenter` als neue native x86-64 Opcodes.
- Vorhandene `%include`, `%define`, `%if`, `%elif`, `%endif` sowie Intel- und unterstützte AT&T-Schreibweisen bleiben durch den bisherigen Quelltext-Präprozessor erhalten.

## GUI-Anbindung

Im ersten Schritt sind Linux-ELF-Builds für eigenständige **Assemblerdokumente** (`.asm`, `.s`) aktiviert. Im Menü `Erstellen` wird nach Auswahl `linux32` oder `linux64` mit `Kompilieren + Linken` eine `.linux32.o` oder `.linux64.o` sowie eine `.elf32` oder `.elf64` Datei **neben der Quelldatei** erzeugt.

`Kompilieren` allein führt bei einer handgeschriebenen ASM-Datei keinen Linklauf aus. `Starten` wird erst bei einer frischen erfolgreich gelinkten Datei aktiviert. Auf Windows bleibt der Linux-Start deaktiviert (Dateien werden dort trotzdem erzeugt). Linux-Binaries erhalten das Ausführungsbit.

## Explizite Grenzen dieser Stage

- Noch kein Linux-dBASE-/WFM-/Pascal-/C-Frontend-Backend und keine Linux-GUI-/Qt5-Runtime: bestehende Windows-PE-Compiler-Ausgaben dürfen nicht als Linux-Code ausgegeben werden. Die Zielauswahl in diesen Frontends weist deshalb auf das derzeit fehlende Compilerziel hin.
- Kein ELF-Dynamic-Linking, kein `libc`, kein PLT/GOT, keine TLS, keine Shared Objects, keine GNU-Linkerskripte und keine externen Archive.
- Keine allgemeine Importverarbeitung: Windows `IMPORT`/DLL wird ausdrücklich abgelehnt.
- ELF32 erfordert zur direkten Ausführung einen Linux-Kernel mit IA-32-Unterstützung. Unter Windows können ELF-Dateien nur erstellt, nicht nativ ausgeführt werden.
- Der Assembler unterstützt weiterhin nur die bisher implementierten x86-/x64-Instruktionen und die erweiterte AT&T-Teilmenge, nicht den vollen GNU `as`-Befehls-/Direktivenumfang.

## Tests

`pytest -q test_stage486_linux_elf.py`

Der neue ELF64-Textausgabe- und Exit-Test wurde unter Linux ausgeführt. ELF32 wurde als korrektes ELF32-i386-Objekt/Executable erzeugt und strukturell überprüft; 32-Bit-Programmausführung ist auf dieser Testmaschine nicht möglich. Beide Architekturen unterstützen symbolische Auflösung zwischen zwei eigenen ET_REL-Objekten.
