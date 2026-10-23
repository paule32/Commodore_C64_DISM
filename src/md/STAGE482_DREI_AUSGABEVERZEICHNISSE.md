# Stage 482 – Drei Ausgabeverzeichnisse im Windows-Compiler

**Verbindliche Basis:** `d64_dism_asm_481.zip`.

Unter **Projekt-Einstellungen → Windows → 32/64-Bit → Compiler → Ausgabe-Verzeichnis** werden pro Architektur wieder drei getrennte, untereinander angeordnete Felder angezeigt:

1. **Assembler-Zwischenspeicherung**: `QLabel` + `QLineEdit` + `QPushButton("...")` für `.asm`; `.extern.inc` und `.payload.inc` bleiben neben der ASM-Datei.
2. **ausführbare Datei**: eigenes Label, Eingabefeld und Verzeichnisauswahl für gelinkte `.exe`/`.dll`.
3. **32-Bit *.pui und *.o Dateien** bzw. **64-Bit *.pui und *.o Dateien**: eigenes Label, Eingabefeld und Verzeichnisauswahl für Pascal-Unit-Interfaces `.pui` sowie interne `.o`/`.obj` (auch `.coff32.o`/`.coff64.o`).

Alle drei Auswahlbuttons verwenden `QFileDialog.getExistingDirectory()` und tragen den gewählten Pfad in das jeweilige Feld ein. Das Umschalten der gemeinsamen Checkbox **relative Pfade** wirkt auch auf das dritte Eingabefeld. Relative Buildpfade werden, entsprechend Stage 479, auf das Verzeichnis der Quelldatei bezogen.

## Projektspeicherung

Die dritte Einstellung liegt architekturgetrennt in den Projektdaten:

- `__windows_pe32_pascal_unit_output__`
- `__windows_pe64_pascal_unit_output__`

Im zugehörigen `Compiler → Ausgabe-Verzeichnis`-INI-Abschnitt wird sie als `PascalUnitOutput` gespeichert. Die vorhandenen Felder `Path` (EXE), `AssemblerCache` (ASM) und `RelativePaths` bleiben unverändert. Das Laden älterer Projektdateien ohne `PascalUnitOutput` führt zu einem leeren dritten Feld; in diesem Fall bleibt die bisherige Objekt-/PUI-Ausgabe erhalten.

## Build-Zielauflösung

- ASM-Zwischendateien: konfiguriertes Cache-Verzeichnis.
- Generierte `.o`/`.obj` sowie Pascal `.pui`: drittes Verzeichnis, soweit gesetzt; sonst bisheriger Objektpfad.
- EXE/DLL: zweites Verzeichnis, unverändert.
- Include-Suche und Pascal-Unit-COFF-Begleitobjekte berücksichtigen den neuen Objektpfad.

## Verifikation

- Python-Syntaxprüfung `d64_dism.py` erfolgreich.
- Neun gezielte automatisierte Tests bestanden (`test_stage482_three_compiler_output_directories.py`), einschließlich 32-/64-Bit, relativer/absoluter Objektpfade, GUI-Elementstruktur und Fallback.
- Ein interaktiver Qt5-/Windows-Test ist in der verfügbaren Testumgebung mangels PyQt5 nicht erfolgt.
