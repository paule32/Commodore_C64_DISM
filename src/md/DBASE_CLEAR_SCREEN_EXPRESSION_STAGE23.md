# dBase Stage 23 - CLEAR SCREEN <Ausdruck>

Stage 23 erweitert die bestehende Anweisung `CLEAR SCREEN` additiv.

## Syntax

```dbase
CLEAR SCREEN
CLEAR SCREEN 0xB0
CLEAR SCREEN RGB(255,0,0)
CLEAR SCREEN "#FF0000"
```

Der Ausdruck darf aus einer Konstanten, einem expandierten `#define`-Makro,
einer Variable oder einer dBase-FUNCTION stammen.

## Numerischer Ausdruck

Ein numerischer Ausdruck muss einen ganzzahligen Wert von 0 bis 255 ergeben.
Der Wert wird als CP437-/Terminal-Byte interpretiert. Die Qt5-Bridge besitzt
eine vollständige CP437-Tabelle fuer 0x80..0xFF.

`0xB0` wird damit zu Unicode U+2591 (`░`).

Die Konsole wird mit exakt 80 Spalten x 25 Zeilen gefuellt. Vorder- und
Hintergrundfarbe stammen aus dem zuletzt ausgefuehrten `SET COLOR TO`.

Beispiel fuer dunkelblau/gelb:

```dbase
SET COLOR TO "B/RG+"
CLEAR SCREEN 0xB0
```

## String-/RGB-Ausdruck

Ein Stringausdruck fuer `CLEAR SCREEN` muss exakt `#RRGGBB` enthalten.
`RGB(rr,gg,bb)` ist der bereits vorhandene Compiler-Builtin und liefert genau
einen solchen String.

```dbase
CLEAR SCREEN RGB(255,0,0)
CLEAR SCREEN "#FF0000"
```

In diesem Modus wird kein Zeichenmuster geschrieben. Der Inhalt wird geloescht
und die komplette Konsolenflaeche erhaelt die angegebene Hintergrundfarbe.
`SET COLOR TO` selbst wird dadurch nicht veraendert.

## Neue Qt5-C-ABI

```cpp
int DBaseQtClearScreenChar(double code);
int DBaseQtClearScreenColor(const char *name, int length);
```

`DBaseQtClearScreen(void)` bleibt fuer die alte Syntax ohne Ausdruck erhalten.

## Gueltigkeitspruefung

Konstante numerische Werte ausserhalb 0..255 oder mit Nachkommastellen werden
vom Compiler abgewiesen. Konstante Stringwerte muessen `#RRGGBB` entsprechen.
Dynamische Stringwerte werden zur Laufzeit von der Qt5-Bridge validiert.
