# PROLOG Native Runtime – Runtime-Stufe 2 – Windows PE32 / PE32+

Der PROLOG-Compiler erzeugt IA-32- bzw. AMD64-Assembler. COFF32/COFF64 und
PE32/PE32+ werden ausschließlich durch die internen Assembler/Writer/Linker
von `d64_dism.py` erzeugt.

Die frühere Compile-Time-SLD-Auswertung ist kein Ausführungspfad mehr. Fakten,
Regeln, Queries, Backtracking und dynamische Klauseln werden in der erzeugten
Windows-EXE verarbeitet.

## Laufzeitmodell

- 32-Bit-Termhandles auf PE32 und PE32+.
- 16-Byte-Termzellen für VAR, ATOM, INT, STRING, NIL, LIST, STRUCT und LINK.
- transienter Term-Heap für Query-/Klauselinstanzen.
- persistenter Dynamic-Heap mit zweitem Semispace für kopierende GC.
- Trail-Stack für rücksetzbare Variablenbindungen.
- Choice-Point-Stack mit Heap-/Trail-Snapshots.
- lexikalische Cut-Barrieren pro Prädikataufruf.
- Laufzeit-Unifikation mit Occurs-Check.
- strikte, bindungsfreie Termidentität für `==/2`.
- dynamische Atom-Tabelle für den Console-Parser.
- großer Runtime-Speicher per `VirtualAlloc`; keine großen Nullblöcke in der EXE.

Der transiente Query-Heap wird an Query-Grenzen als Region zurückgesetzt. Der
persistente Dynamic-Heap besitzt zusätzlich eine kopierende Kompaktierungs-GC.

## Listen

Unterstützt werden echte Laufzeitlisten:

```prolog
[]
[a,b,c]
[H|T]
[a,b|T]
```

Beispiel:

```prolog
append([], X, X).
append([H|T], X, [H|R]) :- append(T, X, R).

?- append([a,b], [c,d], X).
```

## Unifikation und Occurs-Check

`=/2` arbeitet zur Laufzeit und bindet Variablen. Vor einer VAR->Term-Bindung
prüft `__rt_occurs`, ob die Variable bereits im Zielterm vorkommt. Damit wird
z. B. eine zyklische Bindung wie `X = f(X)` abgewiesen.

`\=/2` testet Nicht-Unifizierbarkeit mit reversiblem Heap-/Trail-Snapshot.

`==/2` verwendet `__rt_equal_terms`: zwei unterschiedliche ungebundene
Variablen sind nicht identisch; Listen und Compound-Terme werden rekursiv und
ohne Bindungen verglichen.

## Choice Points, Trail und Cut

Jeder Klausel-/Alternativversuch kann einen Choice Point anlegen. Gespeichert
werden Heap- und Trail-Zustand. Beim Backtracking werden Bindungen ungetrailt
und der transiente Heap auf den Snapshot zurückgesetzt.

Goal-Links tragen zusätzlich eine lexikalische Cut-Barriere. `!/0` setzt den
Choice-Top auf die Barriere des aktuellen Prädikataufrufs. Dadurch werden nur
die Alternativen seit Eintritt in das betreffende Prädikat abgeschnitten;
äußere Aufrufe bleiben erhalten.

## Disjunktion

`;` wird als echtes Runtime-Ziel behandelt:

```prolog
choose(X) :- (X = one ; X = two ; X = three).
```

Linker und rechter Zweig laufen jeweils unter einem reversiblen Choice-Snapshot
und respektieren Cut- sowie Stop-Search-Barrieren.

## Arithmetik und `is/2`

Der Runtime-Evaluator `__rt_eval_arith` unterstützt derzeit:

```text
+X   -X
A+B  A-B  A*B  A/B  A mod B
```

sowie numerische Vergleiche:

```prolog
<   =<   >   >=
```

Beispiel:

```prolog
calc(X) :- X is -(3+4)*2.
?- calc(X), X >= -20.
```

Division bzw. Modulo durch Null lässt den betreffenden Zielzweig fehlschlagen.

## Dynamische Fakten und Regeln

Unterstützt werden:

```prolog
assert(Clause).
asserta(Clause).
assertz(Clause).
retract(Pattern).
```

Dabei kann `Clause` ein Fakt oder eine vollständige Regel sein:

```prolog
?- asserta((path(X,Y) :- edge(X,Y))).
?- assertz(edge(a,b)).
?- path(a,X).
```

Dynamische Klauseln werden mit kompletter `(:-)/2`-Struktur persistent
gespeichert. Beim Match werden sie frisch in den transienten Heap geklont, so
dass Klauselvariablen pro Versuch neue Laufzeitvariablen sind.

`asserta/1` fügt am Anfang der dynamischen Datenbank ein; `assertz/1` und
`assert/1` hängen hinten an. `retract/1` entfernt die erste passende dynamische
Klausel und behält erfolgreiche Pattern-Bindungen.

## Garbage Collection / Kompaktierung

`__rt_dyn_db_compact` entfernt inaktive `retract`-Slots aus der dynamischen
Klauseltabelle und erhält die Klauselreihenfolge.

`__rt_gc_dynamic` arbeitet als kopierende Semispace-GC:

1. Datenbank komprimieren.
2. aktive persistente Klauseln in temporäre frische Termgraphen klonen.
3. aktiven und alternativen Dynamic-Heap vertauschen.
4. Klauseln in den neuen aktiven Semispace kopieren.
5. Root-Handles in der dynamischen Datenbank aktualisieren.

Die GC wird bei hoher Dynamic-Heap-Auslastung automatisch aufgerufen und ist
auch über `gc/0` bzw. `garbage_collect/0` erreichbar.

## Operatorpräzedenz

Sowohl Quellparser als auch nativer Console-Parser berücksichtigen die für die
Runtime benötigten Ebenen:

```text
:-
;
,
=  \=  ==  is  <  =<  >  >=
+  -
*  /  mod
unäres + / -
```

Damit sind unter anderem möglich:

```prolog
?- X is -(3+4)*2, (p(X) ; q(X)).
?- assert((dyn(X) :- p(X), q(X))).
```

## Interaktiver Console-Top-Level

`repl/0` startet den nativen `?- `-Top-Level. Gibt es weder statische Query
noch `main/0`, startet ein Console-Programm automatisch im REPL.

Nach jeder Lösung wartet die Runtime nun auf eine Entscheidung:

```text
X = one.
; = weitere Lösung, ENTER = fertig:
```

- `;` setzt die Suche mit den noch lebenden Choice Points fort.
- Enter setzt `__prolog_stop_search` und beendet nur die aktuelle Query.
- Wird nach `;` keine weitere Lösung gefunden, folgt `false.`.

Beispiel:

```text
?- member(X,[a,b,c]).
X = a.
; = weitere Lösung, ENTER = fertig: ;
X = b.
; = weitere Lösung, ENTER = fertig: ;
X = c.
; = weitere Lösung, ENTER = fertig: ;
false.
?- 
```

`halt.` und `quit.` verlassen den Top-Level.

## Console und GUI

Console:

- PE Subsystem 3
- `AllocConsole`, `ReadFile`, `WriteFile`
- interaktives REPL und schrittweises `;`-Backtracking

GUI:

- PE Subsystem 2
- keine Console-/ReadFile-Abhängigkeit
- Runtime-Unifikation, Regeln, Backtracking, assert/retract und GC bleiben aktiv
- Ausgabe wird gesammelt und per `MessageBoxA` gezeigt
- `repl/0` ist nicht interaktiv

## Windows-Ziele

- PE32: Machine `0x014C`, Optional Header Magic `0x010B`.
- PE32+ / AMD64: Machine `0x8664`, Optional Header Magic `0x020B`.
