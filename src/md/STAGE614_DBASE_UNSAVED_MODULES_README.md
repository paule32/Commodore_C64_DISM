# Stage 614 – dBASE-Module als ungespeicherte Editorblätter

Verbindliche Basis: `d64_dism_stage613(1).zip`. Die vorhandenen Compiler-,
Assembler-, Debug- und Projektfunktionen wurden nicht ausgetauscht.

## Benutzeroberfläche

- Im Kontextmenü von **dBASE Programme**, den direkten dBASE-Unterknoten,
  dBASE-Dateiblättern sowie dBASE-Windows-Ressourcenknoten steht als ERSTER
  Eintrag **Neu:  Module**.
- Ein Klick erzeugt einen leeren dBASE-Quelltexteditor und ein neues Blatt unter
  **dBASE Programme → Module**: `unbenannt.prg`, bei Namenskollision
  `unbenannt_1.prg` usw.
- Das Blatt ist zunächst eine reine Speicherreferenz. Es existiert noch keine
  `.prg` auf dem Datenträger; auch die `.pro`-Datei speichert keinen Phantompfad.
- Der Tab zeigt `[Speichern unter ...]`, das Blatt einen Hinweis beim Überfahren
  mit der Maus. Das Blatt verfügt rechts über dieselbe Projekt-Zuordnungs-
  Dropdown-ComboBox wie andere Projektdateien; der Benutzer kann sein Projekt
  dort bei vorhandenen Projektprofilen wählen.
- Beim ersten **Strg+S** oder **Speichern unter ...** öffnet sich ein Dialog
  für eine neue `.prg`-Datei. Die Wahl einer bereits existierenden Datei wird
  zurückgewiesen. Erst ein erfolgreiches Speichern setzt Dateipfad und
  Projektzuordnung, entfernt das Flag und persistiert den Dateieintrag.
- Solange das aktive Modul ungespeichert ist, fordert ein Wechsel auf eine
  andere Projektdatei bzw. eine andere projektverändernde Kontextmenüaktion
  das Speichern an. Beim Schließen gilt wie bisher **Speichern / Verwerfen /
  Abbrechen**. Verwerfen entfernt das vorläufige Blatt.
- Rechtsklick auf ein vorläufiges Modul bietet zusätzlich **Speichern unter ...**.

## Ausgabe

Das Modul selbst erzeugt beim Anlegen keine Programmausgabe. Statusmeldungen
laufen über das vorhandene IDE-Protokoll. Die bisherige dBASE-Ausgabe der
kompilierten Qt5-Anwendung in deren DOS-/DEBUG-Ausgabekanälen wird nicht
verändert. Es wird kein weiteres Ausgabefenster angelegt.

## Tests

- `test_stage614.py`: 8 Qt-unabhängige Tests (Erzeugung, Namen, Editorprofil,
  Dropdown-Zuordnung, Save-As, kein Überschreiben, Abbruch, Kontextmenüs).
- Unveränderte Tests von Stages 597, 598, 601: 24 Tests erfolgreich.
- Unveränderte Tests von Stage 613: 7 Tests erfolgreich.
- Vollständiger Python-3.13-Syntaxcheck nach Ersatz der zwei originalen
  Python-3.15-`lazy from`-Zeilen in einem **flüchtigen Prüfstring** erfolgreich.
  Die gelieferten Quellen enthalten weiterhin die Original-`lazy`-Imports.
- Eine native GUI-Integration unter Windows/Python 3.15 bleibt zu überprüfen,
  da PyQt5 und Python 3.15 in der Testumgebung nicht verfügbar waren.
