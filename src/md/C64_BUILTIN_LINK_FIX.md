# C64-C: Systemfunktionen vor externen Prototypen

## Fehlerbild

Beim Übersetzen von:

```c
#include <c64.h>

int main(void)
{
    clrscr();
    return 0;
}
```

entstand fälschlich:

```asm
jsr clrscr
```

Der interne Assembler meldete anschließend:

```text
Unbekanntes Symbol: clrscr
```

## Ursache

Die Unterstützung externer C-Prototypen prüfte die aus Headern eingelesene
Deklaration vor den bereits vorhandenen C64-Builtins. Dadurch wurde

```c
void clrscr(void);
```

als Verweis auf ein getrennt zu linkendes Symbol interpretiert. Der Prototyp
soll jedoch nur die C-Signatur bereitstellen. Die Implementierung von
`clrscr()` ist bereits Teil des MOS-6510-Codegenerators.

Dasselbe Problem betraf potentiell:

- `poke`
- `peek`
- `halt`
- `lo`
- `hi`
- `chr`
- `ord`
- `c64_clrscr`
- `c64_poke`
- `c64_peek`

## Korrektur

Der C64-Codegenerator verwendet jetzt diese Reihenfolge:

1. C64-/Runtime-Builtin erkennen und direkt absenken.
2. Erst danach nach einem regulären externen Prototyp suchen.
3. Unbekannte Namen wie bisher als Fehler melden.

`clrscr()` erzeugt wieder:

```asm
lda #$93
jsr $FFD2
```

`poke(address, value)` erzeugt einen indirekten Speicherzugriff, und
`peek(address)` liest den Speicher direkt. Es werden keine externen Symbole
`clrscr`, `poke` oder `peek` benötigt.

## Externe Funktionen bleiben erhalten

Eine normale Deklaration wie:

```c
int AddValues(int left, int right);
```

wird weiterhin als regulärer externer Aufruf erzeugt:

```asm
jsr AddValues
```

und kann über `#pragma link "math_module.c"` bereitgestellt werden.
