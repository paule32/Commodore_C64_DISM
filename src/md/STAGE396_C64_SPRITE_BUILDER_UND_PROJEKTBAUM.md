# Stage 396 – C64-Sprite-Builder und Projekt-Informationen

Basis: `d64_dism_asm_395.zip`.

## Sprite-Builder

Menü: `Datei → Neu → C= 64 m68k → Sprite Editor`.
Der neue Builder wird im Dock `c64_sprite_builder_dock` geöffnet. Die Palette
besteht aus 16 Farben und lässt sich aus einer `.pal`, `.palette` oder `.bin`
Datei laden. Das Zeichenraster kann von 1 bis 24 (HiRes) oder 1 bis 12
(Multicolor) Spalten und von 1 bis 21 Zeilen eingestellt werden. Die Modi
HiRes, Multicolor und die horizontalen/vertikalen C64-VIC-II-2×-Skalierungsflags
werden unterstützt. Hardware-Sprites bleiben 24×21 HiRes- bzw. 12×21
Multicolor-Pixel groß: Größenänderungen des Zeichenrasters gelten der
Editor-Arbeitsfläche und Darstellung, nicht einem neuen VIC-II-Spriteformat.

`.c64sprite` speichert Palette, Modus, Größe, Skalierung und Spritedaten.
`.spr`, `.sprite`, `.bin` speichern die 63/64-Byte-Hardware-Rohdaten; Zusatz-
informationen sind in diesen Formaten nicht enthalten.

## Projekt-Informationen TreeList

Es wurde ein eigener Hauptknoten `C= 64 Sprites` eingeführt:

```text
Projekt-Informationen
├─ BASIC - Programme
│  └─ Commodore C= 64
│     └─ Ressourcen
│        └─ (... alte Ressourcen bleiben erhalten ...)
├─ Assembler-Programme
├─ (...)
└─ C= 64 Sprites
   ├─ MeinSprite.c64sprite
   ├─ Gegner.spr
   └─ Sprite_1.c64sprite       (ungespeichert)
```

Kontextmenü des Knotens: `Neues Sprite`, `Sprite-Dateien hinzufügen …`,
`Knoten öffnen/schließen`. Bei einem Blatt: `Im Sprite-Builder öffnen`,
`Aus Projekt entfernen`; bei ungespeicherten Blättern zusätzlich
`Speichern unter …`.

Der Menüeintrag `Sprite Editor` legt einen neuen ungespeicherten Entwurf samt
Blatt im Projektbaum an. Nach dem ersten Speichern erhält das Blatt den
Dateinamen und den Pfad; falls dieser Pfad schon als Blatt eingetragen ist,
wird stattdessen das vorhandene Blatt verwendet. Bei `Speichern unter` aus
einem existierenden Dateiblatt bleibt das frühere Blatt bestehen, die neue
Datei wird zusätzlich aufgenommen. Doppeltes Anklicken oder einfaches
Anklicken einer gespeicherten Sprite-Datei öffnet den zugehörigen Builder.

Für `*.pro` wurde der INI-Abschnitt `[Category.c64.sprites]` eingeführt.
Nur gespeicherte Dateipfade werden persistiert; ungespeicherte Entwürfe
werden bewusst nicht als nicht existierende Dateien geschrieben. Ältere
`*.pro` ohne den Abschnitt bleiben kompatibel. Der bisherige Sprite-Typ
im BASIC-Ressourcenzweig bleibt ebenfalls erhalten.

## Validierung

- Python-Quelltext: `py_compile`.
- Isolierte Tests: Codec (HiRes, Multicolor, RAW63/64, Palette, JSON),
  Menü-/Dock-Anbindung, TreeList-Blattstatus, Duplikatschutz,
  INI-Persistenz, Verwerfen und bestehende Stage-393–395-Regressionen.
- Vollständiger GUI-/Docking-Laufzeittest unter Windows mit PyQt5 steht aus.
