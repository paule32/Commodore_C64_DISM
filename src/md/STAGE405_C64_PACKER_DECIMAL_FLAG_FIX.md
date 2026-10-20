# Stage 405 – D64PACK: Decimal-Flag im 6510-Entpacker

Verbindliche Ausgangsbasis: `d64_dism_asm_404.zip`.

## Fehlerbild

Wird aus einem C64-BASIC-Quelltext ein MOS6510-PRG erzeugt und der Image-Packer aktiviert,
kann die Ausführung im C64-BASIC-Interpreter mit `?ILLEGAL QUANTITY ERROR IN 10` oder
anderem Fehlverhalten enden. Diese konkrete Meldung wurde nicht in VICE reproduziert;
dafür wurde ein reproduzierbarer Fehler im gepackten Maschinencode nachgewiesen.

## Ursache und Korrektur

Der D64PACK-Bootstrap sicherte zwar mit `PHP` den ursprünglichen Prozessorstatus,
führte danach aber nur `SEI` aus. Der D64PACK-RLE-/LZ-Decruncher verwendet `ADC`,
z. B. um die Anzahl dekodierter Bytes zu bestimmen. Falls der 6510 beim
Aufruf das Decimal-Flag (`D=1`) gesetzt hatte, führte das zu BCD- statt
Binärarithmetik und damit zu falschen entpackten Bytes.

Der Bootstrap führt nun unmittelbar nach `SEI` ein `CLD` aus:

```asm
    php
    pha
    txa
    pha
    tya
    pha
    sei
    cld         ; D64PACK immer binär rechnen lassen
    lda $01
    pha
```

Der ursprüngliche Prozessorstatus wird am Ende weiterhin durch `PLP` restauriert.
Dies betrifft sowohl `RLE` als auch `LZ` und indirekt den Auto-Modus, sofern
Auto einen Packkandidaten auswählt. Die BASIC-Zeile `10 SYS 2061` und die
bestehenden Dateiformate bleiben unverändert.

## Reproduktionsnachweis

Bei einem mit Stage 404 erzeugten BASIC-/LZ-PRG wurden mit dem
6510-Simulationsmodell bei initial `D=1` 446 Bytes des Programms
falsch rekonstruiert. Mit Stage 405 werden alle ursprünglichen Bytes
für RLE und LZ exakt wiederhergestellt, inklusive Spezialfällen mit
BCD-empfindlicher Tokenlänge. Die Simulation prüft zudem Stackpointer,
A/X/Y, Statusregister und `$01`-Port nach dem Entpacken.

Testaufruf:

```
python -m unittest -v test_stage405_packer_decimal.py
```

Vier neue Packer-Tests bestanden. Außerdem bestanden 26 gezielte bestehende
Tests aus Stage 395/401/403/404, insgesamt 30 Tests.

Ein vollständiger Windows-/VICE-Test des gemeldeten BASIC-Laufzeitfehlers
ist noch erforderlich. Die Simulation enthält keine vollständige C64-ROM,
keine Interrupt-Peripherie und keine Laufwerksanbindung.
