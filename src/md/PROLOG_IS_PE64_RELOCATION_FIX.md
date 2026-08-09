# PROLOG `is/2` – PE32+ Runtime-Fix

## Fehlerbild

Im interaktiven Console-REPL lieferten beide Queries:

```prolog
?- X is 1 + 3.
?- (X is 1 + 3).
```

fälschlich `false.`.

## Ursache

Der native PROLOG-Parser war logisch korrekt. Der Fehler lag im internen
AMD64-/COFF64-Assembler von `d64_dism.py`.

Bei RIP-relativen Speicheroperanden mit einem nachfolgenden Immediate, z. B.

```asm
add dword ptr [__prolog_parse_pos], 2
```

wurde immer `IMAGE_REL_AMD64_REL32` verwendet. Die CPU berechnet RIP-relative
Adressen jedoch relativ zum Ende der *gesamten* Instruktion. Nach dem disp32
folgen hier noch vier Immediate-Bytes. COFF/AMD64 stellt dafür die Varianten
`IMAGE_REL_AMD64_REL32_1` bis `_5` bereit.

Ohne `REL32_4` adressierte die Instruktion effektiv:

```text
__prolog_parse_pos + 4
```

statt `__prolog_parse_pos`. Dadurch wurde die Parserposition beim Wortoperator
`is` nicht um zwei Zeichen weitergesetzt. Der rechte Ausdruck wurde deshalb als
Atom `is` interpretiert und der Runtime-Term war effektiv:

```text
is(X, is)
```

statt:

```text
is(X, +(1,3))
```

## Korrektur

`d64_dism.py` kennt nun:

```text
IMAGE_REL_AMD64_REL32
IMAGE_REL_AMD64_REL32_1
IMAGE_REL_AMD64_REL32_2
IMAGE_REL_AMD64_REL32_3
IMAGE_REL_AMD64_REL32_4
IMAGE_REL_AMD64_REL32_5
```

`_x64_append_rm()` erhält die Anzahl der Bytes, die nach dem disp32 noch zur
Instruktion gehören. Der COFF64-Linker berücksichtigt den entsprechenden
REL32_N-Offset ebenfalls.

Damit verwenden u. a.:

```text
ADD/CMP/SUB/... [symbol], imm32 -> REL32_4
MOV [symbol], imm32             -> REL32_4
MOV word [symbol], imm16        -> REL32_2
MOV byte [symbol], imm8         -> REL32_1
SHL/SHR/SAR [symbol], imm8      -> REL32_1
```

die korrekte RIP-Basis.

## Native Verifikation

Der erzeugte PE32+-Maschinencode wurde in einem isolierten x86-64-Testprozess
an seiner bevorzugten PE-ImageBase gemappt. Ohne Win32-Aufrufe wurden die
internen Runtime-Funktionen direkt ausgeführt.

Für beide Eingaben:

```prolog
?- X is 1 + 3.
?- (X is 1 + 3).
```

entstand jetzt:

```text
is/2
  arg0 = X
  arg1 = +(1,3)
```

und `__rt_eval_arith` lieferte:

```text
success = 1
value   = 4
```

PE32 verwendet absolute `DIR32`-Adressierung und war von diesem speziellen
RIP-relative-REL32_N-Fehler nicht betroffen.
