# Stage 487 – erste Linux-dBASE-/WFM-Integration (auf Stage 486)

## Erreicht

- Die Einträge **Linux Ubuntu 22.04 32-Bit** und **Linux Ubuntu 22.04 64-Bit** sind für dBASE-Quelldateien `.prg` und den geöffneten `.wfm`-Formular-Designer auswählbar.
- Der eingebettete WFM-Designer zeigt die beiden Linux-Ziele auch in seiner Ziel-ComboBox.
- `Kompilieren` schreibt `<name>.generated.linux32.asm` bzw. `.linux64.asm`.
- `Assemble`/`Kompilieren + Linken` erzeugt über den internen Assembler und ELF-Objektschreiber ein ELF32-/ELF64-Objekt (`.linux32.o`/`.linux64.o`) und ein statisches ELF-Programm (`.elf32`/`.elf64`). Keine externen Aufrufe von `as`, `ld`, `gcc`, `make`.
- Auf Linux wird das erzeugte ELF ausführbar gemacht und kann über `Starten` ausgeführt werden. Unter Windows ist Cross-Kompilieren/Linken möglich, der Start von ELF wird weiterhin gesperrt.
- Linux-`.prg`: begrenzte freistehende Konsolenstufe für `#define`, `#include`, `#if` und einfache konstante Variablenzuweisungen (`LOCAL`, `STORE`, `=`) und `?`/`??`, Rechenausdrücke und Stringkonkatenation. Generiert echte native Linux-x86-/AMD64-Systemaufrufe `write` und `exit`.
- Linux-`.wfm`: Formularmodell wird mit dem bestehenden WFM-Parser gelesen. Ein *intern assembliertes und gelinktes ELF-Programm* startet mit `execve` die eingebettete Qt5/PyQt5-Formular-Runtime über `/usr/bin/env python3 -c ...`. Es gibt **keine zusätzliche .py-Datei** im Ausgabeverzeichnis. Die Linux-Umgebung (`PATH`, `DISPLAY`, `QT_QPA_PLATFORM`, virtuelle Umgebungen) wird korrekt durchgereicht.
- Unterstützte einfache WFM-Steuerelemente: Button, Label, Edit/LineEdit, Memo/TextEdit, CheckBox, RadioButton, ComboBox, ListBox, GroupBox, ProgressBar. Die üblichen Rechteck-, Text-/Titel-, Sichtbarkeits-/Enabled- und Checked-Eigenschaften werden verwendet. Einfache `onClick`-Methoden mit konstanten `?`, `??` sowie Text-/Caption-Zuweisungen werden ausgeführt.
- Nicht unterstützte Steuerelemente, Ereignisse, dynamische Ausdrücke und Windows-FFI-Imports werden mit einer verständlichen Compilerdiagnose abgewiesen.
- Windows PE32/PE64-Compiler und seine `libd64_qt5.dll` bleiben unverändert.

## WICHTIGE EINSCHRÄNKUNGEN – kein vollständiger Linux-WFM-Port

- Die Qt5-Bridge ist **noch keine native ELF-.so-/libQt5Widgets-Verlinkung** und keine direkte Übersetzung aller dBASE-Methoden in Linux-Maschinencode. Sie verwendet das Linux-Python-Programm mit **PyQt5** zur GUI-Laufzeit. Ein Linux-System muss `python3` sowie `PyQt5` in der von `PATH` aufgelösten Python-Umgebung besitzen.
- Der ELF-Linker bleibt in dieser Stage **statisch** und stellt noch keine dynamischen ELF-Imports/PLT/GOT, `.so`-Anbindung oder libc bereit.
- Umfangreiche WFM-Komponenten, Methoden, Ereignisse, Formulareigenschaften, Objektverwaltung, Windows-API-Aufrufe, dynamische dBASE-Variablen/-Schleifen und WFM-Bootstrap-Anweisungen sind noch nicht auf Linux portiert. Diese Bestandteile dürfen nicht als vollständig funktionsfähig angesehen werden.
- Linux-`.prg`-Variablenzuweisungen werden für diese erste Stufe zur Compile-Zeit als Konstanten ausgewertet. Programmdynamik (Schleifen, interaktive Eingaben, freie Funktionsaufrufe) wird ausdrücklich abgewiesen.
- ELF32 kann hier strukturell assembliert und gelinkt werden; eine tatsächliche Ausführung benötigt Linux-i386-Unterstützung. Die ELF64-Ausführung ist unter Linux x86-64 getestet.
- Kein vollständiger Test der realen Qt5-Fenstergrafik in dieser CI-Umgebung (PyQt5 ist hier nicht installiert). Der ELF64->Python-Qt-Runtime-Prozesswechsel wurde mit einem Test-Modul geprüft. Weitere Windows- und Ubuntu-GUI-Tests sind erforderlich.

## Testaufrufe

```bash
python -m pytest -q test_stage486_linux_elf.py test_stage487_linux_dbase_wfm.py
```

Beispiele: `examples/linux_stage487/hello.prg`, `examples/linux_stage487/Form1.wfm`.
