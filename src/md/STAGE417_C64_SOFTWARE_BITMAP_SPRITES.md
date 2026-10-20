# Stage 417 – C64 Bitmap-/Software-Sprite-Befehle

Basis: `d64_dism_asm_416.zip` (unverändert in den bestehenden Komponenten; nur additive Änderungen).

## Syntax (BASIC -> Compiler -> MOS6510 Assembler -> PRG -> VICE)

```basic
10 LOAD SPRITE "figuren.spr"
20 SCREEN ON
30 SPRITE SOFTWARE ON
40 SPRITE DRAW 0,100,80
45 SCREEN WAIT
50 SPRITE DRAW 1,140,80
55 SCREEN WAIT
60 SPRITE ERASE 0
65 SCREEN WAIT
70 SCREEN OFF
80 END
```

- `LOAD SPRITE "name.spr"` liest beim Compilieren die Host-Rohdatei (63 oder 64 Bytes je Hardware-Sprite) und unterstützt optional deren PRG-Header. Für die Softwaredarstellung werden 24x21 transparente/weiße Bitmap-Pixel aus den Monochrom-Bits interpretiert. Der bisherige Kopierbefehl nach `$3000` bleibt für diese Dateien bestehen.
- `LOAD SPRITE "name.bmsprite"` / `.bmspr` liest das **native binäre Stage-416-Format**: `0..15` = C64-Farben, `255` = transparent. Die Pixel werden für die Softwaredarstellung **beim Compilieren** ausgewertet; es gibt keinen zusätzlichen `$3000`-RAM-Transfer dieser Datei.
- `SCREEN ON` sichert den bisherigen VIC-Bank-/Modus-/Farbhintergrundzustand und das Farb-RAM, schaltet auf VIC-Bank 1 (`$4000-$7FFF`), Multicolor-Bitmap (`$6000`, 8000 Bytes), Bildschirm-Farbattribute (`$4400`, 1000 Bytes) und Color-RAM (`$D800`, 1000 Bytes) und leert die neue Zeichenfläche.
- `SPRITE SOFTWARE ON` aktiviert die folgenden Software-Sprite-Befehle.
- `SPRITE DRAW N,X,Y`: Zeichnet Sprite `N` (0-basiert) bei `(X,Y)` mit transparenten Pixeln; später gezeichnete Sprites liegen oben. X ist in **physikalischen C64-Bildschirmpixeln** und muss gerade sein (`0..318`); Y ist `0..199`. Ein Quellpixel wird im VIC-II-Multicolor-Bitmapmodus als **zwei horizontale Bildschirmpixel** dargestellt.
- `SPRITE ERASE N`: Entfernt Sprite `N`; die verbliebenen sichtbaren Sprites werden korrekt neu zusammengesetzt, auch bei Überlappungen. Im Hintergrund werden nur die geänderten VIC-II-Bitmap-/Farbbytes aktualisiert.
- `SCREEN WAIT` (zusätzlicher Demonstrationsbefehl): hält die Ausführung im Bitmapmodus bis zu einer Taste über KERNAL GETIN `$FFE4` an. Dadurch können die Zwischenschritte in VICE sichtbar geprüft werden.
- `SPRITE SOFTWARE OFF` deaktiviert weitere Draw/Erase-Anweisungen.
- `SCREEN OFF` stellt die vorherigen VIC-II-Konfigurationsregister und die 1000 Bytes Farb-RAM wieder her. Die alte Textbildschirm-RAM-Seite `$0400` bleibt unberührt.

## Wichtige Grenzen, bewusst nicht versteckt

Der echte VIC-II erlaubt im Multicolor-Bitmapmodus **160×200 logische Pixel** (entsprechend 320×200 physischen Pixeln, aber horizontale Farbpixel sind doppelt breit). Seine 4 Farben pro 8×8-Pixel-Zelle umfassen die globale Hintergrundfarbe (`0` bei SCREEN ON) und höchstens **3 zusätzliche C64-Farben**. Der Compiler bietet alle **16 auswählbaren C64-Farbwerte über das gesamte Bild**, aber **nicht 16 beliebige Farben innerhalb jeder Zelle**. Bei mehr als 3 Nicht-Hintergrundfarben in einer Zelle stoppt der Compiler mit der betreffenden Zellposition, statt Farbwerte stillschweigend zu verfälschen. Transparenz des Editorformats ist `$FF`.

Die erste Runtime ist für **linear ausgeführte Programme mit konstanten Sprite-Indizes und Koordinaten** implementiert. Die Farb-/Bitmap-Differenzen werden beim Compilieren auf Grundlage der Szenenreihenfolge berechnet und als kompakte `LDA/STA`-Maschinencodefolgen erzeugt. `IF`, `GOTO`, `GOSUB`, `RETURN`, `FOR` und `NEXT` in solchen Programmen sind deshalb für Stage 417 ausdrücklich nicht freigegeben (Compilerfehler statt semantisch falschem Ergebnis). Dies ist **noch kein dynamischer 6510-Blitter/Mover für Variablen und Animationsschleifen**.

Die Laufzeit-CBSS und der PRG-Code müssen außerhalb der Bitmapbank 1 liegen; die beigelegten Beispiele liegen deutlich unter `$3000`. Größere Programme können mit den belegten RAM-Bereichen kollidieren: Speicherplanung für beliebig große Programme ist noch nicht implementiert.

**Direkter BASIC-V2-Debugtransfer nach VICE** unterstützt die neuen Bildschirm-/Zeichenbefehle noch nicht. Die GUI gibt ausdrücklich die Aufforderung aus, `Compile -> Assemble -> Start` zu benutzen. Der ursprüngliche direkte Debugpfad `LOAD SPRITE` für reine Hardware-Sprite-Rohdaten bleibt vorhanden.

## Beispielprogramme

In `examples/c64bitmap/`:
- `BitmapSprite_Test_417.bas` plus generierter Assembler und `BitmapSprite_Test_417.prg` mit `figuren.spr` (2 Hardware-Sprites als Software-Bitmap gezeichnet).
- `BitmapSprite_16Farben_417.bas` plus generierter Assembler und `BitmapSprite_16Farben_417.prg` mit `Bitmap_16_Farben_417.bmsprite` (zwei Vollfarb-Bitmap-Sprites; alle 16 Werte verteilt auf mehrere VIC-Zellen).

## Überprüfung

Neue Stage-417-Tests überprüfen Kompilierung/Assemblierung, 63-/64-Byte-Rohsprite-Dekodierung, Laden des Stage-416-Formats, 16-Farben-Szenen, Farbgrenzendiagnose, Sprite-Überlappungen und `ERASE` sowie die Abgrenzung zum direkten BASIC-V2-Startweg. Tests werden als `python -m unittest -v test_stage417_software_sprites` ausgeführt.

Kein echter VICE-Laufzeit-/PyQt5-Integrationstest in dieser Linux-Containerumgebung. Der Anwender muss `SCREEN WAIT` und die Modusumschaltung unter Windows/VICE überprüfen.
