# Stage 453 – NTFS-Status der fertigen dBASE-Runtime-DLL prüfen

Basis: `d64_dism_asm_452.zip`.

## Problem

Die Windows-NTFS-Dateikomprimierung (`FSCTL_SET_COMPRESSION` bzw. `compact.exe`)
verändert weder die **logische Dateigröße** einer DLL noch deren MZ-/PE-Bytes.
Die Runtime-DLL aus Stage 452 ist nur 4096 Bytes (PE32) bzw. 4608 Bytes
(PE32+) groß. Daher ist eine sichtbare Platzersparnis auf einem NTFS-Laufwerk
nicht garantiert. Das Explorer-Feld „Größe“ ist **kein** Test des Packstatus.

Bisher prüfte die IDE das Attribut des temporären Builds. Nach dem finalen
`os.replace` fehlte eine erneute Kontrolle; trotzdem wurde Erfolg gemeldet.

## Korrekturen

- `d64dbase/pe_dll_pack.py`: `compression_report` ermittelt das echte
  Komprimierungsattribut und unter Windows die physische Dateibelegung mit
  `GetCompressedFileSizeW`.
- `replace_verified_runtime`: Prüft nach dem endgültigen Einbau den Zustand
  am *finalen Zielpfad*. Ist `pack dll` aktiviert und das Attribut fehlt,
  versucht der Builder erneut direkt am Zielpfad zu komprimieren. Wird es
  dennoch nicht gesetzt, erfolgt ein Fehler und die vorhandene DLL wird
  über eine temporäre Sicherung auf demselben Laufwerk wiederhergestellt.
- `d64dbase/runtime_builder.py`: Verwendet die abgesicherte Übernahme bei
  manuell erzeugten PE32-/PE32+-Runtime-DLLs.
- `d64dbase/console_runtime.py`: Verwendet dieselbe abgesicherte Übernahme
  beim automatischen Deployment neben der Programm-EXE. Ist der Paketpfad
  identisch mit dem Zielpfad, wird die Packeinstellung trotzdem geprüft.
- `d64_dism.py`: Meldet jetzt im Protokoll explizit **„NTFS-komprimiert
  (bestätigt)“**, logische Dateigröße, physisch belegte Bytes und
  Ersparnis. Eine ungepackte Ausgabe wird nicht als gepackt bezeichnet.

Die bestehende Checkbox `pack dll`, `const pool`, die Architekturtrennung,
Projektpersistenz und alle DLL-Exporte bleiben unverändert.

## Prüfung auf Windows

```powershell
$dll = 'C:\Pfad\zur\c64_dbase_runtime.dll'
(Get-Item -LiteralPath $dll).Attributes
((Get-Item -LiteralPath $dll).Attributes -band [System.IO.FileAttributes]::Compressed) -ne 0
compact /q "$dll"
```

Ergibt die boolesche Abfrage `True`, ist das NTFS-Komprimierungsattribut
aktiv. Bei `False` wurde es nicht gesetzt. Eine tatsächliche Reduzierung
von „Größe auf Datenträger“ ist bei so kleinen DLLs selbst dann nicht
gewährleistet.

**Abgrenzung:** Dies ist weiterhin eine transparente **NTFS**-Komprimierung,
kein portabler PE-Unpacker. Für eine auf jedem Dateisystem kleinere und
unmittelbar ladbare DLL wäre eine andere PE-Build-/Packtechnik nötig;
eine normale zlib- oder ZIP-Datei ist für `LoadLibrary` ungeeignet.

## Tests

9 neue Stage-453-Tests: Komprimierung nach finaler Installation erneut
prüfen, erfolgreicher Nachversuch, Rollback bei Misserfolg, normaler Build,
Komprimierungsbericht, echte PE32-/PE32+-DLL-Builds und GUI-Protokoll.
141 Tests aus den Stage-441–453-Runtime-/Compilergruppen und 27 Tests der
früheren Projektverwaltung: jeweils regulär beendet und bestanden.

Eine reale Prüfung von `GetCompressedFileSizeW`/NTFS-Attribut und `LoadLibrary`
bleibt dem Windows-Testsystem vorbehalten.
