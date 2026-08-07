# C64 VIC-II Character-ROM Screen Fix

## Fehlerbild

Der 320x200-HiRes-Modus wurde aktiviert, aber VICE zeigte stabile bunte
8x8-Blöcke statt eines gelöschten Grafikbildschirms. Die CPU löschte die
Screen-Matrix im RAM bei `$9C00`, der VIC-II las dort jedoch nicht dieses RAM.

## Ursache

In VIC-II-Bank 2 (`$8000-$BFFF`) sieht der VIC-II im Bereich
`$9000-$9FFF` stets das Character-ROM. Die bisherige HiRes-Screen-Matrix lag
bei `$9C00-$9FE7` genau in diesem Schattenbereich. Die CPU konnte den RAM dort
beschreiben und wieder lesen, aber der VIC-II verwendete weiterhin die
Character-ROM-Bytes als Farbmatrix. Das erzeugte die bunten Blockmuster.

## Neue Belegung

```text
$8800-$8BE7  Farb-Besitzer der 1000 Zellen, nur CPU
$8C00-$8FE7  HiRes-Screen-/Farbmatrix für den VIC-II
$9000-$9FFF  absichtlich nicht für VIC-II-Grafik benutzt
$A000-$BF3F  8000 Byte HiRes-Bitmap
$C000-...    Grafik-Runtime
```

`$D018` ist jetzt `$38`:

- Bits 7..4 = 3: Screen-Matrix bei Bankbasis + `$0C00` = `$8C00`
- Bit 3 = 1: Bitmap bei Bankbasis + `$2000` = `$A000`

## Zweiter Fehler

Die letzten 232 Bytes von Besitzer- und Screen-Tabelle wurden mit
`LDX #$E7 / DEX / BPL` gelöscht. `$E7` hat bereits das Negative-Flag gesetzt,
deshalb lief die Schleife nur einmal. Die Schleifen zählen nun von `$00` bis
`$E7` aufwärts und initialisieren alle 1000 Zellen.
