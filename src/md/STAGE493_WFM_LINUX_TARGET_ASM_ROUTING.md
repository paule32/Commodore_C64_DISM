# Stage 493: WFM Zielarchitektur und ASM-Ausgabedateien

Verbindliche Basis: d64_dism_asm_492.zip.

## Behobener Fehler

`DocumentEditor.update_syntax_highlighting()` setzte das dBASE-Buildziel bislang
unbemerkt von `linux32`/`linux64` auf `pe32` zurück. Dadurch wurde Linux-x64
Assemblercode im PE32-Assembler weiterverarbeitet (`mov rdi`), und der
ASM-Dateiname war z.B. `Form2.generated.pe32.asm` statt Linux64.

## Neue Zuordnung

- Windows PE32: `Form2.generated.pe32.asm` -> PE32 COFF + PE-Linker
- Windows PE64: `Form2.generated.pe64.asm` -> PE64 COFF + PE-Linker
- Linux ELF32: `Form2.generated.linux32.asm` -> ELF32 i386
- Linux ELF64: `Form2.generated.linux64.asm` -> ELF64 AMD64

Die Linux-Architekturen sind jetzt auch in den beiden internen
`DocumentEditor`-Zielauswahlfeldern für dBASE/WFM aktiviert.
`compile_dbase_form()` schreibt die gewählte Architektur verbindlich in den
Assemblerdateinamen und merkt sich das Ziel am Build-Dokument.
`assemble_dbase_form()` stellt vor der Ausführung sicher, dass ausgewähltes
Ziel, Dokumentziel, erzeugter Dateiname und kompiliertes Ziel übereinstimmen.
Bei einem Alt-Build mit falschem Dateinamen erscheint eine deutschsprachige
Fehlermeldung mit beiden Namen und der Aufforderung, erneut zu kompilieren.
Ein Architekturwechsel und das Öffnen eines anderen Formulars entwerten
veraltete Assembler-/Linkzustände.

Der bereits vorhandene interne Linux-ELF32-/ELF64-Assembler/-Linker aus
Stage 486-492 bleibt unverändert; ebenso Windows COFF/PE32/PE64.
`assemble_generated_document()` wechselt nicht mehr zu dem versteckten
Hilfs-DocumentEditor des WFM-Designers.

## Nachprüfung unter Windows/Linux

1. Form2.wfm im Formulardesigner öffnen.
2. Im Menü Erstellen oder in der WFM-Ziel-ComboBox Linux64 auswählen.
3. Compile: `Form2.generated.linux64.asm` muss entstehen.
4. Assemble: `Form2.linux64.o` und `Form2.elf64` müssen entstehen; kein PE32-Assembler.
5. Wechsel auf Linux32/PE32/PE64 jeweils nach neuem Compile prüfen.
6. Änderungen an der Formularquelle oder der Architektur vor dem nächsten
   Assemble erfordern einen neuen Compilelauf.

Automatische Tests: `test_stage493_wfm_target_assembler_dispatch.py`
(11 Tests bestanden). Native Qt5-/Windows-Interaktion hier nicht geprüft.
