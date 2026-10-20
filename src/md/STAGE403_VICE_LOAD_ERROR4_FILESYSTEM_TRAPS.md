# Stage 403 – VICE LOAD ERROR 4 (Datei nicht gefunden)

**Verbindliche Ausgangsbasis:** `d64_dism_asm_402.zip`.

## Diagnose

`?LOAD ERROR 4` aus dem C64 KERNAL ist „Datei nicht gefunden“. Stage 402
hat zwar das Host-Dateisystem (`-fs8`, `-devicebackend8 1`) konfiguriert,
aber fälschlich `-busdevice8` bzw. `BusDevice8` aktiviert. Das steuert
nicht die für `LOAD` über ein Host-Verzeichnis erforderlichen KERNAL-Traps.

## Korrektur

- Bei VICE-Prozessstart: `-fs8 <Staging-Pfad>`, `-devicebackend8 1`,
  `+drive8truedrive`, `+fs8hidecbm` sowie `-trapdevice8` (VICE 3.10+)
  oder `-virtualdev8` (ältere VICE-Version). Zur Unterscheidung wird die
  Ausgabe von `VICE -help` ausgewertet und das Ergebnis gecacht.
- Bei laufendem VICE über den Binary Monitor: `FSDevice8Dir`,
  `FileSystemDevice8 = 1`, `FSDevice8HideCBMFiles = 0`,
  `Drive8TrueEmulation = 0`, `TrapDevice8 = 1` bzw. Fallback
  `VirtualDevice8 = 1`. Scheitern beide Trap-Ressourcen, wird der Fehler
  dem Benutzer gemeldet, statt stillschweigend eine falsche Bus-Konfiguration
  zu verwenden.
- Beide bisherigen BASIC→VICE-Wege bleiben erhalten. Konvertierung und
  Zwischenspeicherung der `.spr`-Dateien mit Ladeadresse `$3000` unverändert.
- Es werden keine realen Laufwerksdaten oder D64-Images verändert.

## Weiterhin relevante Grenzen

- Ein bereits eingelegtes D64-Diskimage oder manuell geänderte VICE-Optionen
  können Vorrang erhalten. Falls der Fehler bleibt, in VICE im Laufwerk 8
  Verzeichnis statt D64 auswählen und virtuelle Traps aktivieren.
- Bei älteren VICE-Versionen, die keine auswertbare `-help`-Ausgabe liefern,
  wird `-trapdevice8` als Fallback benutzt. Die Option muss bei Bedarf
  in der lokalen VICE-Version geprüft werden.
- VICE steht in der Testumgebung nicht zur Verfügung. Die Tests prüfen
  die Optionen und die Remote-Monitor-Kommandos, nicht den echten
  C64-Ladezugriff.

## Tests

`python -m unittest -v test_stage403_vice_load_error4.py test_stage402_c64_vice_sprites.py test_stage401_c64_basic_load.py`

24 gezielte Tests erfolgreich, Python-Syntax geprüft.
