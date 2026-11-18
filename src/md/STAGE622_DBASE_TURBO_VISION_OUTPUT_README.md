# Stage 622 – dBASE-Debug-Ausgabe als grünes Turbo-Vision-Zeichenfenster

**Basis:** `d64_dism_stage621.zip`; zusätzlich geprüft: das vom Benutzer hochgeladene `packed(20261117-143740).zip` sowie der Screenshot des leeren `dBase Qt5 Console / DEBUG`.

## Beobachtung und Ursache

Im Screenshot ist die ursprüngliche **Konsole** mit schwarzem Hintergrund sichtbar, aber keine `hihi`-Zeile. Die gelieferte `App001.exe` ist eine komprimierte PE32-GUI-EXE, die an diesem Linux-Rechner nicht direkt gestartet werden kann. Deshalb lässt sich allein aus dem Screenshot nicht eindeutig nachweisen, ob die lokal geladene Qt5-DLL bereits den Stage-621-Quellstand enthielt. Die DLL-Datei im gepackten Archiv ist UPX-komprimiert und kann nicht zuverlässig auf ihren Quellstand zurückgeführt werden.

In Stage 621 verwendet die aktive dBASE-Compilerkette für `?` und `??` normalerweise `DBaseQtAppendDebug` und blendet per `DBaseQtSetDebugVisible(1)` den Debug-Kanal ein. Dieser führte für normale `.prg`-EXEs bislang in einen **separaten WFM-/Workstation-Debug-QDialog**, während das sichtbare Qt5-Hauptfenster nur die schwarze Konsole anzeigte. Stage 622 ergänzt deshalb einen lokalen Ausgabebereich **im tatsächlich geöffneten Hauptfenster**.

## Implementierung

- Neue Datei `d64qt5/d64_turbo_output.hpp`: `D64TurboOutputWidget`, ein grünes Turbo-Vision-artiges, im schwarzen Konsolen-Viewport eingebettetes Ausgabefenster.
- Textdarstellung: dunkles Grün, hellgrüne Schrift; Doppelrahmen; grüner Titelleistenbereich `Ausgabe`; rechter und unterer Schatten.
- Eigener `QPlainTextEdit` (read-only) mit vertikalem und bei Bedarf horizontalem Scrollbalken, Textselektion und Scrollback.
- Untere Indikatorzeile: Zeile:Spalte und Größe in Zeichen. Rechts unten ein eigener Größen-Anfasser.
- **Größenänderung blockweise in Zeichen**: Mausraster richtet sich nach `QFontMetrics` der aktiven Konsolenfont. Beim Zoom mit den vorhandenen Lupen bleiben die gewünschten Zeichen-Spalten und Zeilen erhalten, die Pixelgröße wird neu berechnet.
- Die bestehende 80×25-Konsole wird nicht gelöscht; das Ausgabefenster erscheint als Kind des Konsolen-Viewports und wird bei `SET DEBUG OFF` ausgeblendet.
- Für normale `.prg`-EXEs ohne Workstation-Modus schreibt `DBaseQtAppendDebug` nun in das grüne Fenster; `DBaseQtSetDebugVisible` blendet es ein/aus.
- Die vorhandenen WFM-/Workstation-/Pipe-Debugpfade und `SET FORMAT TO CONSOLE` bleiben unverändert.

## Windows-Build

Im entpackten Projektroot:

```bat
build_and_deploy_dbase_debug_stage622.bat
```

Optional kann als Argument der vollständige Ausgabepfad angegeben werden. Erwartet werden Qt5/MinGW32, `qmake`, `mingw32-make`, `g++` und Python. Nach erfolgreichem Build liegt `libd64_qt5.dll` im gewählten `runtime\dbase\pe32`-Ordner. Die alte EXE muss vor dem Kopieren **beendet** sein; für die allererste Probe dBASE-Programm neu kompilieren/assemblieren/linken.

```dbase
? "hihi"
?? "Hallo "
? "Welt"
```

Erwarteter Inhalt des **grünen** Fensters:

```text
hihi
Hallo Welt
```

Bei Vergrößerung oder Verkleinerung per Lupen entspricht ein Rasterblock der jeweils aktuellen Breite/Höhe eines Zeichens. Geometriegröße wird als Anzahl von Zeichen (`Spalten x Zeilen`) angezeigt.

## Grenzen / Nachweis

- In dieser Umgebung sind keine Windows-32-Bit-Qt5-/MinGW-Buildwerkzeuge installiert. Die neue DLL kann daher hier **nicht** binär gebaut und der GUI-Lauf nicht bestätigt werden.
- Das hochgeladene gepackte PE32-Beispiel wurde untersucht, aber weder verändert noch ausgeführt.
- C++-Änderung sowie aktive dBASE-Codegenerierung wurden durch Quell-/Regressionstests geprüft. Eine Windows-Sichtprüfung muss nach dem DLL-Neubau erfolgen.
