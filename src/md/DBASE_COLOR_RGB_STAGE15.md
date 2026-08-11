# dBase Stage 15 - colorNormal, RGB und SET COLOR TO

## `_app.colorNormal`

Direkte Windows-Systemfarbnamen muessen als Stringliteral geschrieben werden:

```dbase
_app.colorNormal = "ActiveBorder"
```

Ein unquoted Name ist kein Farbname, sondern ein normales dBase-Symbol:

```dbase
C = "ActiveBorder"
_app.colorNormal = C
```

Eine bereits vorher definierte Function ist ebenfalls zulaessig:

```dbase
function getColor()
    return "Window"

_app.colorNormal = getColor()
```

Ebenso kann ein Makro die rechte Seite liefern:

```dbase
#define MY_COLOR "Menu"
_app.colorNormal = MY_COLOR
```

Ohne vorherige Definition sind `ActiveBorder` und `ActiveBorder()` Fehler.

## `RGB(rr,gg,bb)`

`RGB` ist ein Compiler-Builtin und erzeugt einen String `#RRGGBB`. Die Kanaele
muessen konstante Ganzzahlen von 0 bis 255 sein. Genau zwei Hexdigits werden
innerhalb von RGB als Hex interpretiert:

```dbase
C1 = RGB(FF,00,80)        // #FF0080
C2 = RGB(0xFF,$00,080h)  // #FF0080
_app.colorNormal = C1
```

## `SET COLOR TO`

Die neue Textfarbanweisung wirkt auf alle nachfolgenden `?`/`??`-Ausgaben.
Die vom Benutzer gewuenschte Reihenfolge ist:

```text
<Hintergrund>/<Vordergrund>
```

Damit bedeutet:

```dbase
SET COLOR TO "W/N"
```

hellgrauer Hintergrund (`W`) und schwarze Schrift (`N`). Bereits ausgegebener
Text behaelt seine bisherigen Farben, weil die C++-Bridge beim Einfuegen einen
`QTextCharFormat` benutzt.

### Grundcodes

| Farbe | Normal | Hell Vordergrund | Hell Hintergrund |
|---|---|---|---|
| Schwarz/Dunkelgrau | N | N+ | N* |
| Dunkelblau/Blau | B | B+ | B* |
| Gruen/Hellgruen | G | G+ | G* |
| Tuerkis/Hellblau | GB/BG | GB+/BG+ | GB*/BG* |
| Dunkelrot/Rot | R | R+ | R* |
| Purpur/Magenta | RB/BR | RB+/BR+ | RB*/BR* |
| Braun/Gelb | RG/GR | RG+/GR+ | RG*/GR* |
| Hellgrau/Weiss | W | W+ | W* |

## Qt5-C-ABI

Die Bridge exportiert weiterhin `DBaseQtSetColorNormal` und neu:

```cpp
int DBaseQtSetOutputColor(const char *spec, int length);
```

`DBaseQtSetColorNormal` akzeptiert Windows-Systemfarbnamen und die von RGB
erzeugten `#RRGGBB`-Werte. `DBaseQtSetOutputColor` setzt die Farben fuer
zukuenftige Textausgaben.
