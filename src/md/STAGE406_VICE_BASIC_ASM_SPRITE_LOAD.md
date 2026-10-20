# Stage 406 – Sprite-LOAD nach BASIC → generiertem Assembler → VICE

**Verbindliche Ausgangsbasis:** `d64_dism_asm_405.zip`.

## Befund an den vom Benutzer gelieferten Dateien

- `Sprite_A.bas` enthält `50 LOAD "sprites.spr",8,1`.
- `Sprite_A.generated.asm` übergibt den elf Zeichen langen Namen `sprites.spr` an KERNAL `SETNAM` ($FFBD), dann Gerät 8 und Sekundäradresse 1 an `SETLFS` ($FFBA), dann ruft es `LOAD` ($FFD5) auf.
- `Sprite_A.prg` hat Ladeadresse $0801 und einen SYS-2061-Startstub. Der gemeldete Wert 4 ist ein KERNAL-Ladefehler („File not found“), **kein** MOS6510-Assemblerfehler.
- Die eigentliche `sprites.spr` wurde nicht hochgeladen. Deshalb kann weder ihr Vorhandensein am Rechner noch ihre VIC-II-Binärdaten oder die reale VICE-Laufwerkseinstellung bestätigt werden.

## Reproduzierbare Lücke in Stage 405

Die automatische Staging-Funktion von Stage 402 wird beim PRG-Start nur aufgerufen, wenn das aktive Dokument `is_basic_document` ist. Ein separat geöffnetes `*.generated.asm` startet sein PRG ohne die zugehörige Sprite-Datei auf dem virtuellen Laufwerk bereitzustellen.

## Korrektur

1. Beim Start aus einem separat geöffneten, als C64-BASIC-Compilerausgabe gekennzeichneten `*.generated.asm` wird nach einer `.bas`/`.basic`-Quelldatei gesucht.
2. Vorrang hat eine gleichnamige Datei im Ordner der Assemblerdatei oder im Ausgabeordner; alternativ wird der Pfad aus dem `; C64 BASIC Compiler output: ...`-Header herangezogen.
3. Die `LOAD "*.spr",8,1`-Abhängigkeiten werden aus dieser BASIC-Quelle vorbereitet, einschließlich des Headers `$3000` auf dem virtuellen VICE-Laufwerk 8.
4. Bei erfolgreichem Staging wird dessen tatsächlicher Ordner **und die enthaltenen Dateien** im Protokoll ausgegeben: `VICE DRIVE8: virtuelles Sprite-Verzeichnis ...`.
5. Fehlende Sprite-Bilddateien erzeugen vor dem VICE-Start eine Fehlermeldung. Unabhängige `.asm`-Programme, die keine BASIC-Compilerausgabe sind, bleiben unverändert.

Die bereits vorhandene Stage-402-Konfiguration für BASIC-Dokumente bleibt erhalten.

## Einschränkung und nächster Diagnose-Schritt

Ein `.prg`, das durch Windows Explorer oder die VICE-GUI direkt gestartet wird, wird **nicht** durch die d64_dism-Startfunktion geschleust. Dann muss das VICE-Laufwerk 8 manuell so konfiguriert sein, dass es eine Datei `sprites.spr` mit einem 2-Byte-Ladeheader `$3000` bereitstellt. Die rohe Sprite-Builder-Datei ist hierfür ohne Konvertierung ungeeignet.

Wenn trotz VICE-Start über die IDE KERNAL Fehler 4 auftritt, bitte VICE-Version, vollständige Protokollmeldung `VICE START`/`VICE DRIVE8`, tatsächliche Laufwerk-8-Konfiguration und `sprites.spr` beilegen. Ein Echtlauf mit VICE war hier nicht möglich.

## Tests

`python -m unittest -q test_stage406_generated_basic_sprite_drive.py test_stage403_vice_load_error4.py test_stage402_c64_vice_sprites.py test_stage401_c64_basic_load.py test_stage404_sprite_native_storage.py`

37 Tests meldeten `OK` (anschließend beendete ein Laufzeitlimit die Testumgebung). Python-Syntax für die beiden geänderten Module bestanden. Kein bestätigter echter VICE-Ladevorgang.
