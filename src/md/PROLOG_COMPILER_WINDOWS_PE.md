# PROLOG Compiler – Windows PE32 / PE32+ – native Runtime-Stufe 2

`d64_dism.py` bindet das PROLOG-Frontend aus `d64prolog/compiler.py` und die
native Laufzeit aus `d64prolog/runtime.py` ein. Der Compiler erzeugt nur
Assembler; COFF und PE werden durch die internen d64_dism-Assembler und -Linker
erzeugt.

## GUI-Integration

- Projekt-Hauptknoten `PROLOG-Programme`
- `Datei -> Neu -> Projekt: PROLOG`
- `Datei -> Neu -> Prolog-Programm`
- Endungen `.pl`, `.prolog`
- Targets `Windows PE32` und `Windows PE64` (= PE32+ / AMD64)
- Windows-Modi `Console` und `GUI`
- Compile -> ASM-Tab -> Assemble -> Link -> Start
- F2 verwendet denselben vollständigen Buildpfad

`.pro` bleibt die d64_dism-Projektdateiendung.

## Sprach-/Runtime-Funktionen

Neben Fakten, Regeln, Rekursion, Variablen, Strings, Integern und Listen stehen
jetzt zur Laufzeit zur Verfügung:

- `=/2`, `\=/2`, striktes `==/2`
- Occurs-Check
- Choice Points + Trail Stack
- lexikalischer Cut `!/0`
- Disjunktion `;/2`
- `is/2`
- `+`, `-`, `*`, `/`, `mod`
- `<`, `=<`, `>`, `>=`
- `assert/1`, `asserta/1`, `assertz/1` für Fakten **und Regeln**
- `retract/1`
- `gc/0`, `garbage_collect/0`
- Console-`repl/0`
- Operatorpräzedenz im Source- und Runtime-Parser
- `;` im interaktiven Top-Level zum Abrufen der nächsten Lösung

Beispiel:

```prolog
edge(a,b).
edge(b,c).

path(X,Y) :- edge(X,Y).
path(X,Y) :- edge(X,Z), path(Z,Y).

main :-
    asserta((dynamic_path(X,Y) :- path(X,Y))),
    X is 3 + 4 * 2,
    writeln(X),
    repl.
```

## Dynamische Regeln

Klammerausdrücke mit `:-` werden als Term geparst und können dynamisch
assertiert/retrahiert werden:

```prolog
?- assert((reachable(X,Y) :- edge(X,Y))).
?- reachable(a,Y).
?- retract((reachable(X,Y) :- Body)).
```

`asserta` steht vor bereits vorhandenen dynamischen Klauseln; `assertz` hängt
hinten an.

## Speicher

Der große Runtime-Speicher wird per `VirtualAlloc` angelegt. Der transiente
Term-Heap wird an Query-Grenzen als Region wiederverwendet. Die persistente
dynamische Datenbank verwendet zwei Semispaces und eine kopierende GC, damit
`assert/retract` nicht dauerhaft Löcher und tote Klauseln ansammeln.

## Interaktiver Top-Level

Console:

```text
?- path(a,X).
X = b.
; = weitere Lösung, ENTER = fertig: ;
X = c.
; = weitere Lösung, ENTER = fertig:
?- 
```

Das `;` wird gelesen, während der Solver-Stack noch aktiv ist. Dadurch werden
wirklich die noch vorhandenen Choice Points fortgesetzt; die Query wird nicht
neu gestartet.

## Binärziele

PE32:
- IA-32 / Machine `0x014C`
- PE Magic `0x010B`

PE32+:
- AMD64 / Machine `0x8664`
- PE Magic `0x020B`

Console verwendet Subsystem 3, GUI Subsystem 2.
