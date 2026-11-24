# Stage 687 – Turbo-Hilfe: Dateiimport, Syntaxfärbung und F1-Vorspann

Verbindliche Basis: `d64_dism_stage686.zip`.

## Kontextmenü

Im Projekt-Informationen-Dock unter **Turbo Hilfe** steht direkt nach **Inhalt hinzufügen** der neue Eintrag **Datei hinzufügen**. Er öffnet eine Mehrfach-Dateiauswahl für vorhandene `.thlp`-Dateien und registriert diese beim ausgewählten Ordner. Ist ein Blatt ausgewählt, werden die importierten Dateien als Geschwister im zugehörigen Ordner aufgenommen. Vorhandene Dateien werden weder verschoben noch überschrieben. Die Zuordnung wird mit der bestehenden Projektbaum-Persistenz gespeichert und der Hilfecompiler erhält die neue Quellliste.

## Syntax-Highlighting

Der `TurboHelpSourceEditor` verwendet einen `QSyntaxHighlighter` für `%topic`, `%include`, `%ref`, `%anchor` und `%link` (auch unabhängig von Groß-/Kleinschreibung). Nur die Schlüsselwörter werden orange (`#FF981F`) dargestellt, nicht die nachfolgenden Argumente. Alle anderen Editorfunktionen, Zeilennummern und die Minimap bleiben erhalten.

## F1 / CHM

`show_chm_viewer` ist jetzt in den bestehenden `dock_opening_prelude`-Mechanismus eingebunden. Damit erhalten globale F1-Hilfeaktionen und Kontexthilfeaufrufe denselben dark-/light-mode-tauglichen Warte-Splash, der bereits beim Laden anderer Docks/Tabelle verwendet wird. Das Laden beginnt nach dem ersten Paint-Zyklus. Direkt vor `ChmViewerDialog.exec_()` wird der Splash ausgeblendet, da der CHM-Viewer ein modaler Dialog ist und der Splash sonst bis zum Schließen der Hilfe stehen bleiben würde. Die Aufräumroutine nach dem Dialoglauf bleibt beim vorhandenen Vorspann.

## Tests und Einschränkungen

* 29 gezielte Tests zu Stage 620, 685, 686 und 687 erfolgreich.
* Erweiterte Regressionen: 142 bestanden, 5 alte textbasierte Prüfungen fehlgeschlagen. Diese fünf fordern Stand-651/652/655/665-Aufruftexte, die auch im originalen Stage-686-Archiv nicht mehr existieren. Keine neue Laufzeit-Regression aus diesen Tests ableitbar.
* Die native Windows-PyQt5-Oberfläche konnte hier nicht gestartet werden; Splash- und Farbdarstellung müssen unter Windows visuell bestätigt werden.
