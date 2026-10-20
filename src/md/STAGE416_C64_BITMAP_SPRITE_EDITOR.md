# Stage 416 – C64 Bitmap Sprite Editor

**Verbindliche Basis:** Stage 415 (`d64_dism_asm_415.zip`).

## Menüintegration

- Projekt/Informationen → `C= 64 Sprites` → Rechtsklick: **Neues Bitmap Sprite** (erster Eintrag), danach `Neues Sprite`.
- Hauptmenü → **Datei → Neu → C= 64 m68k → Bitmap Sprite Editor** unmittelbar über `Sprite Editor`.
- Jeder Editor nutzt ein **eigenes Dock**. Die Hardware-Sprite-Bearbeitung bleibt unverändert.
- Neue Blätter heißen `Bitmap_Sprite_1.bmsprite`, `Bitmap_Sprite_2.bmsprite`, ...
- Gespeicherte `.bmsprite` / `.bmspr` erscheinen unter `C= 64 Sprites`; Klick/Doppelklick öffnet den Bitmap-Sprite-Editor. Diese Dateizuordnung wird in `Category.c64.sprites` im Projekt gespeichert und beim Wiederöffnen aus der Dateiendung rekonstruiert.

## Bedienung

- Frei einfärbbare Pixel: **C64-Farben 0–15** oder **transparent**.
- Linksklick zeichnet mit der selektierten Farbe. Ziehen bei gedrückter Taste malt fortlaufend. Rechtsklick entfernt Pixel (transparent).
- Rastergröße (für die **gesamte Datei**) 1×1 bis 128×128 Pixel, Standard 24×21; Zoom 4–32 Pixel je Rasterzelle.
- Mehrere Bitmap-Sprites innerhalb derselben Datei (bis zu 256), hinzufügen, duplizieren, löschen, leeren und mit Farbe füllen.
- **Neu, Öffnen, Speichern, Speichern unter** und Rückfrage bei ungespeicherten Änderungen.
- Der mit dem Sprite-Builder gemeinsame 16-Farben-Katalog (`C64_CHARACTER_PALETTE`) wird verwendet.

## Dateiformat (binär, keine JSON-Datei)

**Endungen:** `.bmsprite` und `.bmspr`; beide haben dasselbe Format.

| Byteposition | Bedeutung |
|---|---|
| 0–7 | ASCII-Signatur `C64BMSP1` |
| 8–9 | Breite, uint16 Little Endian |
| 10–11 | Höhe, uint16 Little Endian |
| 12–13 | Sprite-Anzahl, uint16 Little Endian |
| ab 14 | Pro Sprite `Breite × Höhe` Pixelbytes, zeilenweise |

Jedes Pixelbyte ist `0..15` (C64-Farbindex) oder `$FF` (transparent). Jeder Datensatz ist exakt `Breite × Höhe` Bytes groß. Der Standardentwurf mit 24×21 Pixeln und einem Sprite benötigt **518 Bytes** (14 Bytes Header + 504 Pixelbytes). Es wird **keine C64-PRG-Ladeadresse** vorangestellt.

**WICHTIG:** Dieses Format ist ein neues, offen dokumentiertes **Software-Bitmap-Sprite-Format**, kein VIC-II-Rohsprite-Format und keine direkt ladbare Commodore-Bitmap. Der Hardware-Sprite-Builder verwendet unverändert `.spr` mit 63/64 Bytes je Sprite. Auf dem echten C64 erlauben HiRes-/Multicolor-Bitmap-Zellen keine uneingeschränkten 16 Farben an beliebigen Pixelpositionen. Eine separate C64-Zeichen-/Blitroutine inklusive Farbkonfliktbehandlung oder passende konvertierte Daten wird für die Darstellung benötigt. **Keine automatische Runtime-Integration in `LOAD SPRITE` oder den VIC-II ist Bestandteil dieser Stage.**

## Technische Änderungen

- `c64_bitmap_sprite.py`: Eigenständiger Binärcodec und Größenvalidierung.
- `c64_bitmap_sprite_editor.py`: QWidget/QPainter-Canvas und vollständige Editor-Bedienung.
- `d64_dism.py`: Menüs, Dock, Projektbaum, Öffnen/Speichern/Dateitypen, Discard-Handling.
- `d64_dism.spec`: neue Module in PyInstaller-Hiddenimports.
- `test_stage416_bitmap_sprite_editor.py`: Format-Roundtrip und strukturelle Tests.

## Teststand

Binärcodec mit allen 16 Farben, mehreren Sprites, transparenter Farbe, Größenänderungen sowie abgewiesenen defekten Dateien getestet; bestehende Projektbaum- und Hardware-Sprite-Tests separat ausgeführt. **PyQt5/VICE-Windows-GUI-Laufzeittest ist hier mangels PyQt5 und VICE nicht möglich.**
