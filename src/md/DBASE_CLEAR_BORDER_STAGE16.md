# dBase Stage 16 – CLEAR SCREEN und SET BORDERCOLOR

## CLEAR SCREEN

`CLEAR SCREEN` löscht ausschließlich den Inhalt des Konsolen-`QPlainTextEdit`.
Das Widget, sein Layout und sein Rahmen bleiben erhalten. Nach dem Löschen wird
die komplette Textfläche mit der zuletzt durch `SET COLOR TO` gewählten
Hintergrundfarbe gefüllt.

Beispiel:

```dbase
SET COLOR TO "W/N"
? "wird gelöscht"
CLEAR SCREEN
? "neuer Inhalt"
```

Bei `W/N` ist `W` die Hintergrundfarbe und `N` die Vordergrundfarbe. Nach
`CLEAR SCREEN` ist deshalb die gesamte Konsolenfläche hellgrau; der Rahmen
bleibt unabhängig davon erhalten.

## SET BORDERCOLOR TO

`SET BORDERCOLOR TO <expr>` ändert nur den 1-Pixel-Rahmen des Konsolen-Editors.
Die Textfläche und die bereits vorhandenen Textinhalte bleiben bestehen.

Gültige Beispiele:

```dbase
SET BORDERCOLOR TO "ActiveBorder"
SET BORDERCOLOR TO RGB(FF,00,00)

C = "WindowFrame"
SET BORDERCOLOR TO C

function getBorder()
    return RGB(00,FF,00)

SET BORDERCOLOR TO getBorder()

#define FRAME "InactiveBorder"
SET BORDERCOLOR TO FRAME
```

Ein nackter Systemfarbname ist ohne vorher definiertes Symbol nicht gültig:

```dbase
SET BORDERCOLOR TO ActiveBorder      // Fehler, wenn keine Variable/Makro
SET BORDERCOLOR TO ActiveBorder()    // Fehler, wenn keine Function
```

Direkte Systemfarben werden als Stringliteral geschrieben:

```dbase
SET BORDERCOLOR TO "ActiveBorder"
```

Die Bridge akzeptiert die bereits vorhandenen Windows-Systemfarbnamen aus
`_app.colorNormal` sowie `#RRGGBB`, das vom `RGB(rr,gg,bb)`-Builtin erzeugt wird.

## Neue Bridge-C-ABI

```cpp
void DBaseQtClearScreen(void);
int  DBaseQtSetBorderColor(const char *name, int length);
```

`DBaseQtClearScreen()` setzt intern den Konsolenhintergrund auf den aktuellen
`SET COLOR TO`-Hintergrund. Die Rahmenfarbe liegt in einem separaten
`g_console_border_color`-Zustand und wird danach unverändert wieder angewendet.

## PE32 / PE32+

PE32 ruft `DBaseQtSetBorderColor` per cdecl auf; PE32+ verwendet die Windows-x64-
ABI mit RCX/RDX und 32 Byte Shadow Space. `DBaseQtClearScreen` hat keine
Argumente und wird in beiden Targets direkt importiert.
