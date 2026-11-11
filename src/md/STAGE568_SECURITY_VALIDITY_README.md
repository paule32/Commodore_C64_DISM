# Stage 568 – Sicherheit: Serialstatus und Gültigkeits-Bereich

Verbindliche Basis: `d64_dism_stage567.zip`. Änderungen beschränken sich auf
`installer_security_settings.py`, `software_installer_dialogs.py`, die
Sicherheit-Hilfe und ihre Tests. Die vorhandenen Compiler-/IDE-Dateien bleiben
auf dem Stand von Stage 567.

## Serial Nummer – Listen Eigenschaften

Die Nummerntabelle enthält jetzt drei Spalten: `Serial Nummer`, `Belegt`
(Checkbox je Reihe) und `Reg. Count` (editierbare nichtnegative Ganzzahl).
Die zuvor vorhandenen Monospace-Fonts, Dark-Mode-Header und Kommandos bleiben.
Undo/Redo berücksichtigt auch Belegt und Registrierungszähler. Beim Sortieren
bleiben die Metadaten an die Serial-Nummer gebunden. Copy/Paste, Textimport und
Textdruck nutzen weiterhin ausschließlich die Nummern selbst.

Die Projektdatei speichert die Nummern wie bisher als Stringliste. Bei Bedarf
erscheint zusätzlich in der betroffenen Liste `serial_details`, z. B.:

```json
{
  "name": "Standardliste",
  "configurations": ["Standard"],
  "serial_numbers": ["ABCD-EFGH", "IJKL-MNOP"],
  "serial_details": {
    "ABCD-EFGH": {"occupied": true, "reg_count": 2}
  }
}
```

Fehlende Metadaten bedeuten `occupied=false`, `reg_count=0`.
Die Vergabe oder Zählung wird in Stage 568 noch nicht von einem laufenden Setup
automatisch geändert.

## Gültigkeits-Bereich

Der bisherige zweite Tab heißt nun `Gültigkeits-Bereich`.
Der Sicherheitsdialog behält seine Geometrie (620×550) und den
Schwarz-Weiß-Titelverlauf im Dark-Mode. Weil drei GroupBoxen in dieser Größe
nicht vollständig nebeneinander und untereinander passen, ist der Inhalt des
Tabs scrollbar; die unteren Dialogbuttons bleiben sichtbar.

Links:
- **Gültigkeit Datum**: Checkbox `Datum des Auslaufen`, Kalender für absolutes
  Datum, 30 Tage nach Erstellung oder 30 Tage nach erstem Start, Abbruch bei
  nicht beschreibbarer Registry, Rest-Tage anzeigen.
- **Zerfall - Zähler**: aktivieren, bis zu 2 System- oder 1 Benutzer-
  Installationen (veränderbar), Abbruch bei Registry-Schreibfehler,
  verbleibenden Zählerstand anzeigen.

Rechts:
- **Einstellungen**: `Produkt Identifikation` als editierbare UUID;
  `Erstellen` generiert `uuid.uuid4()`. Kontaktinfos: Name `%CompanyName%`,
  Webseite `%CompanyURL%`, E-Mail und Telefon. Die Checkbox
  `Kontaktinfos anzeigen` steuert die Editierbarkeit der Kontaktfelder.

Alle neuen Werte stehen optional unter `Sicherheit.settings.validity` in
separaten, typgeprüften JSON-Feldern. Das Sicherheitsformat bleibt v1;
Stage-566/567-Projekte ohne `validity` und `serial_details` bleiben lesbar.
`OK` übernimmt die Werte und löst die vorhandene Projekt-Speicherlogik aus;
`Abbrechen` verwirft nicht übernommene Dialogänderungen und `Hilfe` ruft
das bestehende CHM-Thema `Sicherheit` auf.

**Wichtig:** Stage 568 ist eine Editor-/Konfigurationsänderung. Der fertige
Setup-Laufzeitcode schreibt noch keine Produkt-UUID in die Windows-Registry
und erzwingt derzeit weder Fristen noch Installationsgrenzen oder
Serienregistrierungen. Die zukünftigen Registry-Speicherorte und
Installer-Implementierung werden separat entwickelt.

## Tests

Ausführbar mit:

```sh
python -m unittest -q test_stage566 test_stage567 test_stage568
```

Die Stage-568-Tests decken die abwärtskompatible JSON-Verarbeitung,
Metadatenvalidierung, numerische Grenzwerte, UUID und Projekt-Roundtrip ab.
`test_stage568_qt.py` enthält native PyQt5-GUI-Tests; diese laufen nur, wenn
PyQt5 verfügbar ist. Der vollständige Software-Installer-Testlauf über
`test_stage550` bis `test_stage568` ergab **239 Tests, 41 übersprungen** in
der vorliegenden Umgebung. Die native Sichtkontrolle unter Windows steht aus.
