# Stage 393 – C64 Hex-Viewer: Build-Refresh und JSON-PETSCII-Mapping

**Verbindliche Ausgangsbasis:** `d64_dism_asm_392(1).zip` (Benutzerupload).  
**Änderungen:** `d64_dism.py`, `d64_dism.spec`, neue `C64Pro.petscii.json`, neuer Regressionstest.

## Hex-Refresh nach erfolgreicher Programm-Erstellung

Nach erfolgreicher Assemblierung durch `assemble_document()` (C64-Assemblerquellen) oder `assemble_generated_document()` (erzeugte ASM-Tabs von BASIC, Pascal, C, ...):

1. Die erzeugte Datei ist vollständig geschrieben.
2. `_refresh_assembled_hex_view(document, output_path)` liest die **finale Datei** vom Datenträger.
3. `DocumentEditor.show_assembled_hex_bytes(...)` aktualisiert den Hex-Viewer und aktiviert den Hex-Tab.
4. Die Bytes bleiben im Hex-Viewer mit **8 Bytes/Zeile**, zwei Vierergruppen und PETSCII-Spalte sichtbar.
5. Bei C64-`.prg` bleiben beide Headerbytes (little-endian Ladeadresse) sichtbar; die Adressspalte zeigt **Dateioffsets**, nicht CPU-Laufzeitadressen.
6. Bei Quelltextänderungen kehrt der Hex-Viewer zur Quelltextdarstellung zurück. Bei erneutem Build werden die neuen Ausgabebytes neu eingelesen.

Der Build-Schnappschuss ist nur lesbar (Navigation/Kopieren möglich). Die bestehenden Hex-Editor-Funktionen für echte Binärdokumente bleiben editierbar. Die Byte-Ansicht und der Quelltext-Speicherpfad bleiben getrennt, damit durch Ctrl+S **kein erzeugtes PRG** versehentlich als Quelltext gespeichert wird. Auch das Reassemblieren eines bestehenden PRG-Dokuments ist berücksichtigt.

## PETSCII / C64Pro.ttf

- `C64Pro.petscii.json` enthält alle **256** PETSCII-Bytes (`0x00`–`0xFF`) und den jeweiligen Unicode-Codepoint (`U+XXXX`).
- Die Datei enthält bewusst zunächst die bisherige interne Stage-392-Zuordnung – **keine stillen Glyphenänderungen**.
- Ladepunkt: `load_c64_petscii_unicode_map()` in `d64_dism.py`.
- Der Hex-Viewer zeichnet die rechte Zeichenspalte mit dem **bereits vorhandenen C64Pro.ttf-Font**. `C64Pro.ttf` ist ein lokal bereitzustellender Font; er wird diesem Archiv nicht beigefügt.
- JSON editieren → IDE **neu starten**, damit die Zuordnung einmalig neu eingelesen wird.
- Bei fehlerhafter/fehlender/unvollständiger Map wird die bestehende interne Tabelle weiterverwendet. Eine Meldung erscheint auf stdout.
- Im normalen Python-Start wird die JSON-Datei neben `d64_dism.py` gesucht. Für PyInstaller wird sie neben dem erzeugten `d64_dism.exe` kopiert (`d64_dism.spec`).
- Vorsicht: Manche PETSCII-Control-Zuordnungen sind absichtlich Unicode-Steuerzeichen (z. B. CR/LF), sodass die tatsächliche Glyphenanzeige vom Font abhängt. Für andere Unicode-Codepoints die JSON-Datei entsprechend der C64Pro.ttf-Version anpassen.

## Test

```cmd
py -m py_compile d64_dism.py
py -m unittest -v test_stage393_hex_refresh.py
```

Getestet wurden die Vollständigkeit/Kompatibilität der 256 Mappingeinträge, benutzerdefinierte und defekte JSON-Dateien, finale Datei-Bytes, sicherer Build-Schnappschuss, mehrfaches Build/PRG-Eingabeschutz, Readonly-Mutatoren und Integration in beide Assemble-Pfade.

Ein vollständiger interaktiver Windows-/PyQt5-Test war hier nicht möglich (PyQt5 in der Testumgebung nicht installiert). Zusätzlich empfohlen: C64-BASIC → Kompilieren → ASM-Tab → Assemble → Hex-Tab, danach Quelltextänderung und Rebuild; separat eine `.asm`-Datei assemblieren und die PRG-Kopfbytes vergleichen.
