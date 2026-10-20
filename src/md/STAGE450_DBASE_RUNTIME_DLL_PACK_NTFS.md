# Stage 450 – dBASE Runtime: „pack dll“ (Windows/NTFS)

Basis: `d64_dism_asm_449.zip`. Die bestehende `c64_dbase_runtime.dll` und ihre 11 Exporte sowie alle vorhandenen Menüeinträge bleiben erhalten.

## Oberfläche

- Projekt-Einstellungen → Windows → 32-Bit → Umgebung → **Eingabe** → GroupBox **dBASE Runtime**: neue CheckBox **pack dll**.
- Dieselbe CheckBox unabhängig für Windows → 64-Bit (PE32+) im gleichen Pfad.
- Voreinstellung **aus**; Werte werden als `DBaseRuntimeDLLPack=true/false` in der jeweiligen `.pro`-Datei unter `[Settings.Windows.32Bit.Environment]` bzw. `[Settings.Windows.64Bit.Environment]` gespeichert, bei älteren Projekten `false`.
- Bereits vorhandene DLL-Erzeugungsbuttons und die beiden Werkzeuge-Menüeinträge benutzen dieselbe architekturspezifische Einstellung. Ebenso die automatische Bereitstellung neben gelinkten dBASE-/WFM-Programmen.

## Packverfahren und wesentliche Einschränkung

Eine zlib-komprimierte DLL-Datei ist **keine von Windows direkt ladbare PE-DLL**. Der vorhandene allgemeine PE-EXE-Packer ist für DLLs nicht freigegeben. Stage 450 verwendet deshalb bewusst **transparente NTFS-Komprimierung** über Windows `FSCTL_SET_COMPRESSION` (`DeviceIoControl`) – **keinen portablen PE-Codepacker/UPX-Stub**.

Die logischen Datei-Bytes einschließlich PE-Header, Imports, Exports und Maschineninstruktionen bleiben **bitgenau** erhalten. Windows kann das DLL-Image weiterhin ganz normal mittels `LoadLibrary` und des PE-Loaders abbilden. NTFS dekomprimiert Dateiblöcke transparent. Da die aktuelle DLL nur ungefähr 4–5 KB umfasst, ist eine reale Speicherplatzersparnis **nicht garantiert**.

- **Erforderlich:** Windows und ein NTFS-Ziellaufwerk (sowie Schreib-/Komprimierungsberechtigung). Auf Nicht-NTFS-Zielen wird bei aktivem Schalter eine verständliche Fehlermeldung ausgegeben; es erfolgt keine Ausgabe einer defekten DLL.
- **Kopieren/ZIP:** Das NTFS-Komprimierungsattribut wird beim Kopieren auf andere Dateisysteme oder durch ZIP nicht zwangsläufig übernommen. Die DLL bleibt dabei normal ladbar, allerdings eventuell unkomprimiert.
- **PE32/PE32+:** Es werden weiterhin zwei separate Architekturdateien mit demselben DLL-Namen verwendet. Die Auswahleinstellungen sind getrennt.

## Implementierung

- `d64dbase/pe_dll_pack.py`: Nativer Windows-NTFS-Kompressionsschalter, Prüfung `FILE_ATTRIBUTE_COMPRESSED` und Überprüfung des unveränderten SHA-256 der PE-Datei.
- `d64dbase/runtime_builder.py`: Atomarer manueller DLL-Build im temporären Zielverzeichnis, PE-Exportprüfung vor und nach optionaler Komprimierung, anschließendes `os.replace`. Im Fehlerfall bleibt die vorhandene DLL erhalten.
- `d64dbase/console_runtime.py`: Automatische Bereitstellung mit optionaler Komprimierung und geschütztem Austausch, Auswertung des vorhandenen Komprimierungsstatus beim späteren Start.
- `d64_dism.py`: Architekturabhängige Checkbox, GUI-Synchronisierung und `.pro`-Persistenz; Weitergabe `pack_dll` an beide Buildpfade.
- `test_stage450_dbase_runtime_pack.py`: Tests für UI/Persistenz, manuellen und automatischen Build, PE32/PE32+, Exporterhalt, unzulässige PE-Container, fehlgeschlagene Komprimierung und Plattformbeschränkung.

## Prüfung und Grenzen

Python-Syntax, die echte PE32-/PE32+-Erzeugung und die unveränderten Exporte wurden unter Linux geprüft. NTFS/`DeviceIoControl` und **tatsächliches `LoadLibrary` unter Windows** sind dort nicht ausführbar und müssen auf Windows nachgetestet werden. Tests für diese Windows-spezifische Stufe verwenden eine isolierte Kompressionssimulation.
