# Validierung

Durchgeführt für die Amiga-Implementierung von `System.Graphics`:

1. Python-Syntaxprüfung:

```text
c64pascal/compiler.py
d64_dism.py
amiga500.py
tests/test_pascal_graphics_amiga.py
tests/test_pascal_graphics_amiga_asm.py
```

2. PUI-/ASM-Symbolprüfung:

- 15 Routinen in `System.Graphics.pui`
- zu jeder Routine ein `xdef` und ein Label in `Graphics.amiga.asm`

3. Assemblertest:

- `Graphics.amiga.asm` wurde mit einem kleinen bootfähigen Aufrufer verbunden
- Ergebnis: 12982 Byte Maschinencode
- Ergebnis: 1229 Motorola-68000-Instruktionen
- ADF-Größe: 901120 Byte

4. Erzeugtes Unitmodul:

- `System.Graphics.generated.amiga.asm` wurde mit einer Test-Einsprungmarke
  verbunden und erfolgreich assembliert
- Ergebnis: 12924 Byte Maschinencode
- Ergebnis: 1213 Motorola-68000-Instruktionen

## Lokale ANTLR-Einschränkung

Die im Prüfcontainer installierte Python-Runtime ist
`antlr4-python3-runtime 4.9.3`. Die mitgelieferten Parser wurden für ANTLR
4.13.2 erzeugt und benötigen daher, wie in `c64pascal/README.md` angegeben:

```powershell
py -m pip install antlr4-python3-runtime==4.13.2
```

Die vollständigen Parser-Regressionstests sind für diese Runtime-Version im
Archiv enthalten. Die ASM-, PUI-, Symbol- und Python-Syntaxprüfungen wurden
vollständig ausgeführt.

## Copper-Zebrastreifen-Korrektur

Geprüft wurden:

- Syntax von `c64pascal/compiler.py`, `amiga500.py` und `d64_dism.py`
- Assemblierung von `System.Graphics.amiga.asm` zusammen mit einem Bootprogramm
- Vorhandensein der 15 PUI-Exports
- Copper-Pointer `COP1LC=$00010000`
- Aktivierung von `COPEN` über `DMACON=$8380`
- erneutes Laden aller vier Bitplane-Zeiger in der Copper-Liste

Der vollständige Pascal-Frontend-Test benötigt eine zum generierten Parser
passende `antlr4-python3-runtime`-Version. In der Prüfungsumgebung war 4.9.3
installiert, während die mitgelieferten Parserdateien das neuere Listenformat
für `serializedATN()` verwenden.

## C64-Systemfunktionen und Header-Prototypen

Geprüft wurde, dass die Deklarationen aus `c64.h` nicht als unaufgelöste
externe Symbole ausgegeben werden. `clrscr`, `poke`, `peek`, `lo` und `hi`
werden vor der externen Prototypauflösung als Backend-Builtins behandelt.
Die neuen Regressionstests stehen in `tests/test_c64c_system_headers.py`.

## C64 dynamic array index fix

- Lokale C-Variablen und Parameter in Arrayindizes werden ohne Ausnahme-basierte Konstantenprüfung als dynamische Indizes erkannt.
- Bekannte Konstantenausdrücke werden weiterhin zur Compilezeit ausgewertet und auf Arraygrenzen geprüft.
- Der konkrete Zugriff `GfxFloodXLow[index]`, `GfxFloodXHigh[index]` und `GfxFloodY[index]` ist damit gültig.
- `python -m py_compile` für die geänderten Compilerdateien war erfolgreich.
- Der Speicherzugriff wurde mit einem manuell aufgebauten AST bis zu `_DynamicAccess(expression=index)` geprüft.

- C64 array declaration masking: comments/literals and `return array[index]` are no longer misclassified as declarations.

## C64 HiRes graphics target

- Added `runtime/graphics/c64/graphics_c64.asm` as the shared C/Pascal C64
  hardware target.
- The target assembles at `$C000-$C74C`; bitmap bank `$8000-$BFFF` remains
  reserved.
- Added assembler overlap and runtime-window validation.
- `InitGraphics` clears hidden memory before enabling bitmap display.
- Added stable per-cell colour ownership to prevent coloured 8x8 block
  recolouring.
- Added graphics-linked C program end loop.
- Focused tests: 11 passed.

## C64 HiRes bank-2 relocation

- Relocated the VIC-II graphics bank from `$4000-$7FFF` to `$8000-$BFFF` so
  the complete graphics demo ending at `$61FA` no longer overlaps bitmap RAM.
- Relocated the C64 assembly runtime to `$C000-$CFFF`, below the I/O window.
- Added a regression layout that reproduces the reported `$61FA` program end.


## C64 bitmap below BASIC ROM

The C64 graphics target now clears LORAM during graphics mode so CPU reads at `$A000-$BF3F` access bitmap RAM rather than BASIC ROM. `DoneGraphics` restores the original processor-port value.

- C64 VIC-II Screen-Matrix aus dem Character-ROM-Schatten $9000-$9FFF nach $8C00 verlegt; komplette 1000-Zellen-Löschung korrigiert.

## Direkte C64-Grafikprimitive

Die C64-Implementierung von `DrawLine`, `DrawRect`, `FillRect`, `DrawCircle`,
`FillCircle`, `FloodFill`, `DrawTriangle`, `FillTriangle` und
`DrawTriangleAngles` liegt jetzt vollständig in
`runtime/graphics/c64/graphics_c64.asm`. Der C64-Header und die Pascal-PUI-
Implementierung linken für dieses Ziel nicht mehr automatisch die gemeinsamen
C-Primitive.

Das vollständige C-Beispiel wurde bis zur Endlosschleife emuliert. `FillRect`
zeichnete exakt 5151 Pixel, beide Kreisroutinen stimmten ohne fehlende oder
zusätzliche Pixel mit ihrer Referenz überein, und das gefüllte Dreieck enthielt
keine Scanline-Lücken. Der vollständige Unittest-Lauf bestand mit 94 Tests.

## C64 multicolor primitive rendering

The C64 target was changed from standard HiRes cell ownership to VIC-II
multicolor bitmap palette allocation.

Validated properties:

- `graphics_c64.asm` assembles at `$4000-$5B0F`;
- VIC-II bank 2 remains reserved at `$8000-$BFFF`;
- `$D016 = $18` after `InitGraphics` enables 40-column multicolor bitmap mode;
- screen RAM is `$8C00`, bitmap RAM is `$A000`, colour RAM is `$D800`;
- all 1000 palette, screen and colour-RAM cells are initialized;
- the complete generated C demo executes to `__c_program_end` in the test CPU;
- 1,932,377 MOS-6510 instructions are executed;
- hardware stack returns to `$FF`;
- `GetPixel(165,130)` returns `ColorGreen` (`5`);
- `__gfx_palette_overflow` remains `0`;
- the rendered demo contains solid red, cyan, purple, green, blue, yellow and
  white primitives without the former 8x8 colour-owner blocks.

## C64 Character-Editor

- 255 editierbare Zeichen `$01-$FF`, Zeichen `$00` reserviert
- 8×8-Pixelraster mit Maus- und Tastaturbedienung
- Rohimport mit 2048 oder 2040 Bytes
- Export als Assembler, C und Pascal
- `.chr`/`.charset`-Integration in Dateifilter und Doppelklick
- acht neue Daten- und Integrationstests erfolgreich

## C64 Character output formats and palette editor

- Character editor now contains the right-side `Ausgabe Format` radio group:
  Assembler, Pascal, C and BASIC.
- The button directly below the group saves the charset using the selected
  language and matching file extension.
- BASIC charset export contains `DIM CS(255,7)` and 256 DATA records.
- Added a non-modal C64 palette editor for 16 editable RGB representations.
- Palette raw files contain 48 bytes: 16 RGB triplets.
- Palette export supports Assembler, Pascal, C and BASIC.
- Added `.pal` and `.palette` file routing, menu action, toolbar action and
  `Ctrl+Alt+P`.
- Existing Character-Editor tests: 8 passed.
- New Character-/Palette-Editor tests: 8 passed.
- Python syntax validation passed.

## C64 Text- und Pixelbildschirm-Editoren

- Character-Editor-Ausgabegruppe rechts unter der Vorschau geprueft.
- Oberer Quellcode-Button entfernt.
- Textbildschirm-Roundtrip: 2000 Bytes erfolgreich.
- Kompatibilitaetsimport: 1000 Zeichenbytes mit Standardfarben erfolgreich.
- Pixelbildschirm-Roundtrip: 32000 gepackte Bytes erfolgreich.
- Linie, Rechteck, FillRect, Kreis, FillCircle und FloodFill getestet.
- Assembler-, Pascal-, C- und BASIC-Ausgabe fuer beide Editoren getestet.
- Textbildschirm-Assemblerexport: $2000-$27CF erfolgreich assembliert.
- Pixelbildschirm-Assemblerexport: $2000-$9CFF erfolgreich assembliert.
- Parserunabhaengige Regressionstests: 67 erfolgreich.

## Projekt-Panel und Hilfe-Icons

- `.pro`-Roundtrip mit relativ gespeicherten Pfaden geprüft.
- Alle zwölf geschützten Projektkategorien geprüft.
- Root-Kontextaktionen `Umbenennen` und `Löschen` sind deaktiviert.
- Äußerer rechter Tabbereich enthält `Projekt` vor `Informationen`.
- Bestehende Informationstabs bleiben im Tab `Informationen` erhalten.
- Hilfe-Branches und Hilfe-Blätter verwenden unterschiedliche Icons.
- Character-, Paletten-, Text-Screen- und Pixel-Screen-Regressionstests bleiben erfolgreich.

## Projekt-Kontextaktion Neu, Hilfe-Button und Dark-Mode-Styling

- Standarderweiterungen aller zwölf Projektkategorien geprüft.
- `Unbenannt_<nummer>` überspringt vorhandene Projektknoten und Dateien.
- `Neu` steht vor `Hilfe` im Kontextmenü.
- Spezialeditor-Routen für Character Map, Palette, Char Screen und Pixel Screen geprüft.
- Hilfe-Aktion steht in der Toolbar links vor `Zoom +`.
- Hilfe-Icon wird beim Themewechsel neu erzeugt.
- `QToolButton#project_open_button` besitzt explizite Dark-Mode-Zustände.
- 39 gezielte Projekt-/Editor-Regressionsprüfungen erfolgreich.
- Gesamttests: 81 Tests erfolgreich; 13 Parserimporte wegen lokaler ANTLR-Runtime inkompatibel.

## Editor-, Statusleisten- und F1-Hilfe-Erweiterung

- `Protokoll löschen` wurde in die Dock-Titelleiste verschoben.
- Dock- und Registerkarten-Symbole werden weiß gezeichnet.
- Statusfelder für INS, CAPS, NUM, Dateigröße, Zeile und Spalte wurden ergänzt.
- Das Registerkarten-Kontextmenü enthält Neu, Hilfe, Speichern,
  Speichern unter, Schließen und Umbenennen.
- `Datei -> Neu` besitzt sprach- und werkzeugspezifische Untereinträge.
- F1 ermittelt Cursorwort und Sprache und zeigt vorläufig eine als DEBUG
  markierte CHM-Link-MessageBox.
- 10 neue Quellstrukturtests sowie 39 bestehende Projekt-/Editor-Tests sind
  erfolgreich.

## Editor Compile/Assemble/Start Pipeline

- Ungespeicherte `.c`, `.pas`, `.pp` und ASM-Dokumente werden über den
  Registerkartennamen typisiert.
- Datei -> Neu und Doppelklick verwenden dieselbe Build-Leiste.
- C/Pascal Compile erzeugt nur ASM.
- Der ASM-Tab wird nach Compile sichtbar und enthält Assemble/Start.
- Das Binärprogramm wird erst durch Assemble erzeugt.
- Das Tab-Kontextmenü verwendet das vollständige Datei -> Neu-Untermenü.
- Python-Syntaxprüfung erfolgreich.
- 97 Tests erfolgreich; 13 ANTLR-bedingte Importfehler im Prüfcontainer.

## C64 BASIC Compiler und Projektlisten-Erweiterung

- eigenständiges Frontend `c64basic`
- BASIC → MOS-6510-Assembler → C64-PRG geprüft
- BASIC-Demoprogramm mit 434 Instruktionen assembliert
- PRG-Ladeadresse `$0801`, Einsprung `$080D`
- CLI- und GUI-Kernpfad erzeugen bytegleichen Maschinencode
- neue Dokumente werden als reale Projektdateien angelegt und in `.pro` gespeichert
- Projekt-Kontextmenü auf Hilfe/Hinzufügen/Einträge löschen umgestellt
- Einträge löschen verändert keine Dateien auf dem Datenträger

## C64-BASIC erweiterte Komponenten

- Fließkomma im 5-Byte-CBM-Format: implementiert
- Stringvariablen und Stringarrays: implementiert
- ein- und zweidimensionale Arrays: implementiert
- INPUT und GET: implementiert
- DATA, READ und RESTORE: implementiert
- OPEN/CLOSE/CMD/PRINT#/INPUT#/GET#: implementiert
- 16-Bit-sichere Stringverkettung über Speicherseiten: implementiert
- ursprüngliche und erweiterte BASIC-Tests: 17 erfolgreich
- kombinierte Demo: $0801, Einsprung $080D, Ende $203E
- vollständiger Testlauf: 114 erfolgreich; 13 bekannte ANTLR-Importfehler

