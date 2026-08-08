# Projekt-Doppelklick, F1-Kontexthilfe und F2-Build

## Projekt-TreeList

Die Projekt-TreeList verwendet jetzt Doppelklick fuer Aktionen:

- `Archive`-Hauptknoten: Doppelklick klappt den Zweig auf/zu.
- `.a`-Archivknoten: Doppelklick zeigt `Archiv-Informationen`.
- `.o/.obj`-Unterknoten: Doppelklick zeigt `Objekt-Informationen`.
- Normale Projektdateien: Doppelklick oeffnet die Datei.
- Die Archive-/Objekt-Checkboxen bleiben erhalten und werden durch normalen Einfachklick auf die Checkbox geschaltet.

Damit kann das Markieren fuer Loesch-/Archivaktionen nicht mehr versehentlich die Informationsansicht oeffnen.

## F2 im BASIC-/C-/Pascal-Quelltexteditor

F2 benutzt einen gemeinsamen Buildpfad.

### Hauptprogramm

Erkennung:

- BASIC: derzeit immer Hauptprogramm (C64-BASIC-Frontend).
- C: nur eine echte Definition `main(...) { ... }`; ein Prototyp `main(...);` reicht nicht.
- Pascal: `source_kind == program` des Pascal-Compilers.

Ablauf:

1. Quelle speichern, falls notwendig.
2. Compile nach Assembler.
3. Assemble.
4. Link.
5. Zielprogramm schreiben.
6. Direkt starten (VICE/WinUAE/Windows je Target).

Unter PE32/PE64 werden zusaetzlich vorhandene Projektobjekte und Archive mitgelinkt:

- gleichnamige `.o`-Dateien anderer C- bzw. Pascal-Quellen im Projekt,
- C-Archive unter `C-Programme -> Archive`,
- wenn ein eingetragenes Archiv noch nicht erzeugt wurde: dessen vorhandene Objekt-Unterknoten einzeln.

### Nicht-Hauptprogramm

- PE32: erzeugt nur ein relocierbares COFF32-`.o`.
- PE64: erzeugt nur ein relocierbares COFF64-`.o`.
- C64/Amiga: der Compile-Schritt bleibt erhalten; ein relocierbarer Objektwriter existiert fuer diese Ziele derzeit noch nicht.

Compilerwarnungen, Compilerfehler, Assemblerfehler und Linkerfehler benutzen weiterhin die bestehenden Meldungs- und Protokollpfade.

## F1-Kontexthilfe

F1 im Texteditor bestimmt den Bezeichner am Cursor und oeffnet den CHM-Viewer unmittelbar.

Unterstuetzt werden insbesondere:

- BASIC-/C-/Pascal-Schluesselwoerter,
- Assembler-Mnemonics,
- dokumentierte Funktions-/Methodennamen.

Der Funktionsname wird auch erkannt, wenn der Cursor bereits direkt auf bzw. hinter der oeffnenden Klammer steht, z. B. `printf(`, `WriteLn(` oder `CreateWindowExA(`.

Die fruehere Debug-MessageBox vor dem CHM-Aufruf wurde entfernt.
