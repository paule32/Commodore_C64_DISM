# Stage 637 – Turbo-Vision-MessageBox: Verschieben im DOS-Zeichenraster

**Verbindliche Grundlage:** `d64_dism_stage636.zip`.

## Ziel

Die graue, modale MessageBox wird – wie der Turbo-Vision-Editor und das grüne Ausgabefenster – nicht mehr pixelweise verschoben, sondern **in ganzen Zeichen-Spalten und Zeichen-Zeilen**. Dabei bleibt die Titelleiste im 80×25-Viewport erreichbar, während der Fensterkörper rechts und unten hinausragen darf.

## Umsetzung

- Neue gemeinsame Berechnungsfunktionen in `d64qt5/d64_turbo_messagebox.hpp` unter `d64_turbo_message_grid`.
- Zeichenbreite und -höhe kommen aus der **Font des QPlainTextEdit-Konsolenwidgets**; die Consolas-Font der MessageBox beeinflusst die Rasterbewegung nicht.
- Beim Start wird die mittige Ausgangsposition auf das Raster gerundet.
- Beim Ziehen wird die Differenz der Mausposition in ganze Rasterzellen umgerechnet. Zwischen den Zellen gibt es keine Pixelbewegung.
- **Vertikal**: Titelzeile maximal Reihe **24** (0-basiert), sofern der Viewport mindestens 25 Zeichenzeilen anzeigt. Bei kleineren Viewports bleibt die Titelzeile spätestens in dessen letzter sichtbarer Reihe.
- **Horizontal**: der Dialog darf über die rechte Kante hinausreichen; mindestens die ersten **10 Titelspalten** (oder bei sehr schmalem Viewport dessen ganze Breite) bleiben sichtbar. In einem 80-Spalten-Viewport ergibt das eine maximale linke Fensterposition von Spalte **70**.
- Bei einer Zoom- oder Viewportgrößenänderung wird die logische Spalten-/Zeilenposition gespeichert und mit aktualisierten Zellmaßen wiederhergestellt.
- Buttonaktionen, Escape, die graue Darstellung, Consolas-Font, Rahmen, Schatten und die interne Modalität bleiben unverändert.

## Installation

Alle EXE-Prozesse beenden, die die Datei `libd64_qt5.dll` geladen haben. Im entpackten Stage-637-Projekt `build_and_deploy_dbase_editor_stage637.bat` aufrufen und danach die vorhandene dBASE-EXE starten. Für diese reine C++-GUI-Änderung ist kein erneuter dBASE-Compile/Link erforderlich.

## Prüfung

`python -m pytest -q test_stage637.py` prüft die Implementierung. Der C++-Test kompiliert die echten Geometrie-Funktionen mit Stubs für Qt-Geometrietypen und überprüft die Grenzen bei 80×25, Zoom und kleineren Viewports. Die vorhandenen Stage-634- und Stage-635-Tests sind auf die ausdrücklich gewünschte neue Randbehandlung angepasst.

**Grenze:** Die native Qt5-/MinGW32-DLL und das Ziehen mit einer echten Windows-Maus sind in dieser Umgebung noch nicht getestet.
