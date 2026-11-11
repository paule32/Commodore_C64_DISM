# Stage 566 – Software Installer: Sicherheit / Serial Nummer

**Verbindliche Basis:** `d64_dism_stage565.zip`. Alle nicht unten genannten
Dateien werden unverändert in die neue Stage übernommen.

## Oberfläche

- Button **Einstellungen → Sicherheit** öffnet `InstallerSecurityDialog`
  anstelle des generischen Textkonfigurationseditors.
- Einheitliches Installer-Theme (Hell/Dunkel), eigene verschiebbare Titelleiste
  mit Schwarz-Weiß-Verlauf im Dark Mode. Geometrie **620 × 550 Pixel**.
- `QTabWidget` mit **Serial Nummer** und **Zeitdauer**; Zeitdauer wird hier
  ausschließlich als noch leerer Tab angelegt, weil keine Eingabefelder
  spezifiziert wurden.
- **Serial Nummer Liste** mit `QTableWidget`:
  **Listen Name**, **Anzahl**, **Konfiguration**, ohne vertikalen Header;
  horizontal vom Nutzer veränderbare Spaltenbreiten.
- Unter der Tabelle eine gemeinsame Footerzeile: **Hinzufügen**, **Entfernen**,
  **Bearbeiten** links, **OK**, **Abbrechen**, **Hilfe** rechts.
  Listenaktionen sind im Tab "Zeitdauer" ausgeblendet.
- **Hinzufügen/Bearbeiten** öffnen den Kinddialog
  **Serial Nummer - Listen Eigenschaften** (ebenfalls 620 × 550 Pixel).
  Links: Name (`Neue Liste`), `QTreeWidget` mit Checkboxen
  **Alle Konfigurationen → Standard**. Rechts: **Serial Nummern**,
  Split-Menübutton **Kommandos** mit Pfeil und eine einspaltige editierbare
  Tabelle ohne vertikale Zeilennummern.

## Kommandos

- Wiederherstellen / `Ctrl+Z` (letzte Änderung zurücknehmen),
  Rückgängig / `Ctrl+Y` (zurückgenommene Änderung wiederholen).
  Die Bezeichnungen und ihre **vom Auftrag vorgegebenen** Shortcuts bleiben
  genau in dieser Zuordnung, auch wenn diese Kombination in einigen
  Programmen anders benannt wird.
- Erstellen ... / `Ctrl+G`: Dialog zur Anzahl; erzeugt zufällige,
  `secrets`-basierte eindeutige Nummern mit 4 × 4 hexadezimalen Stellen.
- Finden: Textsuche ab nächster Zeile, mit Umlauf.
- Sortieren: alphabetisch, aufsteigend (Groß-/Kleinschreibung ignoriert).
- Ausschneiden / `Ctrl+X`, Kopieren / `Ctrl+C`, Einfügen / `Ctrl+V`,
  Alle auswählen / `Ctrl+A`.
- Alle Nummern löschen / `Ctrl+L`, Selektierte Reihen Löschen / `Ctrl+Delete`,
  Reihe Einfügen / `Insert`, Reihen Einfügen / `Ctrl+Insert`.
- Drucken: Systemdruckdialog; Importieren / Exportieren: UTF-8-Text,
  eine Nummer pro Zeile. Leere Tabellenzeilen werden beim OK verworfen.
- Maximal 100 lokale Rückgängig-Schritte im Kinddialog. Beim Schließen mit
  Abbrechen bleibt die Mutterliste unverändert.

## Projektdaten / Transaktionen

- Im Projekt-JSON ist der neue, **versionierte** Textabschnitt `Sicherheit`:

```json
{
  "version": 1,
  "settings": {
    "serial_lists": [
      {
        "name": "Neue Liste",
        "configurations": ["Standard"],
        "serial_numbers": ["0123-4567-89AB-CDEF"]
      }
    ]
  }
}
```

- `installer_security_settings.py`: strikte Validierung (Namen und Serial
  Nummern innerhalb der Liste eindeutig, Anzahlgrenzen und Textprüfung).
- OK im Kinddialog übernimmt nur in den **Arbeitsspeicher des Elterndialogs**;
  OK in Sicherheit schreibt den Abschnitt und ruft wie bisher
  `save_configuration()` auf. Abbrechen beider Dialoge verwirft ihre
  Änderungen. Alle anderen Projektabschnitte bleiben erhalten.
- Hilfe öffnet das Installer-CHM-Thema **Sicherheit**. Die neue Quellseite
  `help/software_installer/sicherheit.html` wurde in HHP/HHC/HHK und
  HTML-Index registriert. Wenn eine kompilierte CHM genutzt wird,
  muss diese aus dem aktualisierten Projekt neu erstellt werden.

**Grenze dieser Stage:** Es wird die Verwaltung und Speicherung der Listen
implementiert, *nicht* die spätere Serial-Nummern-Prüfung bei der Installation.
Eine Logik für **Zeitdauer** ist noch nicht beschrieben/implementiert.

## Prüfungen

- `test_stage566.py`: Modellvalidierung, Roundtrips, Hilfethemen,
  Schnittstellen und echte Handler-Fallunterscheidungen ohne GUI.
- `test_stage566_qt.py`: optionale PyQt5-Tests (Dialoggeometrie, Tabs,
  Header, Kommandozeilen und CheckBoxen). Unter Windows/mit PyQt5 ausführbar;
  in der aktuellen Laufzeitumgebung mangels PyQt5 übersprungen.
- Ältere Tests Stages 553–565 laufen unverändert.
