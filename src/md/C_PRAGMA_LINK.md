# C-Mehrdateien-Linker: `#pragma link`

## Syntax

```c
#pragma link "module.c"
```

Alternativ:

```c
#pragma link("module.c")
```

Der ältere, explizite Name wird ebenfalls akzeptiert:

```c
#pragma d64_link_c "module.c"
```

## Pfadauflösung

Der Modulpfad wird relativ zu der Datei aufgelöst, in der das Pragma steht.
Das Pragma darf deshalb direkt in einem Header stehen:

```c
#ifndef MATH_MODULE_H
#define MATH_MODULE_H

#pragma link "math_module.c"

int AddValues(int left, int right);

#endif
```

Die Implementierungsdatei kann denselben Header inkludieren. Die dadurch
entstehende Selbstreferenz wird erkannt und nicht erneut kompiliert.

## Übersetzungsablauf

```text
main.c
  -> Präprozessor
  -> main.generated.amiga.asm

math_module.c
  -> eigener Präprozessor-/Parserlauf
  -> eigenes C-ASM-Modul

beide ASM-Module
  -> statischer Link
  -> Amiga-ADF oder C64-PRG
```

Die Funktion ist kein Intrinsic. Jeder Funktionskörper wird aus der
referenzierten `.c`-Datei geparst und in ein getrenntes ASM-Modul übersetzt.

## Prototypen

Die aufrufende C-Datei benötigt weiterhin einen Prototyp:

```c
int AddValues(int left, int right);
```

Normalerweise steht dieser im Header, der auch das Pragma enthält.

## Unterstützte Funktionsschnittstelle

Aktuell unterstützt der C-Mehrdateien-Linker:

- `void`, `int`, `char`, `unsigned char`, `bool` und Typedef-Aliase
- 16-Bit-Zeigerwerte als skalare Parameter
- Wertparameter
- skalare Rückgabewerte
- lokale skalare Variablen
- Aufrufe zwischen C-Modulen
- `static`-Funktionen mit modulbezogenen internen Symbolen
- rekursive `#pragma link`-Abhängigkeiten
- Deduplizierung mehrfach eingebundener Module
- Erkennung zyklischer Modulabhängigkeiten
- Prüfung mehrfach definierter öffentlicher C-Symbole

## Aufrufkonvention Amiga

Parameter werden von links nach rechts als 16-Bit-Wörter auf den
Motorola-68000-Stack gelegt. Der letzte Parameter liegt direkt hinter der
Rücksprungadresse. Ein skalarer Rückgabewert liegt in `D0.W`.

## Aufrufkonvention C64

Parameter werden als 16-Bit-Wörter auf den 6510-Hardwarestack gelegt. Der
niederwertige Teil des letzten Parameters liegt direkt hinter der von `JSR`
abgelegten Rücksprungadresse. Ein skalarer Rückgabewert liegt in `A/X`.

## Aktuelle Grenzen

- Parameter und automatische lokale Werte liegen in rekursionsfesten
  Stackframes. Auf dem C64 bleibt die Gesamttiefe durch den 256-Byte-
  Hardwarestack begrenzt.
- Lokale `static`-Variablen liegen absichtlich im Datensegment und behalten
  ihren Wert zwischen Aufrufen.
- Variadische Funktionsdefinitionen werden nicht unterstützt.
- Aggregate werden noch nicht als Parameter oder Rückgabewert übergeben.
- Globale und lokale `static`-Variablen unterstützen konstante ganzzahlige
  Initialwerte.
- Weitere Sprachmerkmale und Grenzen stehen in `C_ADVANCED_FEATURES.md`.

## Zusammen mit ASM-Modulen

Beide Mechanismen dürfen parallel verwendet werden:

```c
#pragma link "algorithms.c"
#pragma d64_link_asm "hardware.amiga.asm"
```
