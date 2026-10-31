# Stage 513 – Ressourcen-DLLs nach Architektur und Codepage ablegen

**Basis:** `d64_dism_asm_512.zip` (Stage 512).

## Änderung

Der Ressourcen-Editor legt bei den Toolbar-Aktionen **win32 DLL** und **win64 DLL** die drei erzeugten Binärdateien nun in einem Codepage-Unterordner des Architekturverzeichnisses ab.

| Zielbutton | Unicode (1200) | UTF-8 (65001) | ASCII (20127) |
|---|---|---|---|
| win32 DLL | `win32/unicode/` | `win32/utf8/` | `win32/ascii/` |
| win64 DLL | `win64/unicode/` | `win64/utf8/` | `win64/ascii/` |

Für eine RC-Datei namens `Resource32.rc` erstellt jeder Build im zugehörigen Ordner:

- `Resource32.res` (Microsoft RES)
- `Resource32.o` (architekturspezifisches COFF-Objekt)
- `Resource32.dll` (PE32- bzw. PE32+-Ressourcen-DLL)

Die Ordner werden automatisch erstellt. Andere Codepage-/Architektur-Kombinationen bleiben beim erneuten Build erhalten. Die bisherigen Toolbar-Aktionen `RC → RES`, `COFF32`, `COFF64` werden **nicht** umgeleitet.

## Technische Umsetzung

- `resource_dll_codepage_directory(codepage)` bildet Unicode/1200, UTF-8/65001 und ASCII/20127 auf die Unterordnernamen ab und lehnt andere explizit gewählte Codepages mit einer Fehlermeldung ab. Für ältere `.res`-Dateien ohne Codepage-Metadaten (0) wird `unicode` als Vorgabeverzeichnis verwendet.
- `build_resource_dll_files(..., machine=..., codepage=...)` schreibt alle drei Dateien nach `Quellverzeichnis / Architektur / Codepage`; ohne explizite Angabe wird `ResourceEntry.codepage` verwendet.
- `WindowsResourceEditorWidget._selected_dll_codepage()` liest die ComboBox `resource_codepage_combo` **vor** `_compile_current_rc()`, weil diese Funktion das Eigenschaften-Widget neu aufbauen kann.
- `compile_to_resource_dll()` übergibt die ausgewählte Codepage an den zentralen Builder und meldet den vollständigen Ausgabepfad in der Statuszeile.

Die eigentliche Ressourcenkodierung folgt wie bisher dem RC-Quelltext; bestimmte Windows-Strukturen (z. B. `STRINGTABLE` und `MENU`) müssen weiterhin UTF-16LE-Felder enthalten, unabhängig von der gewählten Codepage. Die hier vorgenommene Änderung betrifft **die Ablage der Build-Artefakte**, nicht die vorgeschriebene Binärstruktur von Windows-Ressourcen.

## Tests

- Automatisierte Tests für alle sechs Architektur-/Codepage-Verzeichnisse, PE32-/PE32+-Header und eingebettete Ressourcen.
- Gleichzeitige Existenz aller sechs Kombinationen und Erhalt früherer Build-Ergebnisse geprüft.
- Prüfung der ComboBox-Auswahl vor dem Neuaufbau des Eigenschaften-Widgets durch simulierten Buttonklick.
- Die Stage-512-Regressionsprüfungen wurden an die neue Ordnerstruktur angepasst.
- Python-Syntaxprüfung und ZIP-Integritätsprüfung.

Die native GUI-Laufzeit und `LoadLibraryEx` auf Windows wurden in dieser Umgebung nicht getestet.
