# Erweiterte C-Sprachmerkmale

Dieses Projekt erweitert das C-Frontend um echte Funktions-Stackframes,
lexikalische Block-Scopes, `static`-Lokale, `typedef`, Strukturen, Enums,
16-Bit-Mengen und einen vollständigen Makro-Präprozessor.

## 1. Automatische lokale Variablen

Normale lokale Variablen liegen im Stackframe der jeweiligen Funktion:

```c
int Factorial(int value)
{
    int partial;

    if (value <= 1)
        return 1;

    partial = Factorial(value - 1);
    return value * partial;
}
```

Jeder Funktionsaufruf besitzt eigene Parameter und eigene automatische
Variablen. Damit sind reguläre Funktionen rekursionsfest.

### Amiga

- `A6` ist der Framepointer.
- Parameter liegen oberhalb der Rücksprungadresse.
- automatische Variablen liegen mit negativen Offsets unterhalb von `A6`.

### C64

- ein eigener Framepointer zeigt in die Hardware-Stackseite `$0100`.
- der vorherige Framepointer wird pro Aufruf auf dem Stack gesichert.
- Parameter und automatische Variablen werden relativ zum aktuellen Frame
  angesprochen.

Der C64-Hardwarestack bleibt naturgemäß auf 256 Byte begrenzt. Tiefe Rekursion
kann daher weiterhin einen Stacküberlauf verursachen.

## 2. Lokale `static`-Variablen

```c
int Counter(void)
{
    static int value = 40;

    value++;
    return value;
}
```

`value` liegt im globalen Datensegment, ist aber nur in seinem Quell-Scope
sichtbar. Der Initialwert wird direkt in die Datendefinition geschrieben und
nicht bei jedem Aufruf neu gesetzt. Der Wert bleibt zwischen Aufrufen erhalten.

Zulässig sind derzeit konstante ganzzahlige Initialisierer. Ohne Initialisierer
wird die Variable mit null angelegt.

## 3. Block-Scopes und Shadowing

```c
int main(void)
{
    int value = 10;

    {
        int value = 20;
        printf("innen=%d\n", value);
    }

    printf("außen=%d\n", value);
    return 0;
}
```

Jeder `{ ... }`-Block erzeugt einen lexikalischen Scope. Gleichnamige Variablen
in inneren Blöcken erhalten getrennte interne Namen und getrennte Stackslots.
Nach Verlassen des Blocks wird wieder der äußere Bezeichner aufgelöst.

## 4. `typedef`

Skalare Aliase:

```c
typedef unsigned int Word;
typedef char Character;
```

Zeiger-Aliase werden als 16-Bit-Adresse behandelt:

```c
typedef unsigned char *BytePointer;
```

## 5. Enums

Benannte und anonyme Enum-Typen werden unterstützt:

```c
typedef enum TColor
{
    colorBlack,
    colorRed,
    colorGreen = 5,
    colorBlue
} TColor;
```

sowie:

```c
enum TState
{
    stateIdle,
    stateRunning,
    stateDone
};

struct TJob
{
    enum TState state;
};
```

Enums werden intern als 16-Bit-Ganzzahltyp behandelt. Nicht explizit gesetzte
Werte erhalten den vorherigen Wert plus eins.

## 6. Mengen / Sets

C besitzt standardmäßig keinen eingebauten Mengentyp. Das Frontend bietet daher
die Erweiterung:

```c
typedef set<TColor> TColorSet;
```

alternativ:

```c
typedef set TColor TColorSet;
```

Eine Menge ist ein 16-Bit-Bitfeld und kann Elemente `0..15` enthalten.
Die normale, getrennt kompilierte Laufzeit wird über `<set.h>` eingebunden:

```c
#include <set.h>

TColorSet colors;

colors = SET_EMPTY();
colors = SET_ADD(colors, colorRed);
colors = SET_ADD(colors, colorBlue);

if (SET_HAS(colors, colorBlue))
{
    /* enthalten */
}
```

Verfügbare Funktionen:

```c
SetEmpty
SetOf
SetAdd
SetRemove
SetUnion
SetIntersection
SetDifference
SetContains
```

`set_runtime.c` wird über `#pragma link` separat kompiliert. Es handelt sich
nicht um Compiler-Intrinsics.

## 7. Strukturen

### `typedef struct`

```c
typedef struct TPoint
{
    int x;
    int y;
} TPoint;
```

Auch eine anonyme Struktur ist möglich:

```c
typedef struct
{
    int width;
    int height;
} TSize;
```

### Getaggte Struktur

```c
struct TCounter
{
    int value;
};

struct TCounter counter;
```

### Verschachtelte Strukturen

```c
typedef struct TPoint
{
    int x;
    int y;
} TPoint;

typedef struct TRect
{
    TPoint topLeft;
    TPoint bottomRight;
} TRect;

TRect rect;
rect.topLeft.x = 10;
```

Strukturen werden im aktuellen Backend in skalare Felder abgesenkt. Rekursiv
eingebettete Strukturen ohne Zeiger werden abgelehnt. Ganzstruktur-Zuweisungen
und Initialisiererlisten sind noch nicht implementiert.

## 8. Makros

Der Präprozessor unterstützt:

- objektartige Makros,
- funktionsartige Makros,
- rekursive Expansion,
- mehrzeilige Definitionen mit `\\`,
- Stringisierung mit `#`,
- Token-Verkettung mit `##`,
- `#undef`,
- `#if`, `#elif`, `#else`, `#endif`,
- `#ifdef`, `#ifndef`,
- `defined(...)`,
- `#pragma once`,
- `__FILE__` und `__LINE__`.

Beispiel:

```c
#define VALUE 4
#define DOUBLE(x) ((x) + (x))
#define MAKE_NAME(a, b) a ## b

#if VALUE == 1
int selected = 1;
#elif VALUE == 4
int selected = DOUBLE(VALUE);
#else
int selected = 0;
#endif
```

## 9. Getrennte C-Dateien

```c
#pragma link "recursive_module.c"
```

Die referenzierte Datei wird als eigene Translation Unit kompiliert. Ihre
öffentlichen Funktionen werden normal über `jsr` beziehungsweise `bsr`
aufgerufen. Jede Translation Unit besitzt eigene interne Labels, statische
Funktionen, statische Variablen und einen eigenen C64-Framepointer.

## 10. Bekannte Grenzen

- C64: Hardwarestack insgesamt 256 Byte.
- Werteparameter und Rückgabewerte sind derzeit skalare 8-/16-Bit-Werte.
- Strukturparameter und Strukturrückgabewerte sind noch nicht implementiert.
- keine Arrays innerhalb von Strukturen.
- keine Union und keine Bitfields.
- keine dynamischen Set-Größen; Sets enthalten höchstens 16 Elemente.
- lokale `typedef`-Deklarationen innerhalb eines Blocks sind noch nicht
  verfügbar.
