# LOGO-Compiler für d64_dism

Der neue LOGO-Frontend-Compiler übersetzt `.logo` und `.lgo` direkt in nativen
IA-32-Assembler und anschließend über die vorhandene interne Toolchain in eine
Windows-PE32-Anwendung. Python wird zur Laufzeit des kompilierten Programms nicht
benötigt.

## Koordinatensystem

- logische Grafikauflösung: **320 x 200 Pixel**
- Startposition: **X=160, Y=100**
- Startrichtung: **Ost / 0 Grad**
- X wächst nach rechts, Y nach unten
- 90 Grad = Süd, 180 Grad = West, 270 Grad = Nord

## Befehle

| Deutsch / Englisch | Bedeutung |
|---|---|
| `right [winkel]`, `rechts [winkel]` | nach rechts drehen, ohne Winkel 90 Grad |
| `left [winkel]`, `links [winkel]` | nach links drehen, ohne Winkel 90 Grad |
| `up`, `hoch`, `north`, `nord` | absolute Richtung Nord |
| `down`, `runter`, `south` | absolute Richtung Süd |
| `east`, `ost` | absolute Richtung Ost |
| `west` | absolute Richtung West |
| `go n` | n Schritte/Pixel in aktueller Richtung |
| `steps n`, `step n`, `schritte n`, `schritt n` | wie `go n` |

Eine absolute Richtung darf direkt eine Schrittzahl erhalten:

    east 40
    south 20

Ebenso ist die explizite Schreibweise mit `steps` möglich:

    east steps 40
    hoch steps 20
    right steps 30
    left steps 30

Dabei bedeutet `right steps 30` eine Bewegung 30 Pixel nach Osten und
`left steps 30` eine Bewegung 30 Pixel nach Westen. Dagegen bleibt
`right 90` die klassische LOGO-Drehung um 90 Grad.

Auch `go` kann eine Richtung erhalten:

    go east 40
    go north steps 25

Kommentare beginnen mit `;`, `#` oder `//`.

## Console-Modus

In der IDE bei Windows-Anwendungsmodus **Console** auswählen. Das erzeugte
PE32-Programm öffnet eine Windows-Konsole, protokolliert Startposition,
Richtungsänderungen und jede neue Position und wartet am Ende auf ENTER.

Kommandozeile:

    py d64_dism.py --write-pe32 beispiel.logo --windows-mode console

## GUI-Modus

In der IDE **GUI** auswählen. Das erzeugte PE32-Programm öffnet die vorhandene
`d64graphics.dll`-Grafikanwendung. Die logische Zeichenfläche ist 320x200 Pixel.
Der Startpunkt (160,100) wird gesetzt und jede Bewegung als Linie gezeichnet.
Das Programm bleibt aktiv, bis das Grafikfenster geschlossen wird.

Kommandozeile:

    py d64_dism.py --write-pe32 beispiel.logo --windows-mode gui

Unter Windows baut d64_dism bei Bedarf die `d64graphics.dll` automatisch mit
dem ausgewählten Direct2D/Direct3D-Backend.

## COFF32

Nur ein relocierbares Objekt erzeugen:

    py d64_dism.py --write-coff32 beispiel.logo --windows-mode console

Der erste LOGO-Backend-Stand ist bewusst auf **Windows PE32** beschränkt.
