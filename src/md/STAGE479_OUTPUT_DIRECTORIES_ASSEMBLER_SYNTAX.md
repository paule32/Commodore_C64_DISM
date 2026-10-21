# Stage 479 – getrennte Windows-Ausgabeverzeichnisse und Assembler-Modus

Basis: `d64_dism_asm_478.zip`.

## Compiler → Ausgabe-Verzeichnis (für PE32/PE32+ getrennt)

- `Assembler-Zwischenspeicherung`: eigenes Feld mit Verzeichnisdialog; für erzeugte `.asm` und die von diesen abgeleiteten `.extern.inc`/`.payload.inc`.
- `ausführbare Datei`: bisheriges Ausgabe-Verzeichnisfeld; für `.o`/`.obj`, `.exe`/`.dll`. Das vorhandene Ausgabeverzeichnis bleibt aus Kompatibilitätsgründen erhalten.
- Bestehende Checkbox `relative Pfade` wirkt auf beide neuen Pfade. Bei aktiver Option werden projektbezogene Einstellungen beim Build auf das Verzeichnis der aktuellen Quelldatei umgerechnet.
- Beide Pfade und der Syntaxmodus werden unabhängig für PE32 und PE32+ in der Projektdatei (Abschnitt `Settings.Windows.*.Compiler.OutputDirectory`, Schlüssel `AssemblerCache`, `Path`, `AssemblerSyntax`) gespeichert.
- Ohne konfigurierte Pfade bleibt die bisherige Dateiausgabe erhalten.
- Nach erfolgreichem Build wird die tatsächlich gespeicherte EXE über `assembled_program_path` gestartet, unabhängig von deren Verzeichnis.

## Assembler → Assembler Modus

- RadioButtons `Intel Syntax` (Standard) / `AT & T  (GNU kompatibel)`.
- Auswahl separat für PE32/PE32+; permanent im Projekt gespeichert.
- Interner nativer Assembler/COFF-Linker bleibt Intel-orientiert. Für AT&T-Eingabecode wird zuerst der unveränderte `%include`- und `%define`-Präprozessor ausgeführt und die expandierte Quelle anschließend mit `windows_asm_att.py` übersetzt.
- Implementiert: typische Registeroperanden mit `%`, unmittelbare Werte mit `$`, Ziel/Quelle-Reihenfolge, einfache GNU-Befehlsgrößensuffixe, `displacement(%base)` und `displacement(%base,%index,scale)`, `.text/.data/.bss/.section`, `.byte/.word/.long/.quad/.zero/.asciz`, `.globl`, `.att_syntax`.
- Die interne Compiler-Codeerzeugung für BASIC/Pascal/dBASE/WFM erzeugt aus Stabilitätsgründen weiterhin den Intel-Zwischencode. Dies bleibt auch bei aktiviertem AT&T-Modus so; es erfolgt **keine vollständige Ausgabe in GAS-Syntax**.
- **Nicht implementiert**: vollständiger GNU-as-Grammatikumfang inklusive aller Direktiven, Relocation-Ausdrücke, SIMD-Sonderformen, GAS-spezifische Symbole und GNU-ELF-Objektdateien. Unsupported Syntax führt zu einem Fehler statt einer stillen Fehlübersetzung. `GNU kompatibel` bezeichnet hier die unterstützte GNU-AT&T-Teilmenge, nicht Vollkompatibilität.
- Der bereits bestehende `%include`-Präprozessor funktioniert in beiden Modi unverändert.

## Verifikation

- 140 zielnahe Regressionstests bestanden (Stage467–479).
- Neue Tests: relative/absolute ASM-/EXE-Pfade, Legacy-Fallback, AT&T-Quellübersetzung, Includes + Makros, realer PE32-/PE32+-COFF- und PE-Linkaufbau.
- Keine native Windows-/Qt5-GUI-Klickprüfung in dieser Umgebung.
