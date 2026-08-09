# PROLOG Runtime: member/2

## Fehlerbild

Im Console-REPL lieferte

```prolog
?- member(X,[a,b,c]).
```

`false.` obwohl die Liste korrekt geparst wurde.

## Ursache

`member/2` war weder als native Builtin-Routine registriert noch als automatisch
verfuegbare Standardbibliotheks-Klausel vorhanden. Der Runtime-Solver fiel daher
auf die normale Praedikat-Suche zurueck und fand keine Klausel `member/2`.

## Loesung

Der Compiler bindet nun automatisch eine kleine PROLOG-Standardbibliothek ein:

```prolog
member(X, [X|_]).
member(X, [_|T]) :- member(X, T).
```

Die Klauseln werden als normale native Runtime-Klauseln kompiliert. Dadurch
verwenden sie dieselbe Laufzeitlogik wie benutzerdefinierte Praedikate:

- Runtime-Unifikation
- Trail Stack
- Choice Points
- Backtracking
- interaktives `;` fuer weitere Loesungen
- Cut-Barrieren im nachfolgenden Goal-Pfad

Definiert das Benutzerprogramm selbst `member/2`, wird die Standarddefinition
nicht zusaetzlich eingebunden.

## Erwartetes Verhalten

```text
?- member(X,[a,b,c]).
X = a.
; = weitere Loesung, ENTER = fertig: ;
X = b.
; = weitere Loesung, ENTER = fertig: ;
X = c.
; = weitere Loesung, ENTER = fertig: ;
false.
?-
```

Wird nach einer Loesung ENTER statt `;` gedrueckt, endet nur die aktuelle Suche.

## Targets

Geprueft mit den internen d64_dism-Toolchains:

- Windows PE32 / IA-32 / COFF32
- Windows PE32+ / AMD64 / COFF64

Beide Console-Images besitzen `member/2` als nativen Runtime-Praedikatpfad.
