# C-Set-Runtime: Funktionsaufrufe in Ausdrücken

## Fehlerbild

Beim Kompilieren von `c64c/runtime/set_runtime.c` erschien:

```text
Methode nicht gefunden: SetOf.
```

Betroffen waren unter anderem:

```c
return value | SetOf(element);
return value & ~SetOf(element);
return (value & SetOf(element)) != 0;
```

## Ursache

`SetOf` war als normale C-Funktion samt Prototyp bekannt. Der Fehler trat vor der
eigentlichen Aufruferzeugung in `_CodeGenerator._expression_type()` auf.

Bei einem `CallExpression` berücksichtigte die Typprüfung nur eingebaute
Funktionen und Klassenmethoden. Ein globaler C-/PUI-Funktionsaufruf wurde deshalb
an `_resolve_method_call()` weitergereicht. Daraus entstand die irreführende
Meldung über eine fehlende Methode.

## Korrektur

Vor der Methodenauflösung wird nun geprüft:

```python
routine = self.external_routines.get(name)
```

Bei einer Funktion wird ihr `result_type` zurückgegeben. Eine Prozedur in einem
Ausdruck erzeugt eine passende Meldung, dass sie keine Funktion ist.

Die Korrektur gilt für:

- Funktionen derselben C-Translation-Unit,
- Funktionen aus `#pragma link`-Modulen,
- Funktionen aus Header-Prototypen,
- Pascal-PUI-Funktionen,
- C64 und Amiga.
