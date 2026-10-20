# Stage 409 – Sprite-LOAD als echtes D64-Diskettenimage

**Verbindliche Basis:** `d64_dism_asm_408.zip`.

## Benutzerwunsch

Wenn der BASIC-Quelltext beispielsweise `50 LOAD "sprites.spr",8,1` verwendet,
legt d64_dism **vor dem Start** ein echtes 1541-D64-Image an und übernimmt
die referenzierte Sprite-Datei unter demselben CBM-Dateinamen. VICE bekommt
diese Diskette auf Laufwerk 8, damit weitere BASIC-Ladevorgänge dieselbe
Diskette lesen können.

## Umsetzung

- `c64_d64_disk.py` erzeugt selbstständig ein reguläres 35-Spur-Image mit
  174.848 Bytes, BAM auf Spur 18/Sektor 0, Commodore-DOS-2A-Verzeichnis ab
  Spur 18/Sektor 1 sowie regulären, verketteten 254-Byte-Dateisektoren.
- Die bestehende Sprite-Vorbereitung konvertiert 63-/64-Byte-Rohsprites in
  ein `PRG` mit `$3000`-Header bzw. übernimmt vorhandene vorbereitete
  Dateien unverändert. **Die Quelldatei wird nie überschrieben.**
- C64-Disketten-Dateinamen werden geprüft (maximal 16 ASCII-Zeichen,
  keine Pfadseparatoren); die D64-Dateieinträge sind geschlossene PRG-Dateien.
- D64-Dateien liegen unter `.d64_dism/vice_disks/` neben dem zuvor
  verwendeten Arbeitsverzeichnis `vice_drive8`. Jede Version bekommt einen
  Hash im Dateinamen. Bereits vorhandene/geänderte Images werden **nicht**
  überschrieben. Bei Änderungen an Sprite/PRG wird ein neues D64 erstellt.
- **BASIC → Compiler → Assembler → VICE:** Das D64 enthält das ausführbare
  PRG als **erste** Datei, dazu `sprites.spr` (ggf. weitere referenzierte
  Dateien). VICE erhält `-8 <disk.d64>` und `-autostart <disk.d64>:<program>`.
  Damit wird von der eingelegten Diskette gestartet, ohne später das D64
  gegen ein Autostart-Hostverzeichnis auszutauschen.
- **BASIC-Editor → VICE:** Beim **neuen** VICE-Start mit Binary Monitor wird
  das D64 mittels `-8 <disk.d64>` eingelegt, danach werden die BASIC-Zeilen
  wie bisher übertragen. Es wird **nicht** `FSDevice8Dir` umgestellt, da die
  bisherige Verzeichniskonfiguration eine eingelegte Diskette abkoppeln würde.
- Bei einem bereits laufenden VICE-Binary-Monitor ohne das passende zuvor
  eingelegte D64 wird der Wechsel transparent abgelehnt: Bitte VICE
  schließen und den BASIC-Transfer erneut aus d64_dism starten. Die
  Binary-Monitor-API-2-Ressourcen zum virtuellen Hostdateisystem sind **kein**
  Disk-Attach-Befehl.
- Wenn keine einschlägige `LOAD "*.spr",8,1`-Referenz existiert, bleibt
  der frühere VICE-Startablauf erhalten.
- Das `vice.ini`-Profil wird weiterhin über die Stage-407-Optionen geladen,
  ohne es zu ändern. Auch originale Sprite-Dateien bleiben unverändert.

## Beispielinhalt der Diskette

```text
0 "DBASE2MANY" D4 2A
6 "SPRITE_A" PRG
1 "SPRITES.SPR" PRG
...
```

Die Sektoranzahlen sind abhängig von den jeweiligen Programmdaten.

### BASIC-V2-Kontrolle

Zum Lesen des Verzeichnisses **im Direktmodus** (nicht innerhalb des
laufenden BASIC-Programms) `LOAD "$",8` und anschließend `LIST` verwenden.
`LOAD "sprites.spr",8,1` soll die Sprite-Daten bei `$3000` ablegen.

## Prüfungen

- 6 neue D64-Tests: Struktur, BAM, Sektorverkettung, letzte Sektorlänge,
  mehrere Verzeichnisse, Dateinamen, Disk-voll-Erkennung, unveränderliche
  Dateiausgaben und VICE-Startwege.
- 38 gezielte Tests (Stage 402, 406, 407, 408, 409): OK.
- 25 zusätzliche Regressionstests (Stage 401, 403, 404, 405): OK.
- Der PyInstaller-Build bindet `c64_d64_disk` als `hiddenimport` ein.
- **Noch kein VICE-Windows-End-to-End-Test** in dieser Umgebung.

## Abgrenzung

Der Trigger ist derzeit die **statisch erkennbare** Form
`LOAD "datei.spr",8,1` (bzw. `.sprite`). Bei variablem Dateinamen oder
einem beliebigen anderen Dateityp ist kein automatischer Import definiert.
Ein außerhalb von d64_dism gestartetes `.prg` kann nicht nachträglich
selbstständig ein Host-D64 erzeugen; dazu muss das D64 vorher bereitstehen.
