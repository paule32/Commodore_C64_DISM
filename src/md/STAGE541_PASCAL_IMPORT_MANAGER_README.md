# Stage 541 – Pascal Import-Manager, Cache und PE-Link-Manifeste

**Verbindliche Basis:** Stage 540 (`d64_dism_stage540.zip`). Die vorherigen
Optimierungs-, Runtime-, CES-, Packer- und Property-Änderungen bleiben erhalten.

## GUI / .pro

Die TreeList enthält für Windows 32-Bit und 64-Bit unabhängig:

`Compiler → Pascal → Importe / Cache`

Die Seite bietet:

- **Import-Cache verwenden** (Standard: an)
- **Nicht verwendete Imports entfernen** (Standard: an)
- **Import-Deklarationen in .inc auslagern** (Standard: aus)
- **Cache für dieses Ziel löschen** (nur Cache-JSONs der Zielarchitektur)

Die Projektdatei erhält:

```ini
[Settings.Windows.32Bit.Compiler.Pascal.Imports]
CacheEnabled = true
PruneUnused = true
Externalize = false

[Settings.Windows.64Bit.Compiler.Pascal.Imports]
CacheEnabled = true
PruneUnused = true
Externalize = false
```

Alte Projekte ohne diese Abschnitte nutzen die Standardwerte.

## Implementierte Komponenten

### `pascal_import_manager.py`

- Einlesen der bekannten `import symbol, "dll", "export"`- und `extern symbol`-Direktiven
- Konflikterkennung für widersprüchliche Importziele
- Konservative Referenzermittlung anhand der übrigen Assembler-Anweisungen und Datenreferenzen
- Kein Entfernen nur aufgrund fehlender Referenz bei Unit-/COFF-/ASM-Mehrmodul-Builds
- Deduplizierung identischer Deklarationen und Ausblenden sicher unbenutzter Deklarationen im Einzelmodul
- Zeilenzahl des ASM-Textes und bestehende Pascal-Quellzeilenzuordnung bleiben erhalten
- Versionierte, nach SHA-256 adressierte JSON-Metadaten (Cache-Hit/Miss)
- Automatische Invalidierung bei Änderungen von Quelle, Assembler-Ausgabe, Optimierungsprofil, Zielarchitektur und lokal gefundenen `libd64_*`-DLLs
- Atomare Schreibvorgänge pro Cache-Key auch bei mehreren parallelen Unit-Compilern
- Cache enthält **keine Laufzeitadressen, IAT-Adressen, Handles oder geladenen DLL-Instanzen**

Beim Projekt-Build liegen die Import-Caches unter
`<Projektordner>/runtime/pascal/cache/pe32/` und `.../pe64/`.

Ohne Projektdatei erfolgt die Ablage im Unterverzeichnis
`.d64cache/imports/pe32|pe64` beim angegebenen Ausgabeverzeichnis oder der Quelldatei.

### `c64pascal/compiler.py`

Beide Windows-Backends übergeben ihren fertigen Assembler an die Importanalyse.
Neue optionale Parameter für `compile_pascal_to_assembly`:

- `import_cache_enabled`
- `import_prune_unused`
- `import_cache_directory`
- `import_runtime_version`

Das Ergebnis besitzt ein `import_manifest` mit deklarierten und tatsächlich
referenzierten Symbolen sowie Cache-Hit/Miss. Andere Targets bleiben unberührt.

### `pascal_parallel_build.py`

Die Worker erhalten getrennte Projektoptionen, nutzen den gemeinsamen
atomaren Cache und legen nach der ASM-Erzeugung pro Unit ein
`*.asm.imports.json` an. Optional wird eine benachbarte
`*.asm.imports.inc` erzeugt. Abhängigkeitssteuerung und `.pui`-Erzeugung
bleiben unverändert.

### Integrierter COFF32-/COFF64-Linker (`d64_dism.py`)

Die endgültige Importmenge wird **aus den Symbol-Relocations aller gelinkten
COFF-Dateien** bestimmt. Nicht referenzierte Import-Deklarationen werden
nicht in die finale PE-Importtabelle übernommen. Das war für viele
COFF-Auflösungswege bereits gegeben und wurde für Stage 541 explizit mit
per-Link-Manifesterzeugung verbunden.

Bei einem Pascal-Programm-/DLL-Link entsteht neben der Ausgabe:

`test_raise.exe.imports.json` bzw. `name.dll.imports.json`

Die Manifeste zeigen die vom gesamten Link verwendeten Import-Symbole, deren
DLL und Exportnamen sowie deklarierte, aber ungenutzte Symbole. Für
PE64 wird sowohl der normale als auch der gepackte Linkpfad berücksichtigt.

**Wichtig:** Die Import-Metadaten werden **nicht** mit Windows-Funktionsadressen
gecached. Die tatsächliche Auflösung geschieht weiter beim Laden der EXE.
Die CES-Diagnose für fehlende DLLs/Exports bleibt im Windows-Loader erhalten.

Bei aktiviertem Link mit Ordinalen kann das Link-Manifest zunächst den
symbolischen Funktionsnamen der ursprünglichen COFF-Referenz enthalten. Der
PE-/D64I-Writer entscheidet weiterhin über den finalen Ordinalimport.

### `.inc`-Auslagerung

Bei expliziter Aktivierung werden die deklarierten Imports und externen Symbole
in eine ASM-Nachbardatei geschrieben und über `%include "...imports.inc"`
eingebunden. Der vorhandene Windows-ASM-Präprozessor expandiert diese
Direktive vor dem Assemblieren. Die Option ist standardmäßig deaktiviert,
um ältere Workflows nicht zu ändern. Ein `.inc`-File reduziert die Größe der
sichtbaren ASM-Datei, jedoch **nicht automatisch** die Größe der EXE.

## Tests

- `python -m unittest -v test_stage541.py` – 12 neue gezielte Tests
- In dieser Umgebung zusätzlich 41 bestehende Tests aus Stage 532–540,
  einschließlich Stage 536/539, erfolgreich; gesamt **53/53**.
- AST-Codegenerator-Smoketests für PE32 und PE64 mit Stack-Cookie-Imports.
- Analyse der vorhandenen `runtime/pascal/test/test_raise.generated.pe32.asm`.
- Cache-Invalidierung, Konkurrenztests mit parallelen Schreibzugriffen,
  `.pro`-Roundtrip und getrennte Architekturkonfigurationen.
- Syntaxprüfung der Hauptdatei nach ausschließlich temporärer Entfernung
  des Python-3.15-Soft-Keywords `lazy` (die ausgelieferte Datei bleibt
  **unverändert** in dieser Hinsicht).

**Noch nicht möglich in der Prüf-Umgebung:** vollständiger Windows-IDE-Build,
visuelle PyQt5-Kontrolle, tatsächlicher PE32-/PE32+-Lauf und die Messung von
EXE-Größe beziehungsweise Compile-Zeit auf Windows. Die installierte
ANTLR-Runtime weicht von der im Projekt verwendeten Version 4.13.2 ab.

Der Import-Cache speichert bewusst **nur Import-Metadaten**, nicht komplette
Compiler-ASTs, fertig assemblierte COFF-Objekte oder PE-Images. Er ersetzt
keinen zukünftigen inkrementellen Objektcache.
