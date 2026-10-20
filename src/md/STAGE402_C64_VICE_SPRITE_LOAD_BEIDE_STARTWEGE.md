# Stage 402 – C64 BASIC LOAD von Sprite-Rohdaten über beide VICE-Startwege

**Ausgangsbasis:** `d64_dism_asm_401.zip` (unveränderte sonstige Stages).

## Hintergrund

Der BASIC-V2-Interpreter in VICE und der Stage-401-BASIC-Compiler rufen beide
bei `LOAD "sprites.spr",8,1` die C64-Laufwerkslogik auf. Eine Windows-Datei im
Projektverzeichnis ist nicht automatisch ein Laufwerksfile. Darüber hinaus
fehlt einer rohen `.spr`-Datei der zweiby­tige PRG-Ladeheader.

## Umsetzung

- Neues Modul `c64_vice_assets.py`: erkennt wörtliche `LOAD "*.spr",8,1`
  oder `LOAD "*.sprite",8,1`, löst Dateien relativ zur BASIC-Datei,
  zum Buildverzeichnis oder aus den referenzierten Projekt-Sprite-Dateien auf.
- Liest 63-/64-Byte-Rohspritedatensätze, richtet sie auf je 64 Bytes aus,
  setzt den Little-Endian-Ladeheader `$3000` (`00 30`) und speichert die
  **umgewandelte Kopie unter dem ursprünglich angeforderten Dateinamen** in
  einem eigenen VICE-Laufwerk-8-Stagingverzeichnis (Tempverzeichnis).
- Bei fehlenden Dateien oder ungültigen Daten erfolgt eine klarere
  Fehlermeldung **vor** dem VICE-Start. Quelldateien werden nicht geändert.
- BASIC-Editor-Kontextmenü: Bei neuen VICE-Prozessen `-fs8` +
  `-devicebackend8 1` + `-busdevice8`, bei einem laufenden Binary Monitor
  Resource Set (`0x52`) für `FSDevice8Dir`/`FileSystemDevice8`.
- BASIC-Compiler-Ausgabe → Start in VICE: dieselbe Vorbereitung und
  Befehlszeilenoptionen zum VICE-Autostart.
- BASIC-Quellcode selbst (`LOAD`) und die KERNAL-Implementierung des
  Stage-401-Compilers bleiben unverändert. Laden erfolgt zur Laufzeit.
- Andere `LOAD`-Varianten, `LOAD SCREEN`, Variablennamen und Assemblerstarts
  bleiben unverändert.

## Grenzen und Anforderungen

- Unterstützt nur **literal** angegebene Sprite-Rohdateien auf Laufwerk 8 mit
  Sekundäradresse 1; dynamische Dateinamen und Dateien in bestehenden `.d64`
  werden nicht automatisch umgeschrieben.
- Eine bereits in VICE eingelegte D64-Diskette kann Vorrang vor dem
  virtuellen Laufwerk haben; in diesem Fall Diskette lösen oder neu starten.
- Sprite-RAM ab `$3000` muss frei sein; Sprite-Pointer 192 ff. und Farbregister
  muss das BASIC-Programm selbst setzen.
- Echte C64-Hardware benötigt die PRG-Datei auf der realen Diskette;
  die automatische Stagingfunktion ist **nur ein VICE-Entwicklungshelfer**.
- Der VICE-Dateisystemzugriff hängt von der VICE-Version und Konfiguration ab;
  ohne laufendes VICE in der Testumgebung nicht Ende-zu-Ende verifiziert.

## Test

`python -m unittest -v test_stage402_c64_vice_sprites.py`

Prüft: Dateierkennung, Kommentare, Rohformat-Padding, Kopie mit Ladeheader,
case-insensitive Hostsuche, ungültige Eingabe, die beiden VICE-Startpfade im
Quelltext und die Wire-Kodierung von Resource Set (VICE Binary Monitor API v2).

Zusätzlich: `test_stage401_c64_basic_load.py` sowie Sprite-/VICE-Regressionstests
und `python -m py_compile d64_dism.py c64_vice_assets.py`.
