# Stage 625 – `SET BACKGROUND TO` füllt das DOS-Hauptfenster

**Verbindliche Basis:** `d64_dism_stage624.zip`. Diese Korrektur ersetzt das in der Stage-624-Dokumentation beschriebene Ziel der Füllung.

## Gewünschte Ebenen

1. **`g_console` = `QPlainTextEdit`** (`dbaseConsole`): Hintergrundfläche der Hauptkonsole im 80×25-Zeichenraster. Hierhin zeichnet `SET BACKGROUND TO`.
2. **`g_turbo_output` = `D64TurboOutputWidget`**: grünes, verschiebbares / maximierbares Ausgabefenster **über** dem Konsolen-Viewport. Der Befehl verändert dieses Fenster **nicht**.

```dbase
SET BACKGROUND TO 1, 14, 176
? "hihi"
```

Erwartetes Verhalten: Auf der **Hauptfläche hinter dem grünen Ausgabefenster** liegt das CP437-Zeichen 176 (`░`) in VGA-Blau (Hintergrund = 1) und Gelb (Vordergrund = 14). Der `?`-Text `hihi` erscheint weiterhin im separaten grünen Ausgabefenster, ohne dass dessen Hintergrund, Rahmen, Größe oder Position verändert werden. Ein Verschieben des grünen Fensters legt die gemusterte Hauptfläche frei.

Die Kurzform `SET BACKGROUND TO 177` behält die aktiven Farben des Hauptfenster-Hintergrundes bei. Bei wiederholter Verwendung werden die zuletzt mit `SET BACKGROUND TO bg, fg, char` angegebenen Farben übernommen. Die Parameter und Codegenerierung aus Stage 624 bleiben unverändert (PE32/PE64, Variablen, Ausdrücke, Makros, Funktionen, `self`-Properties).

## Technische Änderung

In `d64qt5/d64qt5_bridge.cpp` ruft `DBaseQtFillBackground()` **nicht mehr** `g_turbo_output->fillBackground()` auf. Stattdessen wird die bereits vorhandene Hauptkonsole-Zeichenroutine `render_console_character_pattern()` verwendet, die 80×25 Zellen, Farbformatierung und die DOS-/CP437-Zeichentabelle berücksichtigt. Auch CP437-Grafikzeichen 0–31 und 127 werden nun über dieselbe DOS-Zeichentabelle wie im grünen Fenster umgesetzt.

Die aktiven Musterfarben und der Zeichencode werden im bestehenden `ConsoleClearMode::CharacterPattern` gespeichert und nach einer Zoomänderung durch `restore_console_clear_pattern_after_grid_change()` erneut auf die Hauptkonsole gerendert. Das Remote-Terminal-Template wird entsprechend invalidiert. Die Sichtbarkeit des grünen Fensters wird **nicht** erzwungen, es wird lediglich bei bereits sichtbarem Fenster oben gehalten.

**Hinweis:** Die Füllung wird als Textmuster in `QPlainTextEdit` geschrieben. Explizite direkte Konsolenausgaben (`SET FORMAT TO CONSOLE`) können dessen Dokument verändern; eine unabhängig vom Textinhalt gerenderte Hintergrundebene gehört nicht zu Stage 625. Die normalen `?`-Ausgaben im Turbo-Vision-Fenster verändern das Muster nicht.

## Build / Installation

Windows, MinGW32 / Qt5:

```bat
build_and_deploy_dbase_debug_stage625.bat
```

Optional mit anderem Zielverzeichnis:

```bat
build_and_deploy_dbase_debug_stage625.bat "T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64\runtime\dbase\pe32"
```

Die ABI-Signatur `DBaseQtFillBackground(int bg, int fg, int code)` und die DLL-Export-Ordinalnummer **1016** ändern sich nicht. Für ein bereits mit Stage 624 erzeugtes EXE-Programm ist daher lediglich der **Qt5-DLL-Neubau und -Austausch** erforderlich. Laufende EXEs vor dem Austausch beenden. Falls das Programm noch mit Stage 623 gebaut wurde, muss es dagegen mit Stage 625 neu übersetzt werden.

## Prüfungen

Automatische Tests prüfen Compiler-Syntax und Codegenerierung (PE32/PE64), Bridge-Verkabelung, den 80×25-Rasterpfad, CP437, Farben, Zoom-Hook sowie unveränderte `?`-Ausgabe in das grüne Widget. Ein nativer Qt5-/MinGW-DLL-Build und eine visuelle Windows-Prüfung sind in der aktuellen Umgebung nicht möglich.
