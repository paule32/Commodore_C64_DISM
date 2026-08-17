# Stage 59 – Assembler Mini-Map und F2 Build/Link/Start

## Mini-Map

Der Rohdaten-Editor und der erzeugte ASM-Editor verwenden beide `SourceEditorWithMiniMap`.
Damit besitzen beide dieselbe `SourceMiniMap` mit identischem Scroll-, Klick-, Drag-, Mausrad- und 120-px-Verhalten.

## F2 im Rohdaten-Assembler

Für `.asm`, `.s`, `.a65`, `.m68k` und `.inc` wird F2 jetzt vom zentralen Buildpfad akzeptiert.

Ablauf:

1. Datei bei Bedarf speichern.
2. Assemblercode mit der internen Toolchain assemblieren.
3. Für PE32/PE64 intern zum finalen PE-Image linken.
4. Nur wenn das erzeugte Artefakt die Endung `.exe` besitzt, die EXE direkt starten.
5. `.dll`, `.prg`, `.adf` und `.amiga` werden nur erzeugt und nicht durch diesen neuen EXE-Autostart gestartet.

## F2 im erzeugten ASM-Tab

`SourceTextEdit::Key_F2` sendet dort jetzt über `build_generated_requested` an `build_and_run_generated_assembly_document`.
Der sichtbare/editierte ASM-Text ist die verbindliche Eingabe; die Hochsprache wird nicht erneut kompiliert.
Für PE32/PE64 werden vorhandene Projektobjekte/-archive wie beim normalen Hauptbuild an den internen Linker übergeben.

## Kein externer Build

Die neuen F2-Pfade rufen weder `qmake` noch `mingw32-make` auf. Der Start erfolgt ausschließlich über die bereits erzeugte EXE.

## Regression

- Stage-59-spezifisch: 6/6
- Gesamtprojekt: 615/615
- interner PE32 Minimal-Build: MZ / 1024 Bytes
- interner PE64 Minimal-Build: MZ / 1024 Bytes
