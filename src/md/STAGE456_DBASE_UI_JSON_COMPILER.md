# Stage 456 – dBASE FORM: externe UI-Komponenten / JSON

Basis: `d64_dism_asm_455.zip`. Bestehender WFM-Assemblerpfad bleibt der Standard.

## Projekteinstellungen

Unter **Projekt-Einstellungen → Windows → 32-Bit / 64-Bit → Compiler → dBASE → Optimierung** befindet sich die GroupBox **Visuelle Elemente** mit:

- **external UI components** (Standard: aus): Speichert statische FORM-/Widget-Geometrie, Schrift und Properties als ein JSON-Dokument pro Formular anstelle der einzelnen Assembler-Setter. Der Compiler erstellt neben einer vorhandenen `.wfm`-Quelldatei eine lesbare `<name>.ui.json`; das JSON wird *zusätzlich* als Datenblock in das EXE-Image eingebettet. Zur Programmlaufzeit wird daher keine externe `.ui.json` benötigt.
- **compress json** (Standard: aus): nur bei aktivem `external UI components` verfügbar; der JSON-Block wird vor der Assemblierung/Verlinkung mit zlib und einem Qt-kompatiblen 4-Byte-Längenpräfix komprimiert. Die Qt5-Bridge dekomprimiert über `qUncompress` und liest über `QJsonDocument`. Eine kleinere Gesamt-EXE ist wegen PE-Sektionsausrichtung nicht garantiert.

Beide Einstellungen werden getrennt für PE32 und PE32+ gespeichert unter:

`Settings.Windows.32Bit.Compiler.dBASE.Optimierung`

`Settings.Windows.64Bit.Compiler.dBASE.Optimierung`

mit `ExternalUIComponents` und `CompressJson`. Alte Projekte ohne diese Werte bleiben im ursprünglichen Assembler-Modus.

## Compiler / Datenformat

- `d64dbase/wfm_external_ui.py`: Version-1-JSON-Writer, UTF-8 und optionale Qt-kompatible Komprimierung, sidecar `.ui.json` für bestehende `.wfm`-Dateien.
- `d64_dism.py`: WFM-Codegenerator setzt die Grafik-Properties nicht mehr einzeln. Alle Grafik-Handles bleiben in `.bss`, ihre **Adressen** werden in einer kleinen, statischen Tabelle gespeichert; der JSON-Block liegt in `.data`. Nach der Objekterzeugung ruft der Startcode einmal `DBaseQtFormApplyExternalUi` auf.
- Ereigniszuordnung und WFM-Prozeduren bleiben ausführbarer Code; Timer und Nicht-Visual-Komponenten behalten ihre bisherige Erzeugungslogik. Das neue Format kodiert keine Programmlogik in JSON.
- `d64qt5/d64qt5_bridge.cpp` und `.h`: Qt-Reader für die Formular-Properties mit Versions- und Größenprüfungen; `d64qt5_bridge.def` exportiert die **optionale**, nach Namen importierte Funktion `DBaseQtFormApplyExternalUi` mit Ordinal `@1005`.
- `generate_runtime_abi.py` nimmt den neuen optionalen Export von der historischen Ordinal-ABI-Prüfsumme aus. **Der bisherige ABI-Hash bleibt unverändert.**

**Wichtig:** Die auf Windows verwendete `libd64_qt5.dll` muss mit den hier mitgelieferten, geänderten Bridge-Quellen neu erstellt und neben dem generierten Programm bereitgestellt werden, **bevor** der neue JSON-Modus gestartet wird. Ältere Qt5-DLL-Versionen exportieren `DBaseQtFormApplyExternalUi` nicht. Der alte, standardmäßig aktive Assembler-Modus benötigt den neuen Export nicht.

## Prüfungen

Die neuen Tests `test_stage456_wfm_external_ui_json.py` decken Writer, Roundtrip mit und ohne Komprimierung, sidecar-Datei, Einstellungen und vollständiges PE32-/PE32+-Assemblieren/Linken ab. Die umfangreicheren Compiler-/Runtime-Regressionen waren ebenfalls erfolgreich: **125 bestanden, 1 übersprungen** (ausgewählte Stage-441–455-Tests). Ein Windows-Qt5-Laufzeittest und die native Qt-Bridge-Neukompilierung waren in der hier verfügbaren Umgebung nicht möglich.

Das ältere Stage-450-Testmodul prüft ausschließlich die inzwischen durch D64Z abgelöste transparente NTFS-Packvariante und ist für den Stage-455/456-Packer nicht mehr maßgeblich.
