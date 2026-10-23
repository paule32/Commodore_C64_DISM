# Stage 483 – Deutsche Standard-Kontextmenüs und WFM-AT&T-Korrekturen

**Verbindliche Basis:** `d64_dism_asm_482.zip`. Keine Änderungen an der Intel-Codeerzeugung, dem Makro-Präprozessor, den Win32-Importen oder dem Linker.

## Qt-Bearbeitungsmenüs

Das globale Eventfilter des Hauptfensters verwendet für normale `QLineEdit`-Eingabefelder (sowie standardmäßige `QPlainTextEdit`-/`QTextEdit`-Instanzen) deren originale `createStandardContextMenu()`-Aktionen und ersetzt ausschließlich den angezeigten QAction-Text:

- Undo → Rückgängig (Strg+Z)
- Redo → Wiederherstellen (Strg+Y)
- Cut → Ausschneiden (Strg+X)
- Copy → Kopieren (Strg+C)
- Paste → Einfügen (Strg+V)
- Delete → Löschen
- Select All → Alles markieren (Strg+A)

Separatoren, QAction-Objekte, deren `triggered`-Verbindungen, `enabled`-Zustand und echte Qt-Tastaturkürzel bleiben erhalten. Benutzerdefinierte Kontextmenüs, insbesondere der WFM-ASM-Editor und DBF-Gittereditoren, werden nicht überschrieben; die bisherige Übersetzung dort verwendet ebenfalls „Alles markieren“.

## WFM unter GNU-AT&T

Das WFM-Codegenerat liefert unter anderem `.entry __d64_wfm_entry`. Stage 480 verwandelte eine punktpräfigierte `.entry`-Direktive irrtümlich in den AT&T-Instruktionsoperanden `.entry $__d64_wfm_entry`. Damit schlug die anschließende Rückübersetzung an der unbekannten Direktive `.entry` fehl.

Der Intel→AT&T-Konverter behandelt jetzt `entry`, `.entry`, `.d64_entry` als Metadaten-Direktiven und erzeugt stets `.d64_entry __d64_wfm_entry`, **ohne** `$`. Bei der Rückübersetzung werden `.d64_entry`, das alte `.entry __d64_wfm_entry` und sogar das ehemals falsche `.entry $__d64_wfm_entry` zu `entry __d64_wfm_entry` normalisiert. Ungültige Einstiegssymbole lösen einen eindeutigen Fehler aus.

Weitere im realen WFM/WinAPI-Build entdeckte Fehler wurden korrigiert:

- GNU-x87-Ganzzahl-/Gleitkomma-Suffixe werden passend zur tatsächlichen Speicherbreite konvertiert. `FISTPL` bezeichnet einen 32-Bit-Integer-Speicheroperand, `FISTPLL` 64 Bit; `FILDL` bezeichnet 32 Bit, `FILDLL` 64 Bit. Gleitkommaoperationen `FLDS/FLDL` usw. werden getrennt behandelt.
- In direkter GNU-Adressierung werden symbolische Offsets wie `__dbase_ffi_return+4` als Speicheroperanden einschließlich `[ ... ]` und Größenpräfix in die Intel-COFF-Darstellung zurückgewandelt, nicht als fehlerhafte unmittelbare Werte.
- `%include` und `%define` funktionieren weiterhin; sie werden vor der AT&T-Umsetzung expandiert.

## Verifikation

- Neue Tests: `test_stage483_german_input_context_menus.py`, `test_stage483_att_wfm_entry_regression.py`.
- Der komplette WFM-ASM-Rundlauf inklusive des tatsächlichen WFM-Einstiegs wurde für PE32 und PE32+ assembliert und zu Windows-EXE-Dateien verlinkt.
- Ein WFM mit Win32-FFI-Aufruf wurde für PE32 und PE32+ über Intel → AT&T → Intel übersetzt und verlinkt; Maschinenprogramm (`.text`) und Datensektion (`.data`) sind bei direktem Intel-Code und AT&T-Rundlauf bytegleich.
- Die interaktive Qt5-Oberfläche lässt sich in dieser Testumgebung mangels PyQt5 nicht starten. Windows-Start der generierten EXE wurde ebenfalls nicht erprobt.
