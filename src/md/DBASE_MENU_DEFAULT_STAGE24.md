# dBase Stage 24: Standardmenü, menuFile-Ausdruck und volle 80×25-Konsole

## Konsolenfläche

Die `QPlainTextEdit`-Konsole zeigt keine horizontalen oder vertikalen Scrollbars mehr. Die explizite Stage-17-Hilfe zum Reservieren einer zusätzlichen Leerzeile wurde entfernt. Das 80×25-Raster steht damit vollständig für Text bzw. `CLEAR SCREEN <Zeichen>` zur Verfügung.

## menuFile

Kanonische Syntax:

```dbase
_app.menuFile = "menu.mnu"
```

Die alte Form `_app.menuFile = <menu.mnu>` ist nicht mehr gültig.

Da eine `.mnu`-Datei beim Kompilieren als dBase-Quellcode eingebunden wird, muss der Ausdruck zur Compile-Zeit als String bestimmbar sein. Unterstützt werden insbesondere:

```dbase
#define MF "menu.mnu"
_app.menuFile = MF
```

```dbase
mf = "menu.mnu"
_app.menuFile = mf
```

```dbase
function getMenu()
    return "menu.mnu"

_app.menuFile = getMenu()
```

Auch konstante Funktionsparameter und String-Verkettung sind möglich.

Ein leerer Wert:

```dbase
_app.menuFile = ""
```

verhält sich wie ein nicht gesetztes `menuFile`.

## Standardmenü

Wenn kein nichtleeres `menuFile` vorhanden ist, ruft der generierte PE32/PE32+-Startcode vor `DBaseQtShowWindow` die C-ABI `DBaseQtEnsureDefaultMenu()` auf.

Die Menüleiste erhält:

1. `=`
2. `Datei`

`Datei` enthält `Neu`, `Speichern`, `Speichern unter...`, `Alle Schließen`, einen Separator und `Beenden`.

`Beenden` schließt das Hauptfenster und beendet die Qt-Ereignisschleife. Das `Datei`-Popup verwendet weiterhin `AsciiPopupMenu`, also den bestehenden Terminal/CP437-Zeichenrahmen und die bisherigen Menüfarben.
