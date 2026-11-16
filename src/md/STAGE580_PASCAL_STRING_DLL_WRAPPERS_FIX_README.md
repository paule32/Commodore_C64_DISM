# Stage 580 – alte IntToStr/StrToInt-Pascal-Wrapper aus PE32-EXE entfernen

**Verbindliche Basis:** d64_dism_stage579.zip. Die Runtime-Änderungen aus Stage 578
und die Double-BSS-Bereinigung aus Stage 579 bleiben erhalten.

## Reproduzierte Ursache

In Stage 579 hatte die eingebettete IDE einen **zweiten Präprozessor** in
`d64_dism.py`. Die normale Compiler-API nutzte bereits das Zielmakro
`__D64_TARGET_PE32__`, aber die GUI bereitete ihre Pascal-Dateien **vor**
diesem Compileraufruf vor und übergab das Zielmakro nicht. Wenn die Unit
`System.Strings.pas` in der IDE direkt für Windows PE32 gebaut wurde, aktivierte
`{$ifndef __D64_TARGET_PE32__}` den veralteten Zweig:

    function IntToStr(...): String;
    begin result := jit_dynstring_from_cstr(_IntToStr(...)); end;

Deshalb konnten die Funktionskörper `__pas_global_inttostr:` und
`__pas_global_strtoint:` trotz der Stage-578-DLL-Anbindung wieder erscheinen.
Das betraf außerdem den von Stage 536 verwendeten parallelen Unit-Build,
bei dem `c64pascal.preprocess_pascal_source` ebenfalls ohne Backend-Makros
aufgerufen wurde.

Zusätzlich war im Stage-579-Archiv `runtime/pascal/test/test_raise.generated.pe32.asm`
als **veraltetes** generiertes Beispiel enthalten (mit genau den gemeldeten
Wrappern). Diese Datei war nicht neu erzeugt worden.

## Korrekturen

1. `d64_dism.py`: `preprocess_pascal_source(..., target=...)` verarbeitet
   `__D64_TARGET_PE32__` beziehungsweise `__D64_TARGET_PE64__` jetzt
   zielabhängig **vor** dem Auswerten von `{$ifdef}` / `{$ifndef}`.
   Die zwei Flags können nicht versehentlich aus den vom Anwender
   bereitgestellten Makros auf ein falsches Backend umgeschaltet werden.
2. GUI-Einzelcompile und CLI übergeben das ausgewählte Ziel an diesen
   Präprozessor.
3. Parallele Unit-Compiles geben `_pascal_target_macros(macros, target)`
   an `c64pascal.preprocess_pascal_source` weiter.
4. `c64pascal/compiler.py`: Wenn der aus Unit-Quelltext **neu berechnete**
   PUI-Vertrag von der vorhandenen PUI abweicht, gilt das vorhandene
   COFF-Objekt nicht mehr als aktuell. Es wird die Unit-Quelle verwendet,
   auch falls die alte Objektdatei einen jüngeren Zeitstempel trägt.
5. Veraltete ausschließlich `test_raise` betreffende Builds im mitgelieferten
   Projekt wurden entfernt: das generierte `.asm`, zwei `.exe` und das `.o`.
   `test_raise.pas` und die Runtime-Quellen bleiben erhalten.
6. `test_stage579.py` prüft das neue BSS-Verhalten mit tatsächlichem
   Backend-Code statt mit dem historischen Assemblerbeispiel.
   `test_stage580.py` deckt IDE-Makros, Unit-Imports, PE32-ASM-Emitter,
   PE64-Altpfa​​d, Parallel-Build und Cache-Schutz ab.

## Erwartete PE32-Ausgabe nach erneutem Build

    import _IntToStr, "libd64_runtime.dll", "jit_pas_inttostr"
    import _StrToInt, "libd64_runtime.dll", "jit_pas_strtoint"

    ; Aufruf der aus der DLL importierten Implementierung:
    push eax
    call _IntToStr
    add esp, 4

Es sollen **keine** Definitionen `__pas_global_inttostr:` oder
`__pas_global_strtoint:` und kein zweiter Aufruf von `_jit_dynstring_from_cstr`
für diese Funktion im PE32-Programm entstehen.

## Neu bauen unter Windows

1. Stage 580 entpacken und **die Stage-580-Version von `d64_dism.py` und
   `c64pascal/compiler.py` verwenden**. Nicht die ältere Stage 579 starten.
2. Alte Compiler-Zwischenprodukte für die Unit `System.Strings` aus dem
   Projekt-Ausgabeverzeichnis entfernen: `System.Strings.pui`,
   `System.Strings.coff32.o` / `System.Strings.o`,
   `System.Strings.generated.pe32.asm` (soweit vorhanden). Ebenso für
   `test_raise`: alte `.o`, `.exe` und generierte `.asm` entfernen.
3. Das Ziel **Windows PE32** auswählen, die Unit/Projektquellen erneut
   kompilieren und die **neu erstellte** `.generated.pe32.asm` prüfen.
4. Die neue `libd64_runtime.dll` aus Stage 578/579 mit NASM und MinGW32
   bauen (`cd runtime && bash build.win32.sh`) und an den vom Programm
   genutzten DLL-Suchort kopieren. Ein alte DLL exportiert die neuen Namen
   möglicherweise nicht; dies ist getrennt von der ASM-Codegenerierung.
5. Anschließend für die EXE wirklich **neu assemblieren/linken**.

Nicht pauschal alle `.pui` oder `.o` anderer Units löschen – nur die
betroffenen alten Produkte oder die bewusst neu zu bauenden Abhängigkeiten.

## Verifikation und Grenzen

    python -m unittest -v test_stage580 test_stage579 test_stage578 test_stage546
    python -m unittest -v test_stage541 test_stage543 test_stage545

Die Umgebung hier hat `antlr4-python3-runtime==4.9.3`, die mitgelieferten
ANTLR-Pascal-Klassen sind aber mit 4.13.2 erzeugt. Deshalb konnte der
komplette Parser-zu-Windows-EXE-Lauf nicht ausgeführt werden. Die Tests
prüfen echte IDE-Präprozessoren, die Unit-Interface-Scanner sowie den
ASM-Emitter mit AST-Daten, **nicht** den nativen Windows-Link oder die
endgültige EXE-Laufzeit. Der Python-Quelltext `d64_dism.py` enthält Python-3.15-
`lazy import`-Syntax und kann in dieser Python-3.13-Umgebung nicht als
Ganzes bytekompiliert werden; die geänderte Präprozessorregion wird separat
extrahiert und ausgeführt.
