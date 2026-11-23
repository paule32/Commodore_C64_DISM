# Stage 649 – dBASE-Klassen-DLL: EXPORTs als PE32-/PE64-Include

**Verbindliche Grundlage:** `d64_dism_stage648.zip`.

## Ziel

Die in `d64dbase/dll_backend.py` erzeugten `export "...", symbol`-Deklarationen
werden beim Speichern des generierten Assemblercodes in eine separate `.inc`-
Datei geschrieben. Die frühere In-Memory-API `compile_dbase_to_assembly()`
bleibt unverändert: Sie liefert weiterhin vollständigen, ohne Sidecar
assemblierbaren Code zurück.

## Neue Dateinamen (im ASM-Ausgabeverzeichnis)

| Ursprüngliche erzeugte ASM-Datei | Export-Include |
|---|---|
| `System.SysUtils.generated.pe32.asm` | `System.SysUtils.pe32.inc` |
| `System.SysUtils.generated.pe64.asm` | `System.SysUtils.pe64.inc` |

Das gilt für dBASE-CLASS-DLLs (source_kind `library`); normale PRG-EXEs
bleiben unverändert. Bisherige getrennte `.extern.inc` für Importe und
`.payload.inc` für WFM bleiben erhalten.

Der generierte ASM-Header sieht beispielsweise so aus (tatsächliche Zeilen
und Nummern hängen vom Inhalt ab):

```asm
bits 32
; ...
entry __d64_dll_entry
%include "System.SysUtils.pe32.inc"
%line 47

section .text
```

`%line N` setzt die *nachfolgende* ASM-Zeile auf die logische Zeile `N` zurück.
Dies wird für jeden entfernten EXPORT-Block erzeugt, auch wenn die Anweisungen
an mehreren Stellen auftreten. Die Include-Datei erhält ihre eigenen
Datei-/Zeileninformationen. `%line` selbst erzeugt weder Bytes noch COFF-Symbole.

Die Include-Datei enthält die exakt vom Compiler generierten `export`-
Deklarationen. Sie wird vor dem Speichern der Haupt-ASM-Datei atomar geschrieben
und beim Assemblieren relativ zur ASM-Datei gefunden. Der interne Makro-
Prozessor löst das `%include` vor dem COFF-Parser auf.

## Technische Anpassungen

- `windows_asm_macros.py`: neue reine Funktion
  `externalize_windows_exports(assembly, assembly_path)` mit Rückgabe
  `(asm_text, inc_path, inc_text)`. Keine selbstständigen Dateizugriffe.
- `d64_dism.py`: Integration in `_finish_compile_stage()` nur für Windows-
  dBASE-Library-Targets, nach bestehender Import- und Payload-Auslagerung
  und vor möglicher AT&T-Konvertierung. Ausgabe der Include-Datei mit dem
  vorhandenen atomaren Writer.
- `test_stage649.py`: Regressionstests für Include-Dateinamen, PE32 und PE64,
  `%line`-Quellpositionen, zusätzliche Export-Blöcke, identische COFF-Code-
  und Exporttabellen und erzeugte DLLs, sowie AT&T-Syntax.

## Testnachweise

- `pytest -q test_stage649.py`: PE32 und PE64, COFF, DLL-Link, Line-Maps.
- `pytest -q test_stage605.py test_stage646.py test_stage641.py test_stage639.py -k 'not real_pe32_pe64_class_dlls and not original_source_assembles_to_coff'`:
  55 Tests, 59 Untertests bestanden.
- `pytest -q test_stage648.py -k 'exception_catch_block_copy_and_nonvolatile_regs or internal_assembler_rep_movsd_opcode'`:
  4 Tests bestanden (2 langsamere Linktests ausgenommen).
- Manueller AT&T-Roundtrip: PE32 und PE64 jeweils 26 Exporte aus
  `System.SysUtils.prg` erfolgreich geparst.

**Hinweis:** Kein Ausführungstest auf einem echten Windows-System erfolgt.
Länger laufender vollständiger Stage-639–649-Regressionstest wurde nach
Timeout abgebrochen; nur die hier angegebenen erfolgreichen Tests gelten
als Nachweis.
