# Stage 572 – Agent 0001: Tabellenheader, Speichernachfrage, ComboBox

**Verbindliche Ausgangsbasis:** `d64_dism_stage571.zip`.

## Behobene Probleme

1. Die mittlere Token-Tabelle hatte nur für den **horizontalen** Header ein eigenes Qt-Stylesheet; der **vertikale** Header war ausgeblendet. Jetzt sind beide Header sichtbar und erhalten für Dark/Light-Mode dieselben expliziten Hintergrund-/Textfarben. Zusätzlich gibt es eine `QPalette`-Absicherung und eine passende Formatierung für die Tabellen-Ecke.
2. Die Speichernachfrage für neue Sätze wurde zuvor ausschließlich über den Text in der **editierbaren ComboBox** ausgelöst. Das ursprünglich bekannte separate Eingabefeld „Satz:“ war im Stage-571-Ersatzmodul nicht vorhanden. Stage 572 stellt dieses Feld wieder her und verarbeitet beide Eingabewege durch dieselbe Prüfung und Nachfrage.
3. Die ComboBox wurde nach Speichern neu befüllt, aber bisher wurde nur `setEditText()` statt eines echten Listeneintrags (`setCurrentIndex()`) verwendet. Jetzt wird der gespeicherte Satz in der JSON-Liste gesucht, in der ComboBox sichtbar **selektiert** und die Anzeige aktualisiert.

## Bedienung

- Satz im Eingabefeld „Satz:“ schreiben und **Prüfen** drücken; oder direkt in der editierbaren ComboBox schreiben und **Enter** oder **Prüfen** drücken.
- Zuerst wird der eingegebene Satz über die vorhandene Teilgrammatik analysiert. Bei einem **neuen** Satz erscheint eine Ja/Nein-Nachfrage, auch wenn die Basisprüfung eine Auffälligkeit meldet.
- **Ja**: Text in die JSON-Datei schreiben und den neuen ComboBox-Eintrag auswählen.
- **Nein**: Kein Dateizugriff zum Speichern, keine Aufnahme in die ComboBox.
- Bereits gespeicherte Sätze erzeugen keine Nachfrage. Bei beschädigter JSON-Datei wird nicht überschrieben.
- Benutzerdaten liegen wie zuvor unter Windows in `%APPDATA%\d64_dism\agent_0001_examples.json`; `agent_0001_examples.json` im Programmverzeichnis ist nur die Startvorlage.
- Bei aktivem Dark-Mode wird der horizontale und der vertikale Header dunkel (`#303030`), die Schrift hell (`#f5f5f5`). Im Light-Mode werden beide entsprechend hell dargestellt.

## Geänderte Dateien

- `agent_0001.py`: Qt-Theme, Satzfeld, Eingabequellenerkennung, Ja/Nein-Persistenz, ComboBox-Auswahl.
- `test_stage571.py`: alte Header-Assertion an die neue gemeinsame Headerformatierung angepasst.
- `test_stage572.py`: neue Tests für beide Eingabewege, JSON-Roundtrip, Dialogzustimmung, Duplikate, beschädigte JSON, Headerstil und optional native Qt-Bedienung.
- Diese README.

Keine Änderungen an `d64_dism.py`, `agent_0001_data.py`, `agent_0001_core.py` oder anderen Bestandteilen der Stage 571.

## Tests

`pytest -q test_stage55*.py test_stage56*.py test_stage570*.py test_stage571.py test_stage572.py` (ausgewählte Tests Stage 553–572): **216 bestanden, 50 übersprungen, 205 Subtests bestanden**.

Die übersprungenen GUI-Tests benötigen PyQt5. Die tatsächliche Dark-Mode-Darstellung der Header und die Bedienung unter Windows konnten hier nicht nativ überprüft werden; Ablauf und JSON-Zustandsänderungen wurden Qt-unabhängig mit GUI-Dummies getestet.

## Bekannte Grenze

`agent_0001_core.py` bleibt die Teilgrammatik-Basisprüfung aus Stage 571; dies ist weiterhin **kein vollständiger deutscher Grammatikparser**. Grammatik-Inhalte wurden nicht geändert.
