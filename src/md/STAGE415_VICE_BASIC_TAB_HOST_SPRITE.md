# Stage 415 – C64 BASIC Debug: Tabulatoren und Sprite-Quelle

Verbindliche Basis: `d64_dism_asm_414.zip`.

## Fehlerbild

Im VICE-BASIC-Debugfenster erscheint:

    Zeichen kann fuer den VICE-BASIC-Debugtransfer nicht als PETSCII kodiert werden: U+0009 ('\t')

U+0009 ist ein Tabulator aus dem BASIC-Editor (u. a. in laengeren REM-Kommentarzeilen).
Der Fehler stammt **nicht** aus der Sprite-Datei und verhindert nicht zwingend eine
vorher schon gelungene Uebertragung von `LOAD SPRITE`.

## Behebung

`d64_dism.py` / `c64_basic_text_to_petscii` ersetzt bei der **VICE-Keyboard-Feed-
Kodierung** jeden Unicode-TAB durch ein PETSCII-Leerzeichen (`$20`). Quelle,
Editor und gespeicherte .bas-Datei werden nicht umgeschrieben. Explizite C64Pro-
Private-Use-PETSCII-Sonderzeichen (`U+E000..U+E0FF`) bleiben unveraendert.
Andere nicht darstellbare Unicode-Zeichen werden weiterhin mit einer konkreten
Meldung abgewiesen. TABs innerhalb eines BASIC-Strings werden nur im direkten
VICE-Debugtransfer zu Leerzeichen; fuer buchstabengetreue Texte ist das zu beachten.

### Ladeweg und Protokoll

* `LOAD SPRITE "sprites.spr"` im BASIC -> VICE Debugtransfer: Windows-Host-Datei
  (aufgeloest relativ zur BASIC-Quelldatei), Binary Remote Monitor schreibt
  Daten in den C64-RAM, standardmaessig ab `$3000`. Das Protokoll meldet:

      VICE LOAD SPRITE: HOST/WINDOWS -> VICE BINARY MONITOR: T:\...\sprites.spr -> $3000 (128 Bytes)

* `LOAD "sprites.spr",8,1`: C64-KERNAL-Ladevorgang auf Laufwerk 8; verwendet das
  eingelegte D64. Beim VICE-Start erscheint ggf. `VICE D64 ATTACH: -8 ...`.
* `LOAD SPRITE` aus BASIC -> Compiler -> Assembler: Sprite-Binardaten werden
  beim Kompilieren in das PRG eingebettet und zur Laufzeit nach `$3000` kopiert.

Dass eine Diskette eingelegt ist, bedeutet fuer den Sonderbefehl `LOAD SPRITE`
**nicht**, dass von der Diskette geladen wurde.

## Tests

    python -m unittest -v test_stage415_vice_basic_tabs_sprite_origin \
      test_stage413_c64_load_sprite_host \
      test_stage414_c64_basic_gui_source_diagnostics \
      test_stage410_c64_load_filename_petscii \
      test_stage412_vice_d64_autostart

31 Tests OK. `python -m py_compile` fuer GUI, Compiler, VICE Assets, D64
und neuen Test OK. Vollstaendiger realer Windows-/VICE-GUI-Lauf ausstehend.
