# Stage 476 – Fortschritt über dem WFM-Assembler-TabWidget

Basis: `d64_dism_asm_475.zip`.

## Benutzeroberfläche

Im `dbase_form_assembly_host` befindet sich oberhalb von `dbase_form_assembly_tabs` eine Kopfzeile mit `Assembler`, der `QProgressBar` (`dbase_form_asm_progress`) und rechts dem Statuslabel (`dbase_form_asm_progress_label`).

- Vor dem Build: Fortschrittsbalken unsichtbar; beim Start sichtbar, Mindest-/Startwert 1.
- Compile: Gesamtzahl nach Ausführung des dBASE-Präprozessors; expandierte `#include`-Dateien zählen mit. Der WFM-Parser meldet die tatsächlich verarbeiteten Zeilen. Nach erfolgreicher Codeerzeugung und Ausgabe der ASM-Datei wird der Balken ausgeblendet, das Label zeigt gelb `Erfolgreich kompiliert !`. Fehler: rot `Fehler beim kompilieren !`.
- Assemble: Die tatsächlichen `%include`-Dateien werden mit dem PE32-/PE64-Präprozessor expandiert. `MacroResult.locations` bestimmt das Maximum; verschachtelte Includes zählen mit. Die internen PE32-/PE64-Assembler melden während des ersten Assembler-Durchlaufs jede verarbeitete physische Zeile. Erst wenn auch die Linker-/Ausgabestufe erfolgreich war, wird der Balken ausgeblendet und gelb `Linkvorgang erfolgreich !` gemeldet. Im Fehlerfall rot `Fehler, Linken nicht möglich !`.
- Beim Start einer Aktion wird der Quellcode-Tab sichtbar gemacht, damit die Anzeige nicht hinter dem Designer-Tab liegt.
- Der GUI-Eventloop wird während der Zeilenmeldungen gedrosselt (ca. 35 ms) und ausschließlich mit `ExcludeUserInputEvents` bearbeitet, damit keine zweite Compile-/Assemble-Aktion reentrant gestartet wird. Die eigentliche Codeerzeugung und Verlinkung laufen weiterhin im bisherigen Build-Aufruf (kein zusätzlicher Worker-Thread).

## Schnittstellen

Die folgenden optionalen Callbacks bleiben bei anderen Aufrufern standardmäßig deaktiviert:

- `parse_dbase_wfm(..., progress_callback=callback)` meldet verarbeitete Quellzeilen.
- `assemble_pe32_coff_object(..., progress_callback=callback)` und `assemble_pe64_coff_object(...)` melden `(expanded_line, expanded_total)`.
- `*_write_pe32/64_generated_objects(..., progress_callback=callback)` reicht den Callback **nur an das Hauptmodul** weiter. Zusätzlich gelinkte Module ändern nicht den Fortschrittsnenner der Haupt-ASM-Datei.

## Einschränkungen

Es ist *zeilenbasierter Parser-/Assemblerfortschritt*, keine Zeitprognose. Bei aufwendiger WFM-Codeerzeugung oder COFF-Verlinkung kann die Anzeige schon die letzte Quellzeile erreicht haben, obwohl noch intern gearbeitet wird. Bis zum Abschluss bleibt die ProgressBar daher sichtbar. Ein zuvor eintretender Präprozessorfehler kann die Zählung verhindern; der Balken startet dann bei 1 und zeigt anschließend die rote Fehlermeldung.

Die GUI wurde in dieser Umgebung nicht nativ mit PyQt5 gestartet. Die Callback-/Linker- und WFM-Parserpfade wurden mit realen PE32-/PE32+-Assemblytests geprüft.
