# Stage 571 – Agent 0001: Deutsche Grammatik, JSON und Dark-Mode

**Verbindliche Ausgangsbasis:** `d64_dism_stage570.zip`.

## Bestandsprüfung und wichtige Einschränkung

`d64_dism.py` referenzierte bereits `from agent_0001 import GermanGrammarWidget`, **aber
`agent_0001.py` und die ursprünglichen ComboBox-Texte waren in Stage 570 nicht enthalten**.
Das frühere Archiv `d64_dism_agent_0001_integration.zip` wurde in der Library
gefunden, war jedoch nicht als Originaldatei materialisierbar. Daher wurde
`agent_0001.py` **neu als kompatibler Einstiegspunkt** angelegt. Es wird nicht
behauptet, dass alle Funktionen des ursprünglichen separaten Grammatikparsers
vollständig rekonstruiert sind.

## Geänderte/ergänzte Dateien

- `d64_dism.py`: Registrierung des Agent-Widgets, Weitergabe des Dark-Mode
  beim Öffnen und bei laufender Theme-Umschaltung.
- `agent_0001.py`: neue PyQt5-Oberfläche für die Auswahl/Eingabe, mittlere
  Token-Tabelle mit explizitem QHeaderView-Dark-Mode, rechts Diagnoseausgabe;
  neue Texte vor Speicherung prüfen und mit Ja/Nein bestätigen.
- `agent_0001_data.py`: JSON-Speicher mit UTF-8, NFC-/Whitespace-Normalisierung,
  Dublettenprüfung, atomischem Schreiben und Fehlerdiagnosen; beschädigte
  JSON-Dateien werden nicht automatisch überschrieben.
- `agent_0001_core.py`: ein bewusst begrenzter Basisprüfer für die bekannten
  Beispiele (Fragewort-/Satzbau- und Kongruenzmuster), **kein vollständiger
  grammatischer Parser** und kein ANTLR-Ersatz.
- `agent_0001_examples.json`: JSON-Startdaten mit den fünf aus dem vorherigen
  Agent-0001-Verlauf bekannten Beispieltexten.
- `test_stage571.py`: unabhängige Tests für Datenhaltung, Prüfung und Integration.

## JSON-Format

```json
{
  "version": 1,
  "examples": [
    {"text": "Was ist heute für ein Tag?"}
  ]
}
```

Die ausgelieferte Datei `agent_0001_examples.json` ist eine **nur gelesene
Startvorlage**. Neue Benutzereinträge werden unter Windows in
`%APPDATA%\\d64_dism\\agent_0001_examples.json` gespeichert (unter Linux in
`~/.config/d64_dism/agent_0001_examples.json`, falls `XDG_CONFIG_HOME` nicht
gesetzt ist). Beim ersten Hinzufügen übernimmt die Benutzerdatei automatisch
auch die Startbeispiele. Benutzerdateien bleiben bei Programmupdates erhalten.

## Bedienablauf

1. Einen vorhandenen Text wählen oder eigenen Text in die editierbare ComboBox
   schreiben.
2. Mit **Prüfen** oder **Enter** die Basisanalyse starten. Die Tabelle und
   die rechte Diagnoseanzeige werden aktualisiert.
3. Nur bei noch nicht gespeicherten Texten erscheint eine Nachfrage.
   Auch ein Text mit gefundenen Auffälligkeiten kann bewusst gespeichert
   werden, um ihn künftig als fehlerhaftes Grammatikbeispiel wiederzuverwenden.
4. **Ja** speichert dauerhaft in die JSON-Benutzerdatei. **Nein** belässt die
   Eingabe ungespeichert. Bereits gespeicherte Texte erzeugen keine Nachfrage.

## Tests / Restriktionen

- `pytest -q test_stage570.py test_stage571.py`: **30 bestanden, 1 übersprungen**;
  drei zusätzliche parametrische Unittests erfolgreich.
- Die neue Qt-Oberfläche wurde als struktureller Test geprüft; ein nativer
  PyQt5-Durchlauf ist hier nicht möglich, da PyQt5 nicht installiert ist.
- `d64_dism.py` enthält bereits Python-3.15-`lazy`-Importsyntax; unter dem
  in der Testumgebung verfügbaren älteren Python funktioniert `py_compile`
  deshalb nicht direkt. Die bestehenden Stage-570-Tests prüfen diese Datei
  mit dem bekannten Kompatibilitätsschritt.
- Eine vollständige syntaktische Prüfung und Semantikanalyse für beliebige
  deutsche Sätze ist **nicht** implementiert. Dafür wäre die Originaldatei
  des vorherigen Agent-0001-Moduls nötig.

Alle übrigen Dateien aus Stage 570 bleiben im Archiv unverändert.
