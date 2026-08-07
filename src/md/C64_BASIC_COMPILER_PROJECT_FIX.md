# C64 BASIC Compiler und Projektlisten-Erweiterung

## Buildablauf

BASIC-Dateien (`.bas`, `.basic`) verwenden denselben dreistufigen Ablauf wie C und Pascal:

1. **Compile** übersetzt BASIC in editierbaren MOS-6510-Assemblercode.
2. **Assemble** übersetzt den ASM-Tab in eine C64-PRG-Datei.
3. **Start** startet die erzeugte PRG-Datei in VICE.

Der erzeugte Assembler beginnt bei `$080D`. Der integrierte Assembler ergänzt automatisch einen BASIC-SYS-Stub bei `$0801`.

## Unterstützte BASIC-Stufe

Der Compiler arbeitet mit 16-Bit-Integerwerten und unterstützt:

- Zeilennummern und mehrere Anweisungen pro Zeile
- `REM` und Apostroph-Kommentare
- numerische Variablen und `LET`
- `PRINT` beziehungsweise `?`, Zeichenketten, Semikolon und Komma
- `IF ... THEN`
- `GOTO`
- `GOSUB` und `RETURN`
- `FOR ... TO ... STEP ...` und `NEXT`
- `POKE`
- `SYS` mit konstanter Adresse
- `END` und `STOP`
- Operatoren `+`, `-`, `*`, `/`, `MOD`, `AND`, `OR`
- Vergleiche `=`, `<>`, `<`, `>`, `<=`, `>=`
- Dezimal-, `$`-Hexadezimal- und `%`-Binärzahlen

Die in der ersten Compilerstufe noch fehlenden Bereiche – Stringvariablen, Fließkomma, Arrays, `INPUT`, `READ/DATA` sowie Datei- und Gerätekanäle – sind im erweiterten Stand implementiert. Einzelheiten stehen in `C64_BASIC_COMPILER_EXTENDED_FIX.md`.

## Kommandozeile

```text
python d64_dism.py --write-c64 programm.bas
```

Erzeugt:

```text
programm.generated.asm
programm.prg
```

## Neue Dokumente und Projektdatei

Ein Dokument aus **Datei → Neu** wird sofort als `Unbenannt_<nummer>.<endung>` im aktiven Projektordner angelegt. Der Eintrag erscheint in der passenden Kategorie und die `.pro`-Datei wird unmittelbar im INI-Format gespeichert.

Falls noch kein Projekt aktiv ist, wird im aktuellen Arbeitsordner automatisch eine freie Datei wie

```text
Unbenannt_Projekt_1.pro
```

angelegt.

## Kontextmenü der Projekt-TreeList

Das Kontextmenü enthält nur noch:

```text
Hilfe
Hinzufügen
Einträge löschen
```

- **Hinzufügen** nimmt eine oder mehrere vorhandene Dateien in die gewählte Kategorie auf.
- **Einträge löschen** entfernt sämtliche Referenzen der gewählten Kategorie.
- Dateien auf dem Datenträger werden dabei nicht gelöscht und nicht umbenannt.
