# Stage 578 – Pascal `IntToStr`/`StrToInt` direkt aus der Runtime-DLL (PE32)

**Verbindliche Basis:** vom Benutzer hochgeladenes `d64_dism_stage577(1).zip`.
**Geltungsbereich:** Windows PE32 (i386). PE64/C64/Amiga behalten bisherige Implementierungszweige.

## Ursache in Stage 577

`System.Strings.pas` implementierte `IntToStr` und `StrToInt` als Pascal-Wrapper,
die der Compiler als `__pas_global_inttostr` und `__pas_global_strtoint`
in jede konsumierende PE32-Assembly übernehmen konnte. Der Wrapper für `IntToStr`
rief `jit_dynstring_from_cstr(_IntToStr(...))` auf, obwohl
`runtime/pascal/inttostr.asm` bereits `_jit_dynstring_from_cstr` nutzt und
einen fertig allozierten Pascal-DynString-Datenzeiger liefert. Der zusätzliche
Aufruf war unnötig und konnte den Zwischenstring verlieren.

## Neue PE32-Aufrufe

`System.Strings.pas` deklariert jetzt im `interface`-Teil:

```pascal
function IntToStr(AValue: Integer): String; cdecl;
    external 'libd64_runtime.dll' name 'jit_pas_inttostr';
function StrToInt(S: String): Integer; cdecl;
    external 'libd64_runtime.dll' name 'jit_pas_strtoint';
```

Die Interface-Importe kommen durch die PUI-Metadaten zum konsumierenden
Programm. Der Compiler erzeugt in PE32 nur noch sinngemäß:

```asm
import _IntToStr, "libd64_runtime.dll", "jit_pas_inttostr"
import _StrToInt, "libd64_runtime.dll", "jit_pas_strtoint"

push eax
call _IntToStr
add esp, 4
; eax = Pascal-Stringdatenzeiger, nicht C-Pointer mit Fremd-Ownership
```

**Keine** Pascal-Routine `__pas_global_inttostr:` bzw.
`__pas_global_strtoint:` wird für diese Unit mehr generiert.

Die NASM-Implementierungen bleiben in `runtime/pascal/inttostr.asm` und
`runtime/pascal/strtoint.asm`, haben zusätzlich die C-ABI-kompatiblen
COFF-Symbole `_jit_pas_inttostr`/`_jit_pas_strtoint` und werden über die
`.def`-Dateien mit den DLL-Exportnamen `jit_pas_inttostr`/`jit_pas_strtoint`
veröffentlicht. Die vorhandenen statischen Labels `IntToStr`, `_IntToStr`,
`StrToInt`, `_StrToInt` bleiben für Altnutzer erhalten.

`inttostr.asm` verwendet bei Einbau IN die DLL mit
`-dJIT_PASCAL_RUNTIME_INTERNAL=1` das vorhandene interne COFF-Symbol
`__jit_dynstring_from_cstr`, um keine Selbst-Import-Abhängigkeit zu erzeugen.
Ein eigenständig assembliertes `inttostr.o` benutzt unverändert die bisherige
öffentliche C-ABI-Bindung.

## Build-Schritte unter MSYS2 MinGW32

Vom Projektverzeichnis:

```bash
cd runtime
bash build.win32.sh
```

oder für den zweiten, im Stage-577-Projekt vorhandenen Runtime-Buildbaum:

```bash
cd runtime/compiler
bash build.win32.sh
```

Benötigt werden wie bisher GCC/G++, NASM und MinGW32 (i686-w64-mingw32).
**Die im Stage-577-Archiv befindlichen vorkompilierten Runtime-DLLs sind alt.**
Das neue `libd64_runtime.dll` muss zuerst gebaut und für die EXE in den
Windows-DLL-Suchpfad (normalerweise neben die EXE) kopiert werden. Es wurden
keine neuen DLL-/EXE-Binaries vorgetäuscht.

Alle PE32-PUI/Assembler/COFF-Zwischenprodukte für `System.Strings` müssen neu
erstellt werden. Die im Archiv auffindbaren veralteten PE32-Erzeugnisse dieser
Unit wurden entfernt. Andere bestehende Buildprodukte blieben unangetastet.
Bei explizitem `{$L inttostr.o}` oder `{$L strtoint.o}` in fremden
**PE32-Hauptprogrammen** sind diese Direktiven ebenfalls zu entfernen, da
beide Funktionen jetzt über die Runtime-DLL bereitgestellt werden. Das
mitgelieferte `test_raise.pas` verwendet eine zielabhängige Guard-Direktive.

## Compiler-Präprozessor

Das bekannte IDE-Zielmakro `__D64_TARGET_PE32__` gilt jetzt ebenfalls bei
direkten `c64pascal.compiler`-Aufrufen und bei automatisch geladenen Units.
Analog existiert `__D64_TARGET_PE64__` für den 64-Bit-Pfad. Zielmakros sind
Backend-abhängig, keine vom Anwender überschreibbaren Auswahloptionen.
Die Testprogramme des Projekts verwenden die vorhandene IDE-Makrobenennung.

## Prüfungen

```bash
python -m unittest -v test_stage578
python -m unittest -v test_stage545 test_stage546 test_stage578
python test_stage532.py
python -m py_compile c64pascal/compiler.py
bash -n runtime/build.win32.sh runtime/compiler/build.win32.sh
```

In dieser Umgebung: 6/6 neue Regressionstests, 20/20 Tests aus den genannten
`unittest`-Modulen und vier Stage-532-Smoketests erfolgreich. Quellcode- und
Shell-Syntax geprüft. **Kein Windows-DLL-Link und keine native
Windows-Laufzeitprüfung**: hier fehlen MinGW32 und NASM. Außerdem ist die
lokal installierte Python-ANTLR-Laufzeit 4.9.3 älter als der mit ANTLR 4.13.2
generierte Pascal-Parser. Tests verwenden für die Codegenerierung deshalb den
im Projekt vorhandenen Parser-unabhängigen Test-Loader.

## ABI-Details

- PE32, `cdecl`, 32-Bit-Parameter auf dem Stack, Caller räumt Parameter auf.
- `IntToStr(Integer): String` liefert einen Pascal-DynString-Datenzeiger in
  `EAX`. Die DLL allocatiert über denselben Runtime-Speicherallocator wie
  die übrigen Pascal-String-Funktionen.
- `StrToInt(String): Integer` liest den nullterminierten Datenbereich eines
  Pascal-Strings. Die Semantik des bisherigen Assemblers bleibt bestehen:
  bei ungültigen Zahlen/Überlauf `0`, kein Pascal-Exception-Throw.
- Integer-Grenzen `-2147483648` bis `2147483647` bleiben erhalten.
- PE64 wurde **nicht** auf diese neuen 32-Bit-Exports umgestellt; die beiden
  hier eingebundenen NASM-Dateien enthalten ausschließlich i386-Code.

