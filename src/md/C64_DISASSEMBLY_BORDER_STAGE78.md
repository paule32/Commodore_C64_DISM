# Stage 78 – oberer Rahmenradius, C64-Fuellroutinen und Binary-Disassembly

## 1. Hauptfensterrahmen

Der sichtbare beige Frameless-Rand bleibt 2 px breit. Nur oben links und oben
rechts wird ein Radius von 2 px verwendet. Neben dem gezeichneten QPainterPath
wird die reale Windows-Fenstermaske mit QRegion angepasst, damit die nativen
eckigen Client-Pixel an den beiden oberen Ecken nicht sichtbar bleiben.

Die vorhandene 7-px-WM_NCHITTEST-Zone fuer alle vier Kanten und vier Ecken
bleibt unveraendert.

## 2. C64 Textbildschirm fuellen

C64-Textbildschirm-RAM: `$0400-$07E7`, exakt 1000 Bytes = 40 x 25 Zeichen.
Der Wert im Bildschirm-RAM ist ein **Screen-Code**, nicht zwingend PETSCII.

Das Beispiel `examples/assembler/c64_fill_screen_stage78.asm` enthaelt drei
Routinen:

- `FillLine`: A=Screen-Code, X=Zeile 0..24; fuellt genau 40 Bytes.
- `FillRange`: A=Screen-Code, PTRLO/PTRHI=Start, LENLO/LENHI=Laenge.
- `FillScreen`: A=Screen-Code; fuellt exakt 1000 Bytes `$0400-$07E7`.

`FillScreen` verwendet absichtlich eine 16-Bit-Laenge von 1000 und schreibt
nicht pauschal vier volle 256-Byte-Seiten. Dadurch bleiben `$07E8-$07FF` und
insbesondere die Sprite-Pointer unangetastet.

## 3. PRG/BIN beim Oeffnen automatisch disassemblieren

`ExplorerWindow.open_document()` behandelt nun `.prg` und `.bin` als C64-
Programm-Binaries:

- `.prg`: die ersten zwei Bytes sind die Little-Endian-Ladeadresse.
- `.bin`: rohe Datei, Standard-Ladeadresse `$0801`.
- der originale Binaerpuffer bleibt im Hex-Editor erhalten.
- der Rohdaten-Tab bekommt automatisch ein dokumentierbares 6510-Listing und
  wird direkt fokussiert.
- ein BASIC-SYS-Startstub wird als `.byte` erhalten und der Maschinen-Code ab
  der erkannten SYS-Adresse disassembliert.

## 4. Kommentare automatisch ausrichten

`C64_DISASSEMBLY_COMMENT_GAP = 8`.

Die laengste Anweisung wird zuerst bestimmt. Danach beginnt jede Kommentar-
spalte an `max_instruction_width + 8`. So stehen alle Semikolons exakt in einer
Fluchtlinie.

Die semantische Kommentar-Tabelle ist erweiterbar:

```python
C64_DISASSEMBLY_CALL_COMMENTS = {
    ("JSR", 0x5344): "Bildschirm loeschen",
}
```

Das erzeugte Listing verwendet die Unicode-Ausgabe:

```asm
    JSR $5344        ; Bildschirm löschen
    RTS              ; $0804: 60
```

Die Zieladresse wird aus den echten Opcode-Bytes gelesen. Die Dokumentation
funktioniert deshalb auch dann, wenn der Disassembler ein lokales Label statt
`$5344` darstellen sollte.

## 5. Dokumentiertes Listing speichern

Das Bearbeiten des Rohdaten-ASM veraendert den Hex-Puffer des geoeffneten
PRG/BIN nicht. Wird das Listing bearbeitet und `Ctrl+S` benutzt, erzwingt die
GUI `Speichern unter` und schlaegt `<dateiname>.asm` vor. Das originale Binary
wird damit nicht versehentlich mit Text ueberschrieben.

## Tests

- Stage-78-spezifisch: 7/7
- kompletter Testbestand: 756/756
- C64-Fuellbeispiel wird mit dem integrierten MOS-6510-Assembler assembliert.
- PRG-Ladeadresse, BIN-$0801-Fallback, BASIC-SYS-Stub, Kommentarspalte und
  `$5344`-Dokumentation werden getestet.
