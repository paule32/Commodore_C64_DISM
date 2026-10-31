# Stage 499 – Quellstruktur, Ereignisprozeduren und Komponentenpanel

**Verbindliche Grundlage:** `d64_dism_asm_498.zip`.

## Quellstruktur im WFM-Editor

- Unter **Prozeduren** erscheint `__init__` vor `__del__`, anschließend werden alle anderen Prozeduren alphanumerisch und unabhängig von Groß-/Kleinschreibung sortiert.
- Unter **Funktionen** erscheint `__main__` zuerst; alle übrigen Funktionen werden ebenso alphanumerisch sortiert.
- Zahlen werden natürlich sortiert: `Button2_onClick` erscheint vor `Button10_onClick`.
- Die Zuordnung von `Qt.UserRole` zur ursprünglichen Quellzeilennummer wird nicht verändert; Navigation in den Editor führt weiterhin zur tatsächlichen Deklaration.
- Globale Variablen bleiben in ihrem bisherigen Verhalten unverändert.

## Ereignisprozeduren anlegen

- Ein neuer Event-Handler wird beim Erstellen zwischen die alphabetisch sortierten vorhandenen Event-Handler einsortiert, statt grundsätzlich am Schluss der Methodenliste zu landen.
- Das gilt beispielsweise für `Button1_onLostFocus`, `Button2_onClick` und `Button10_onClick`, auch wenn die zugehörigen Methoden zuvor in anderer Reihenfolge erstellt wurden.
- Bestehende *nicht* zu den Ereignissen gehörende Methoden behalten ihre relative Reihenfolge; bestehende `source_lines` und Methodenrümpfe werden nicht geändert.
- Neben dem üblichen Muster `<Komponente>_on<Ereignis>` werden per `CLASS::` explizit gebundene benutzerdefinierte Eventnamen berücksichtigt.
- Doppelte Prozedurdeklarationen werden unabhängig von Groß-/Kleinschreibung verhindert. Beim erneuten Doppelklick auf einen existierenden Handler wird die bestehende Methode geöffnet.
- Die Umordnung der Ereignismethoden findet nur bei einer **neuen** vom Designer angelegten Eventmethode statt, **nicht** bei einer reinen Aktualisierung der TreeList.

## Linkes Komponenten-/Eigenschaftenpanel

- `show_dbase_form_designer()` verwendet im horizontalen `resizeDocks`-Aufruf 340 statt 330 Pixel für die linke Palette samt Eigenschaften/Ereignissen. Die Breite des rechten Designer-Docks wird weiterhin durch den verfügbaren Raum bestimmt.
- Vom Benutzer anschließend manuell geänderte Dock-Größen bleiben von der Änderung unberührt, bis der Formular-Designer erneut aufgerufen wird.

## Betroffene Dateien

- `d64_dism.py`: Quellstruktur-Aufbau, Event-Erzeugung, Standardbreite der linken Spalte.
- `d64dbase/form_method_order.py`: Qt-unabhängige Sortierschlüssel und Einfügelogik.
- `test_stage499_wfm_outline_event_order_panel_width.py`: 9 neue Tests für Sortierung, Zeilenbezug und Einfügen.

## Testumfang und Grenzen

- 38 Tests: Stage 499 sowie angrenzende Stage-494-/495-/498-Tests bestanden.
- 35 weitere WFM-/Assembler-Editor-Tests (Stages 467, 468, 469, 473 und 474) bestanden.
- Ein zusätzlicher alter Build-Ziel-Testlauf erreichte das Zeitlimit und wurde nicht als bestanden gewertet.
- Python-Syntax und ZIP-Integrität wurden separat geprüft.
- Der Qt5-Formular-Designer konnte in der Testumgebung mangels PyQt5 nicht interaktiv per Mausklick geprüft werden.
