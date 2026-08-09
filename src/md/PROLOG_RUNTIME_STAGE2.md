# PROLOG Runtime Stage 2 – Änderungen

Diese Stufe schließt die im vorherigen Runtime-Stand noch offenen Punkte:

1. dynamische Regeln über `assert((Head :- Body))`
2. getrennte Einfügereihenfolge für `asserta` und `assertz`
3. striktes, bindungsfreies `==/2`
4. lexikalisch begrenzter Cut über verschachtelte Prädikataufrufe
5. `is/2` und Integerarithmetik
6. Disjunktion `;/2`
7. Operatorpräzedenz im Quell- und REPL-Parser
8. kopierende GC/Kompaktierung der persistenten dynamischen Datenbank
9. Occurs-Check bei Variablenbindungen
10. interaktives `;` zum schrittweisen Abrufen weiterer Lösungen

Die komplette Runtime wird als IA-32- oder AMD64-Assembler erzeugt und durch
die internen d64_dism-COFF-/PE-Komponenten gebaut.

## Standardbibliothek: member/2

`member/2` ist nun ohne eigene Definition verfuegbar. Intern werden die beiden
Standardklauseln als normale native Runtime-Klauseln eingebunden. Dadurch liefert
`?- member(X,[a,b,c]).` per Backtracking `X = a`, `X = b`, `X = c` und arbeitet
mit dem vorhandenen interaktiven `;`-Mechanismus. Eine benutzerdefinierte
`member/2`-Definition ersetzt die automatische Standarddefinition.

## REPL-Parser: unvollständige Operatoren

Der native Präzedenzparser propagiert fehlende rechte Operanden nun als
`INVALID` bis zum Top-Level. Eingaben wie `?- X is 2 + 2 -.` erzeugen
`syntax_error.` statt einen unvollständigen Term an den Solver zu übergeben.
