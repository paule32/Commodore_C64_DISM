[Deutsch](STAGE519_RESOURCE_EDITOR_PROJECT_SETTINGS_BUILD.md) | [English](STAGE519_RESOURCE_EDITOR_PROJECT_SETTINGS_BUILD.en.md)

# Stage 519 – Projekt-Einstellungen für Ressourcen-DLL-Buttons verbindlich übernehmen

**Basis:** `d64_dism_asm_518.zip` (Stage 518)

## Korrektur

Im Docking-Fenster **Resourcen-Editor** lesen die Buttons **win32 DLL** und
**win64 DLL** die Einstellungen unter **Projekt-Einstellungen → Windows →
32-Bit/64-Bit → Umgebung → Ressourcen** jetzt über **einen gemeinsamen,
architekturspezifischen Live-Abruf** aus. Die Parameter werden unmittelbar vor
dem jeweiligen Build an `build_resource_dll_files()` weitergegeben.

Die Seite unter Windows / 32-Bit wird nur beim **win32 DLL**-Button benutzt.
Die separate Seite Windows / 64-Bit steuert ausschließlich **win64 DLL**.
Ein Wechsel des Zielbuttons ändert weder die Einstellungen der anderen
Architektur noch deren erzeugte Dateien.

### Gelesene Einstellungen

- **ASCII:** „without UTF-16 LE Copy“ oder „with UTF-16 LE Copy“.
- **UTF-8:** „without UTF-16 LE Copy“ oder „with UTF-16 LE Copy“.
- **Unicode:** vorhandene Windows-Standardstruktur (UTF-16LE).
- **Compress DLL / enable:** Komprimierung aktiv oder deaktiviert.
- **Compress DLL / transparent:** Windows-/NTFS-LZX-Komprimierung. Nur auf
  entsprechend unterstütztem Windows-Dateisystem möglich; anderenfalls ein
  eindeutiger Fehler statt eines falschen Erfolgshinweises.
- **Compress DLL / custom:** zlib-komprimierte, dafür geeignete eigene
  Ressourcendaten in der DLL (`D64PK001`), mit dem nativen Decoder aus Stage
  518 lesbar. Windows-Standardressourcen bleiben über Windows-APIs zugänglich.

Änderungen an den Projekteinstellungen wirken auch dann auf den **nächsten**
Build, wenn das Resourcen-Editor-Dock bereits vor dem Öffnen des
Projekteinstellungsfensters existierte. Das UI wird beim Build als aktuelle
Quelle behandelt; der vorhandene Auto-/Manuell-Projektspeicherpfad bleibt
unverändert. Falls kein Projekt-Einstellungen-Dock existiert, werden die
bereits geladenen Projektwerte verwendet.

Auch die vorhandenen manuellen **RC → RES**- und **COFF32/COFF64**-Aktionen
verwenden das gemeinsame Mapping. Sie erzeugen weiterhin einzelne Exportdateien;
die DLL-Kompression gilt für die DLL-Buttons und nicht für `.res`/`.o`.

### Rückmeldung

Nach erfolgreicher DLL-Erstellung erscheint in der Statusleiste neben dem
Zieldateipfad auch das tatsächlich verwendete Mapping sowie der Modus von
`Compress DLL` (`aus`, `transparent` oder `custom`). Für Unicode wird
`Windows-Standard UTF-16LE` anstelle eines missverständlichen Kopie-Status
angezeigt.

### Ausgabeverzeichnisse

Die Architektur-/Codepage-Ausgaben aus Stage 513 bleiben bestehen:
`win32/{ascii,utf8,unicode}` und `win64/{ascii,utf8,unicode}`, jeweils mit
`.res`, `.o` und `.dll`.

### Tests

- 5 neue Stage-519-Tests: Live-Abfrage der beiden Projekteinstellungsseiten,
  geänderte Einstellungen nach Anlegen des Editors, Win32- und Win64-Builds
  mit unterschiedlichen Mapping-/Custom-Kompressionsoptionen, Übergabe des
  transparenten Modus sowie Kompatibilität der separaten Anbieter.
- 115 Regressionstests für Stages 504–515.
- 29 alte Tests für Mapping / Kompression (Stages 516–517) zusammen mit neuen
  5 Tests in einem Lauf (34 vor Ergänzung des fünften Tests).
- 61 Tests einschließlich nativer Decoder- und Formular-/Session-Funktionen.
- 211 Tests insgesamt in separaten Läufen erfolgreich.
- `python -m py_compile d64_dism.py` erfolgreich.

Ein echter PyQt5-Windows-GUI-Test und die tatsächliche `compact.exe`-Ausführung
unter NTFS wurden hier nicht durchgeführt. Der Aufruf mit transparentem Modus
wurde über einen kontrollierten Test des DLL-Button-Handlings validiert.
