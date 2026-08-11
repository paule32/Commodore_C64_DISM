# dBase Stage 13 - `_app`, Klassenobjekte und Qt5 MENU

Diese Stufe erweitert den dBase-Compiler additiv um die erste native Klassen-/Objektschicht.

## Eingebaute Klassenobjekte

- `_app` ist das globale `APPLICATION`-Objekt der gesamten Anwendung.
- `this` ist auf Top-Level ein Alias fuer `_app`.
- `MENU` ist die erste eingebaute GUI-Klasse.
- Objektmember werden in pointergrossen nativen Slots gespeichert (PE32: 32 Bit, PE32+: 64 Bit).

Beispiel:

```dbase
_app.MFENSTER = new MENU(_app)
with (_app.MFENSTER)
    text = "&Fenster"
endwith
```

`new MENU(_app)` erzeugt ein Top-Level-QMenu im Hauptmenuebalken. Ein Kindobjekt

```dbase
_app.MFENSTER.MCASCADE = new MENU(_app.MFENSTER)
```

wird als Menueeintrag unter `MFENSTER` erzeugt.

## WITH / ENDWITH

In dieser Stufe besitzt `MENU` folgende Properties:

- `text = "..."`
- `onClick = class::PROCEDURE_NAME`
- `shortCut = "Ctrl+F4"`
- `separator = true|false`

`class::NAME` muss auf eine bereits im Programm definierte parameterlose `PROCEDURE` zeigen. Der Compiler erzeugt einen echten nativen Funktionszeiger und uebergibt ihn an `d64qt5.dll`.

Ein `{...}`-Codeblock wird syntaktisch bereits als onClick-Wert akzeptiert. Ein leerer bzw. nur kommentierender Codeblock ist in Stage 13 ein sicherer No-Op-Callback; die eigentliche Ausfuehrung beliebiger Codeblock-Inhalte folgt spaeter.

## `_app.menuFile`

```dbase
_app.menuFile = <menus/window.mnu>
```

Die Datei wird beim Kompilieren relativ zur dBase-Quelldatei gelesen und an genau dieser Stelle als Menuequelle eingebunden. Makros des normalen dBase-Praeprozessors koennen auch in `.mnu`-Dateien verwendet werden.

## Qt5 Bridge

Die Bridge exportiert zusaetzlich:

```c
void *DBaseQtMenuCreate(void *owner);
void DBaseQtMenuSetText(void *handle, const char *text, int length);
void DBaseQtMenuSetSeparator(void *handle, int separator);
void DBaseQtMenuSetShortcut(void *handle, const char *text, int length);
void DBaseQtMenuSetOnClick(void *handle, void (*callback)(void));
```

Der interne Codegenerator importiert nur diese C-ABI-Symbole. Qt5-C++-Namensmangling taucht im erzeugten ASM nicht auf.

## Layout

Im Konsolen-Tab der erzeugten Anwendung:

1. QMenuBar (grauer Hintergrund, schwarze Schrift)
2. QPlainTextEdit (schwarzer Hintergrund, graue Schrift)

Menue-Font-Fallback:

1. Consolas
2. Courier New
3. Qt Fixed Font

Die bereits vorhandenen Zoom-Buttons bleiben oberhalb der Tabseiten erhalten.

## PE32 / PE32+

PE32 verwendet cdecl. PE32+ verwendet die Windows-x64-ABI. Objekt-Handles sind pointergross. Callback-Adressen zeigen direkt auf die vom dBase-Codegenerator erzeugten PROCEDURE-Labels.

## Derzeitiger Klassenumfang

Stage 13 implementiert bewusst zuerst das fuer `_app` und `MENU` benoetigte Klassenfundament. Frei deklarierbare benutzerdefinierte `CLASS ...`-Definitionen sind noch nicht Teil dieser Stufe; `class::NAME` bezeichnet hier den Procedure-Namespace des aktuellen dBase-Anwendungsmoduls.
