# Stage 413 – C64 BASIC `LOAD SPRITE` (Windows-Host / VICE Binary Monitor)

Verbindliche Basis: `d64_dism_asm_412.zip`. Alle bisherigen Stage-412-Funktionen bleiben erhalten.

## Zwei voneinander unabhängige Ladewege

* `LOAD "name.spr",8,1`: unveränderter BASIC-V2/KERNAL-LOAD eines **PRG-Eintrags** namens `NAME.SPR` von Diskettenlaufwerk 8. Stage 409–412 erstellen dafür bei lokal vorhandenen `.spr`-Dateien weiterhin ein D64 mit passendem Commodore-Dateinamen. Ein beliebiger lokal existierender `.spr`-Name wie `figur.spr` wird als Disk-Eintrag `FIGUR.SPR` übernommen.
* `LOAD SPRITE "name.spr"`: neue **d64_dism-Erweiterung**, liest die Host-Datei im Verzeichnis der BASIC-Quelldatei und stellt sie ab `$3000` in den C64-RAM. Optional `LOAD SPRITE "name.spr",$3040` (Dezimaladresse ebenfalls erlaubt). Keine Diskette erforderlich.

## BASIC → VICE (direkt, Debug-/Binary-Monitor)

Der vorhandene VICE Binary Monitor (API v2, Memory Set) schreibt die vorbereiteten Bitmapbytes nach `$3000` bzw. zur gewählten Adresse. `LOAD SPRITE` ist kein originales BASIC-V2-Kommando: Beim Programmtransfer wird eine nummerierte Anweisung als `REM LOAD SPRITE HOST` eingetragen. Die Bytes selbst werden über den Monitor übertragen und sind vor `RUN` im C64-RAM. Eine unnummerierte Einzelanweisung überträgt nur die Daten.

Voraussetzung: der Remote/Binary Monitor ist erreichbar oder wird beim BASIC-Transfer von d64_dism gestartet. Eine Sprite-Datei wird nur aus einer lokalen, vorhandenen Datei gelesen. Weder Hintergrundfarbe noch VIC-II-Register werden automatisch geändert.

**Hinweis:** Im direkten BASIC-V2-Interpreter ist die Datenübertragung ein Start-/Transfer-Vorgang; eine spätere erneute Ausführung der als `REM` gespeicherten Zeile lädt die Datei nicht noch einmal vom Windows-Host. Für wiederholte Laufzeit-Disketten-Loads ist `LOAD "name.spr",8,1` zu benutzen.

## BASIC → Compiler → Assembler → PRG → VICE

Der Compiler liest den Host-Sprite beim **Übersetzen** und bettet die Original-Bitmapbytes ins PRG ein. Der generierte MOS6510-Code besitzt eine Kopierroutine `__basic_sprite_copy`, die beim Erreichen der BASIC-Zeile die Bytes an die gewünschte Adresse schreibt. Dadurch kann auch ein standalone PRG ohne laufenden Host-Monitor oder eingelegte D64-Diskette funktionieren. Die Spritedatei muss beim Kompilieren existieren, nicht beim späteren Start in VICE. Änderungen an der `.spr` erfordern erneutes Compilieren und Assemblieren.

Der übliche Pointer für `$3000` in VIC-Bank 0 ist `POKE 2040,192`, für `$3040` entsprechend `POKE 2040,193`. Zusätzlich müssen die entsprechenden `$D000...`-Register gesetzt werden; das Laden allein aktiviert ein Sprite nicht.

### Unterstützte Formate

* Original-Rohdaten: 64 Bytes/Sprite, bei 63 Bytes/Sprite wird ein Null-Ausrichtungsbyte eingefügt.
* Bereits vorbereitete PRG-Daten: 2-Byte-Ladeadresse + 64-Byte-Sprites. Die Adresse muss zur angeforderten Zieladresse passen, der PRG-Header wird bei RAM-Transfer **nicht** kopiert.
* Zieladresse muss durch 64 teilbar sein und der gesamte Block muss in den 64-KiB-Adressraum passen. Bei abweichenden/fehlenden Hostdateien folgt ein Compiler-/Debugfehler statt stiller Ignorierung.

### Wichtige C64-Speicherbedingung

Sprite-Daten brauchen freien RAM im aktuell vom VIC-II verwendeten 16-KiB-Bankfenster. Beim kompilierten Programm darf der Zielbereich nicht mit Programmcode, eingebetteten Daten oder der CBSS kollidieren. Wird eine andere VIC-Bank gewählt, müssen die Sprite-Pointer entsprechend angepasst werden. Die C64-Runtime verwaltet keine automatischen RAM-Reservierungen für diese Adressen.

## Beispiel (Sprite 0 in Textmodus anzeigen)

```basic
10 LOAD SPRITE "sprites.spr"
20 POKE 2040,192
30 POKE 53248,120
40 POKE 53249,100
50 POKE 53264,0
60 POKE 53276,0
70 POKE 53287,1
80 POKE 53269,1
90 END
```

Für Laden vom Disk-Image stattdessen `10 LOAD "sprites.spr",8,1` und den Namen auf dem D64 im CBM-Verzeichnis prüfen. Beide Kommandos unterscheiden sich absichtlich.

## Prüfungen

* Neue Stage-413-Tests für Syntax, Host-Dateiauflösung, 63-/64-Byte-Bitmap, PRG-Header, eingebettete Bytefolgen, alternative Adressen, separates D64-KERNAL-LOAD sowie den Binärmonitor-Pfad.
* Bestehende Stage-410-PETSCII-Tests und Stage-412-D64-Autostart-Tests.
* Py_compile, ZIP-Integrität, Test-PRG assembliert.
* Mangels lokalem Windows/VICE nicht mit dem tatsächlichen Emulator grafisch getestet.
