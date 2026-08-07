# Editor-Neuanlage und Compile/Assemble/Start-Pipeline

## Behobener Fehler

Neue Dokumente aus `Datei -> Neu` besitzen zunächst noch keinen Dateipfad. Die
Editorsteuerung bestimmte den Dokumenttyp bisher ausschließlich über
`document.path.suffix`. Deshalb wurden bei einem neuen `Unbenannt_1.c` oder
`Unbenannt_1.pas` weder die Build-Leiste noch die Zielauswahl angezeigt.

`DocumentEditor.effective_suffix` wertet jetzt zuerst den gespeicherten Pfad und
anschließend den vorläufigen Registerkartennamen aus. Damit verhalten sich neu
angelegte Dokumente sofort genauso wie per Doppelklick geöffnete Dateien.

## Sichtbare Steuerung

### C und Pascal

Im Quelltext-Tab erscheinen sofort:

- `Compile`
- `C-64`
- `Amiga`
- Buildstatus

Der `Start`-Knopf wird im Quelltext-Tab für C/Pascal nicht angezeigt, da dort
noch kein Binärprogramm existiert.

### Assembler

Im ASM-Quelltext-Tab erscheinen:

- `Assemble`
- `Start`
- `C-64`
- `Amiga`

## Dreistufiger Build

1. **Compile**
   - übersetzt C oder Pascal ausschließlich in zielabhängigen Assemblercode;
   - speichert `.generated.asm` bzw. `.generated.amiga.asm`;
   - öffnet automatisch den erzeugten ASM-Tab.

2. **Assemble**
   - übersetzt den sichtbaren und editierbaren ASM-Code;
   - erzeugt je nach Ziel `.prg`, `.amiga` oder `.adf`;
   - aktiviert anschließend `Start`.

3. **Start**
   - startet das zuletzt assemblierte Programm mit VICE oder WinUAE.

Bei einem noch ungespeicherten Dokument öffnet der erste Build automatisch den
Dialog `Speichern unter...`, weil die ASM- und Binärausgabe einen eindeutigen
Dateinamen benötigt.

Wird der C- oder Pascal-Quelltext nach dem Compile verändert, wird `Assemble`
bis zum nächsten Compile deaktiviert und der ASM-Status als veraltet markiert.

## Registerkarten-Kontextmenü

Das Kontextmenü besitzt jetzt nur noch:

- `Neu` als Untermenü
- `Speichern`
- `Speichern unter...`

Das Untermenü `Neu` verwendet dieselben `QAction`-Objekte wie das Hauptmenü und
enthält daher identisch:

- BASIC-Programm
- Assembler-Programm
- Pascal-Programm
- C-Programm
- C-64 Character Map
- C-64 Text Screen
- C-64 Pixel Screen
- Textdatei

## Validierung

- Python-Syntaxprüfung von `d64_dism.py`: erfolgreich
- 16 neue/angepasste Pipeline- und UI-Tests: erfolgreich
- 55 gezielte Projekt-/Editor-/C64-Werkzeugtests: erfolgreich
- vollständiger Testlauf: 97 Tests erfolgreich
- 13 Compiler-Testmodule konnten wegen der lokal inkompatiblen ANTLR-Runtime
  nicht importiert werden
