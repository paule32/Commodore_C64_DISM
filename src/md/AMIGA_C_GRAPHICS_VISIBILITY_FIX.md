# Amiga-C-Grafik bleibt sichtbar

## Ursache

Das bisherige C-Beispiel war nicht semantisch identisch zum funktionierenden
Pascal-Beispiel. Es enthielt am Ende:

```c
DoneGraphics(tmUpperLower);
printf("Graphics demo finished\n");
```

`DoneGraphics()` schaltet absichtlich vom 320x200-Grafikmodus zur
Text-Copper-Liste zurück und löscht dabei die Text-Bitplane. Die zuvor
gezeichneten Primitive sind danach nicht mehr sichtbar. In WinUAE wirkt das
wie ein Reset oder eine sofortige Rückkehr zum Startbildschirm.

## Grafik sichtbar lassen

Im Grafik-Demo darf `DoneGraphics()` nicht aufgerufen werden. Nach `return`
aus `main()` bleibt der Standalone-Startcode in seiner Endlosschleife; der
aktuelle Copper-/Bitplane-Zustand bleibt erhalten.

## Text anzeigen

Textausgaben mit `printf()` werden während des Grafikmodus in die Text-Bitplane
geschrieben, die zu diesem Zeitpunkt nicht angezeigt wird. Für sichtbaren Text
muss zuerst `DoneGraphics()` aufgerufen werden. Dann verschwindet die Grafik
absichtlich.

Dafür existieren jetzt zwei getrennte Beispiele:

- `graphics_demo.c`: Grafik bleibt sichtbar.
- `graphics_demo_text.c`: Grafikmodus verlassen und Ergebnis als Text anzeigen.

Die Farbnamen `ColorBlack` bis `ColorLightGray` sind nun im C-Header identisch
zur Pascal-Unit `System.Graphics` definiert.
