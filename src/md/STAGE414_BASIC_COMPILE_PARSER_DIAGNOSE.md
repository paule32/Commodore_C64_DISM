# Stage 414 – C64-BASIC-Compilerpfad und tatsächliche Parser-Anweisung sichtbar machen

Basis: d64_dism_asm_413.zip.

## Anlass

Im C64-Editor zeigt das Bild die Anweisung `98 LOAD SPRITE "sprites.spr"`. Der Compile-Dialog meldet jedoch
`BASIC-Zeile 98: Variable oder Arrayelement erwartet.`. Diese Meldung entsteht ausschließlich bei der
Prüfung eines Variablen- beziehungsweise Zuweisungsziels. Der sichtbare Befehl ist in Stage 413 korrekt
implementiert. Der sichtbare Testcode einschließlich REM-Zeilen mit Tabulatoren wurde direkt und nach
C64-Editor-Wrapping/Gutter-Nummerierung erfolgreich kompiliert. Deshalb ist die tatsächliche Ursache
im Windows-Lauf nicht nachgewiesen und darf nicht als behoben gelten.

## Neue Diagnose in d64_dism.py

Bei einem C64-BASIC-Quelltext mit einer regulären `LOAD SPRITE`-Anweisung schreibt die GUI vor dem
Übersetzen in das normale Protokoll:

    C64 BASIC COMPILER: T:\\...\\c64basic\\compiler.py; LOAD SPRITE=ja
    C64 BASIC EINGABE: '98 LOAD SPRITE "sprites.spr"'

Ist die importierte Compilerdatei veraltet und besitzt sie keine
`c64_basic_sprite_command`-Implementierung, gibt die GUI einen konkreten Hinweis samt Modulpfad,
statt mit einer irreführenden Syntaxmeldung fortzufahren.

Bei einem Compilerfehler werden – soweit vorhanden – die ursprüngliche Parser-Anweisung und die
wirkliche BASIC-Quellzeile protokolliert und im Fehlerdialog angegeben. Beispiel:

    Parser-Anweisung: 'ABC=...'
    Quelltext im Compiler: '98 ABC=...'
    Compiler-Modul: T:\\...\\c64basic\\compiler.py

Die Anweisungsdiagnose wird im Compiler im Ausnahmefall ergänzt, ohne das Parsen erfolgreicher Programme
zu ändern. Debug-Ausgaben können auch versteckte bzw. unerwartete Zeichen über `repr` sichtbar machen.

## Test

1. Stage 414 vollständig entpacken und aus **diesem** Ordner `d64_dism.py` ausführen.
2. BASIC-Programm mit Zeile 98 öffnen, Compile anklicken.
3. Im Protokoll die Zeilen `C64 BASIC COMPILER` und `C64 BASIC EINGABE` prüfen.
4. Wenn weiterhin eine Fehlermeldung erscheint, zusätzlich `C64 BASIC PARSERFEHLER` und
   `C64 BASIC FEHLERZEILE` sowie den Fehlerdialog kopieren.

Die hier implementierte Stage ist eine zielgerichtete Diagnose und ein Schutz vor veralteten
Compilerimporten, keine behauptete abschließende Fehlerbehebung in der Windows-GUI.

## Regressionen

`python -m unittest -v test_stage414_c64_basic_gui_source_diagnostics test_stage413_c64_load_sprite_host test_stage411_c64_setnam_pointer test_stage410_c64_load_filename_petscii`

26 Tests bestanden. Python-Syntax von `d64_dism.py` und `c64basic/compiler.py` geprüft. Ein Windows-/PyQt5-
Laufzeittest steht noch aus.
