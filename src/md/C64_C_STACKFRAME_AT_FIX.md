# C64-C-Stackframe-Fix fuer `@` im Assembler

## Fehlerbild

Beim Kompilieren einer C64-C-Datei mit einer automatischen lokalen Variable,
zum Beispiel:

```c
int main(void)
{
    int value;
    value = 1;
    return value;
}
```

konnte der erzeugte Assembler eine Zeile wie diese enthalten:

```asm
sta @cframe:-2
```

Der interne C64-Assembler akzeptiert `@` nicht in Ausdruecken und meldete:

```text
Ungueltiges Zeichen im Ausdruck: '@'
```

## Ursache

`@cframe:<offset>` ist ausschliesslich eine interne Markierung des
C-Codegenerators. Normale Zuweisungen wurden bereits in hardware-stackrelative
6510-Zugriffe umgesetzt. Die automatische Nullinitialisierung lokaler
Variablen verwendete jedoch noch `_store_variable()` aus dem Pascal-Backend,
das den Labeltext direkt ausgab.

## Korrektur

`_CCodeGenerator._store_variable()` leitet nun jeden Schreibzugriff ueber
`_emit_store_access()`. Ein Stackslot mit Offset `-2` wird dadurch zum Beispiel
so ausgegeben:

```asm
ldx __c_frame_pointer
sta $00FE,x
```

16-Bit-Werte benutzen entsprechend zwei Bytes:

```asm
sta $00FE,x
sta $00FF,x
```

Vor der Rueckgabe des erzeugten Assemblers wird ausserdem geprueft, dass kein
`@cframe:`-Marker mehr enthalten ist.
