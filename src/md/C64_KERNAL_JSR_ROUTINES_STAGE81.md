# Stage 81 – C64 KERNAL JSR-Kommentierung

## Korrektur zu Stage 78/80

Die Clear-Screen-Routine des normalen C64-KERNAL 901227-03 wird über **`JSR $E544`** aufgerufen. Die frühere Zuordnung `$5344` war falsch und wurde entfernt. Im Disassembly wird jetzt z. B. ausgegeben:

```asm
    JSR $E544        ; Bildschirm löschen | $0801: 20 44 E5
```

## Offizielle KERNAL-Jump-Table

Der C64 stellt 39 offizielle KERNAL-Einsprungpunkte im Bereich `$FF81` bis `$FFF3` bereit. Diese Adressen werden in Stage 81 automatisch kommentiert.

| Adresse | Name | Kommentar |
|---:|---|---|
| `$FF81` | `CINT` | Bildschirmeditor und VIC-II initialisieren |
| `$FF84` | `IOINIT` | I/O-Geräte initialisieren |
| `$FF87` | `RAMTAS` | RAM testen/initialisieren und Speichergrenzen setzen |
| `$FF8A` | `RESTOR` | Systemvektoren auf Standardwerte zurücksetzen |
| `$FF8D` | `VECTOR` | Systemvektoren lesen oder setzen |
| `$FF90` | `SETMSG` | KERNAL-Systemmeldungen steuern |
| `$FF93` | `SECOND` | Sekundäradresse nach LISTEN senden |
| `$FF96` | `TKSA` | Sekundäradresse nach TALK senden |
| `$FF99` | `MEMTOP` | Obere Speichergrenze lesen oder setzen |
| `$FF9C` | `MEMBOT` | Untere Speichergrenze lesen oder setzen |
| `$FF9F` | `SCNKEY` | Tastaturmatrix scannen |
| `$FFA2` | `SETTMO` | Timeout-Steuerung setzen |
| `$FFA5` | `ACPTR` | Byte vom seriellen Bus empfangen |
| `$FFA8` | `CIOUT` | Byte auf den seriellen Bus senden |
| `$FFAB` | `UNTLK` | UNTALK auf dem seriellen Bus senden |
| `$FFAE` | `UNLSN` | UNLISTEN auf dem seriellen Bus senden |
| `$FFB1` | `LISTEN` | LISTEN auf dem seriellen Bus senden |
| `$FFB4` | `TALK` | TALK auf dem seriellen Bus senden |
| `$FFB7` | `READST` | I/O-Statusbyte lesen |
| `$FFBA` | `SETLFS` | Logische Datei, Gerät und Sekundäradresse setzen |
| `$FFBD` | `SETNAM` | Dateinamen und Dateinamenlänge setzen |
| `$FFC0` | `OPEN` | Logische Datei öffnen |
| `$FFC3` | `CLOSE` | Logische Datei schließen |
| `$FFC6` | `CHKIN` | Eingabekanal wählen |
| `$FFC9` | `CKOUT` | Ausgabekanal wählen |
| `$FFCC` | `CLRCHN` | I/O-Kanäle auf Standard zurücksetzen |
| `$FFCF` | `CHRIN` | Zeichen vom aktuellen Eingabekanal lesen |
| `$FFD2` | `CHROUT` | Zeichen an den aktuellen Ausgabekanal schreiben |
| `$FFD5` | `LOAD` | Datei laden |
| `$FFD8` | `SAVE` | Speicherbereich in Datei speichern |
| `$FFDB` | `SETTIM` | Systemuhr setzen |
| `$FFDE` | `RDTIM` | Systemuhr lesen |
| `$FFE1` | `STOP` | STOP-Taste prüfen |
| `$FFE4` | `GETIN` | Zeichen aus Eingabepuffer/Kanal holen |
| `$FFE7` | `CLALL` | Alle logischen Dateien/Kanäle zurücksetzen |
| `$FFEA` | `UDTIM` | Systemuhr um einen Tick erhöhen |
| `$FFED` | `SCREEN` | Bildschirmgröße (40×25) zurückgeben |
| `$FFF0` | `PLOT` | Cursorposition lesen oder setzen |
| `$FFF3` | `IOBASE` | Basisadresse des I/O-Bereichs zurückgeben |

## Interne, häufig direkt angesprungene Routine

| Adresse | Name | Kommentar |
|---:|---|---|
| `$E544` | `CLSR` | Bildschirm löschen |

Interne ROM-Adressen sind im Gegensatz zur offiziellen Jump-Table nicht die portable KERNAL-API. Stage 81 führt daher zunächst nur die verifizierte Clear-Screen-Routine `$E544` als interne Zusatzroutine.

## Implementierung

`C64_KERNAL_JSR_ROUTINES` enthält die 39 offiziellen Einsprungpunkte. `C64_INTERNAL_JSR_ROUTINES` enthält ausgewählte interne Routinen. `C64_DISASSEMBLY_CALL_COMMENTS` wird daraus erzeugt und von Disassembler sowie Live-Assemblerhilfe gemeinsam benutzt.

Beispiele:

```asm
    JSR $E544        ; Bildschirm löschen | $0801: 20 44 E5
    JSR $FFD2        ; CHROUT: Zeichen an den aktuellen Ausgabekanal schreiben | ...
    JSR $FFE4        ; GETIN: Zeichen aus Eingabepuffer/Kanal holen | ...
```

## Tests

- KERNAL-Tabelle: 39 Einträge, exakt `$FF81..$FFF3` in 3-Byte-Schritten.
- `$E544` wird als Bildschirm löschen erkannt.
- `$5344` wird nicht mehr als Clear-Screen-Routine erkannt.
- KERNAL-Aufrufe wie `$FFD2`, `$FFE4`, `$FFF0` liefern Beschreibungstexte.
- Vollständige Regression: 774/774 erfolgreich.
