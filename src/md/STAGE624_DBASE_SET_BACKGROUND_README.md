# Stage 624 – SET BACKGROUND TO / Füllung des dBASE-Konsole-Fensters

**Verbindliche Basis:** `d64_dism_stage623.zip`.

## Syntax

```dbase
SET BACKGROUND TO <char>
SET BACKGROUND TO <bg>, <fg>, <char>
```

`<bg>` und `<fg>` sind **numerische DOS/VGA-Farbcodes von 0 bis 15**, `<char>` ist ein **CP437-Zeichencode von 0 bis 255**. In der Kurzform werden die bisher aktiven Hintergrund- und Vordergrundfarben des grünen Ausgabefensters beibehalten.

Alle Parameter werden als numerische dBASE-Ausdrücke behandelt: Literale, Variablen, arithmetische Ausdrücke, Makroersetzungen und Funktionsaufrufe. In Klassenmethoden funktionieren auch numerische `self.Property`-Werte sowie parameterlose Klassenfunktionen.

```dbase
SET BACKGROUND TO 176
SET BACKGROUND TO 1, 14, 177

bg = 2
fg = 15
symbol = 178
SET BACKGROUND TO bg, fg, symbol

#define DOSCHAR 219
SET BACKGROUND TO DOSCHAR

FUNCTION Zeichencode()
    RETURN 176
SET BACKGROUND TO 1, 15, Zeichencode()
```

Klassenbeispiel:

```dbase
CLASS TAppearance OF TObject
    PROPERTY Bg = 1
    PROPERTY Fg = 14
    PROPERTY Zeichen = 176
    PROCEDURE Darstellen()
        SET BACKGROUND TO self.Bg, self.Fg, self.Zeichen
        RETURN
ENDCLASS
```

## Anzeige

* Die Zeichenfläche des vorhandenen grünen Turbo-Vision-Ausgabefensters wird vollständig auf das Zeichenzellenraster passend mit dem CP437-Muster gefüllt. Der Fensterrahmen, der Schatten und die Titelleiste bleiben bestehen.
* `?`/`??` nach `SET BACKGROUND TO` überschreiben die gefüllten Textzellen **ab links oben**, statt erst unter der Füllung zu erscheinen.
* Bei Zoom-/Rasteränderungen wird der Hintergrund samt darüber ausgegebenem Text erneut angeordnet.
* Alternativer Konsolen-/Workstation-Weg: die Konsole wird ebenfalls mit den gleichen numerischen Farben und dem gleichen Zeichen ausgefüllt, soweit der Qt5-Console-Viewport verfügbar ist.
* Ungültige Konstanten werden beim Kompilieren beanstandet. Dynamische Parameter werden zur Aufrufzeit als ganzzahlige Farbcodes/Zeichencodes behandelt; Werte außerhalb des erlaubten Bereichs werden von der Qt-Bridge abgelehnt.

## Kompilierung, DLL und ABI

Neue C-ABI-Funktion `DBaseQtFillBackground(int bg, int fg, int code)` im Qt5-Bridge-Export mit Ordinal **1016**. Die Kurzform übergibt `bg=-1, fg=-1`. Alte DLLs besitzen diesen Export nicht; daher muss `libd64_qt5.dll` zwingend neu erstellt werden.

Unter Windows mit installierter MinGW32-/Qt5-Umgebung:

```bat
build_and_deploy_dbase_debug_stage624.bat
```

Bei abweichendem Ausgabeverzeichnis:

```bat
build_and_deploy_dbase_debug_stage624.bat "T:\mein\Projekt\runtime\dbase\pe32"
```

Danach dBASE-PRG **mit Stage 624 neu kompilieren, assemblieren und linken**. Reines Ersetzen der DLL erweitert eine bereits fertig gelinkte alte EXE nicht um den neuen Befehl.

## Änderungen

- `d64dbase/compiler.py`: neuer AST-Knoten, Parser, Typ-/Werteprüfung, PE32/PE64-Codegenerierung, Imports.
- `d64dbase/derived_class_abi.py`: neue Anweisung in CLASS-Methoden, `self.PROPERTY`, Klassenfunktionen und numerische Ausdrücke.
- `d64dbase/grammar/DBaseLexer.g4`, `DBaseParser.g4`: passende ANTLR-Referenzgrammatik.
- `d64dbase/__init__.py`: öffentlicher AST-Export.
- `d64qt5/d64_turbo_output.hpp`: VGA-Palette, CP437-Tabelle, rasterbasierte Füllung und Textüberlagerung.
- `d64qt5/d64qt5_bridge.cpp`, `.h`, `.def`: neue C-Bridge.
- `tests/test_stage624_set_background.py`: 20 Integrations-/Validierungstests.

## Prüfgrenzen

Die Tests prüfen den realen Python-Compiler (PE32/PE64), die Klassen-Codegenerierung sowie die C++-Integration statisch. Ein nativer Qt5-/MinGW32-DLL-Build und die Sichtprüfung unter Windows bleiben erforderlich.
