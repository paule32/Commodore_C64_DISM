# Stage 452 – dBASE Runtime DLL / WinError 1 beim Packen

**Verbindliche Basis:** `d64_dism_asm_451.zip`.

## Ursache

Bei aktivierter Checkbox **pack dll** verwendet die IDE transparentes
Windows-Dateisystemkomprimieren via `FSCTL_SET_COMPRESSION`. Für manche
Dateisysteme, Netzlaufwerke oder Windows-Umgebungen schlägt dieser Aufruf mit
**WinError 1 – Unzulässige Funktion** oder **WinError 50 – Nicht unterstützt**
fehl. Stage 451 versuchte `compact.exe` nur bei Zugriffs-/Freigabefehlern 5/32.

## Korrektur

- `d64dbase/pe_dll_pack.py`: Ein WinError **1**, **5**, **32**, **50** oder **87**
  löst nun – unter Windows und bei aktivierter Komprimierung – den zweiten
  Versuch über das mit Windows gelieferte `compact.exe` aus.
- `compact.exe` wird bevorzugt aus `%SystemRoot%\\System32` gesucht, danach
  über `PATH`. Der Exitcode **und** das `FILE_ATTRIBUTE_COMPRESSED` werden
  weiterhin überprüft.
- Scheitern beide Wege, versucht die IDE per `GetVolumePathNameW` und
  `GetVolumeInformationW` den Datenträger, das Dateisystem und die Unterstützung
  für Datei-Komprimierung zu ermitteln und zeigt dann einen konkreten Hinweis:
  **lokales NTFS-Verzeichnis mit Schreibrechten wählen oder `pack dll`
  deaktivieren**.
- **Kein vorgetäuschter Erfolg**: Wird die DLL nicht tatsächlich komprimiert,
  bleibt der Packvorgang fehlgeschlagen. Eine vorhandene Ausgabe-DLL wird
  weiterhin nicht durch einen erfolglosen Packvorgang überschrieben.
- **Keine Veränderung des PE-Inhalts**: Die DLL wird weder mit ZIP/zlib noch
  mit einem nicht ladbaren Containerformat ersetzt. Die SHA-256-Kontrolle
  des unveränderten PE-Inhalts bleibt aktiv.
- Menüeinträge, architekturgetrennte Projekt-Einstellungen, `const pool`, die
  WFM-Optimierungen und alle bisherigen DLL-Exporte bleiben unverändert.

## Prüfung direkt unter Windows

Wird die DLL auf Laufwerk `T:` erzeugt, die tatsächliche Laufwerksart prüfen:

```powershell
Get-Volume -DriveLetter T | Select-Object DriveLetter, FileSystem
fsutil fsinfo volumeinfo T:
```

Für ein temporäres Ausgabeverzeichnis auf einer lokalen NTFS-Partition
(z. B. `C:\\Temp\\dBASE`) kann die bestehende Projektauswahl verwendet werden.
Netzfreigaben, ReFS, exFAT oder andere Laufwerke ohne kompatible
Dateikomprimierung können durch den Compiler nicht in NTFS umgewandelt werden.

**Hinweis:** Die NTFS-Komprimierung ist kein portabler DLL-Packer. Beim
Kopieren auf andere Dateisysteme kann das Komprimierungsattribut entfallen,
während die DLL weiterhin ladbar bleibt.

## Tests

- 12 neue Stage-452-Tests: WinError-1-/50-Fallback, Zugriffsfehler,
  explizite Fehlerdiagnose, PE32-/PE32+-DLL-Neuerzeugung mit simuliertem
  FSCTL-Fehler, Exportprüfung und unveränderte Menü-/Projektanbindung.
- 90 DLL-/Runtime-Tests (Stages 446–452) vollständig bestanden,
  darunter 12 neue Stage-452-Tests.
- 42 dBASE-/Mathematik-Regressionen aus Stage 441–445 bestanden.
- Insgesamt **132 regulär bestandene Tests**.

Die tatsächliche NTFS-Komprimierung kann nur auf einem Windows-System mit
geeignetem Ziellaufwerk geprüft werden. Die Tests simulieren die Windows-Fälle,
führen jedoch keine echten Windows-`FSCTL`-Aufrufe aus.
