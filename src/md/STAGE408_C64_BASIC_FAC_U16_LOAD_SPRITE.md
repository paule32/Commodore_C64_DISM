# Stage 408 – KERNAL LOAD / Sprite-POKE und FAC-Integerkonvertierung

Basis: d64_dism_asm_407.zip

## Reproduzierbare Ursache

Die C64-BASIC-Runtime erzeugte fuer `__basic_fac_to_int` bisher:

```
jsr $B1AA
 tax
 tya
 rts
```

FACINX $B1AA liefert A = Low-Byte, Y = High-Byte (C64 ROM-Disassembly
$B1AA: JSR $B1BF, $B1AD: LDA $64, $B1AF: LDY $65).
Die alte Hilfsroutine machte daraus A=High, X=Low, obwohl ALLE
BASIC-Compiler-Aufrufer A=Low und X=High erwarten.
Dadurch wurde `LOAD "sprites.spr",8,1` mit Geraet 0 und Sekundaeradresse 0
an `SETLFS $FFBA` weitergegeben und ein FILE NOT FOUND (LOAD ERROR 4)
konnte trotz vorhandener Datei auftreten.

Ausserdem akzeptiert FACINX positive Werte nur bis 32767; POKE-Adressen
am VIC-II wie $D015/53269 wurden deshalb mit ILLEGAL QUANTITY abgewiesen.

## Korrektur

```
__basic_fac_to_int:
    jsr $BC9B   ; QINT FAC -> vorzeichenbehafteter 32-bit integer, $62-$65
    lda $65     ; Low-Byte
    ldx $64     ; High-Byte
    rts
```

Die vorhandenen Aufrufstellen fuer LOAD, POKE, SYS, Arrays und Integer
uebernehmen wieder A=Low, X=High.
Der Wechsel auf QINT ermoeglicht bei der Konvertierung auch 16-Bit-
VIC-II-Adressen oberhalb von 32767. Zahlbereichspruefungen pro BASIC-
Befehl sind eine separate Aufgabe und bleiben unveraendert.

## Vorbereitete Sprite-Dateien

`c64_vice_sprite_program()` erkennt 130-Byte-PRG-Images mit dem bereits
vorhandenen Header `00 30` und verarbeitet sie nicht doppelt. Raw 63/64-
Byte-Sprites bleiben unveraendert unterstuetzt. Der eigentliche Sprite-Builder
speichert weiterhin originale rohe `.spr`-Dateien.

## Testbeleg

- test_stage408_fac_uint16_load_poke.py: 6 Tests bestanden.
- 13 zusaetzliche Stage-401- und Stage-403-Tests bestanden.
- 17 Stage-402/404-Sprite-Tests bestanden.
- Das vom Benutzer hochgeladene `Sprite_A(1).bas` wurde erneut uebersetzt
  und als PRG mit der korrigierten Runtime assembliert.

### Nicht durchgefuehrt

Kein interaktiver VICE-Laufzeitversuch unter Windows. Daher bitte neu
kompilieren und assemblieren, bevor aus einem Test auf einen behobenen
C64-Ladevorgang geschlossen wird. Falls `LOAD ERROR 4` weiterhin auftritt,
muss anschliessend die aktive VICE-Laufwerk-8-Zuordnung kontrolliert werden.
