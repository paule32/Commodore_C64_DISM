[Deutsch](STAGE494_WFM_EVENTS_ONGOTFOCUS_NAVIGATION.md) | [English](STAGE494_WFM_EVENTS_ONGOTFOCUS_NAVIGATION.en.md)

# Stage 494 – OnGotFocus und Doppelklick auf WFM-Ereignisprozeduren

Grundlage: Stage 493 (`d64_dism_asm_493.zip`).

## Eigenschaften-Panel → Ereignisse

- Die linke Ereignisliste zeigt **OnGotFocus** statt **OnGetFocus**.
- Vorhandene Formulare mit `OnGetFocus` behalten die hinterlegte Prozedurzuordnung; beim Einlesen und beim nächsten Schreiben wird die Bezeichnung zu `OnGotFocus` migriert. Existiert auch eine aktuelle `OnGotFocus`-Bindung, bleibt diese maßgeblich.
- Die rechte Spalte **Prozedur** schlägt automatisch `<Komponentenname>_onClick`, `<Komponentenname>_onGotFocus` usw. vor. Bereits eingetragene Namen bleiben erhalten. Timer verwenden weiter die etablierte `OnTimer<N>`-Benennung.
- Ein Doppelklick direkt auf das noch leere Feld übernimmt den sichtbaren Placeholder, bindet `CLASS::<Prozedurname>` an das Ereignis, aktiviert die Navigationsschaltfläche und öffnet die entsprechende Quellcode-Position.
- Existiert die Methode noch nicht, legt der Designer sie wie folgt innerhalb der WFM-Klasse an:

  ```dbase
  procedure PushButton1_onClick(Sender)
      /* Event Code */
      return
  ```

- Existiert die Methode bereits, wird **keine zweite Methode** angelegt. Stattdessen navigiert der Editor zur vorhandenen `PROCEDURE`-/`FUNCTION`-Deklaration, wobei Groß-/Kleinschreibung nicht unterschieden wird.
- Bei unvollständig bearbeiteten Quelltexten, die eine Methode bereits enthalten, aber nicht parsebar sind, wird die ursprüngliche Stelle angesprungen, statt Quelltext zu überschreiben.
- Bereits im WFM-Editor verfasste Methodeninhalte bleiben erhalten; der neu erzeugte Eintrag wird vor dem erneuten Quelltext-Rendern nicht aus dem alten Editorstand überschrieben.
- `Sender` ist für die jeweilige Plattform die vom WFM-Runtime-Code übergebene Objekt-/Handle-Information; die tatsächlichen Laufzeitfunktionen hängen vom entsprechenden Windows- bzw. Linux-Backend ab.

## Dateien

- `d64_dism.py`: Ereignisname, Placeholder-Doppelklick, Migration und Quellcode-Navigation.
- `d64dbase/form_event_handlers.py`: unabhängig von Qt testbare Hilfsfunktionen zur Normalisierung und Suche.
- `test_stage494_wfm_focus_event_navigation.py`: Regressionstests für Legacy-Migration, Placeholder, neue/alte Methoden, korrekte Quellcodepositionen.

## Prüfung

- Python-Syntax mit `py_compile`.
- 12 neue Stage-494-Tests erfolgreich.
- 38 bestehende ausgewählte WFM-Regressionstests erfolgreich.
- `parse_dbase_wfm` erkennt die erzeugte `OnGotFocus`-Bindung und `Sender`-Prozedur.
- Native Qt5-GUI-Mausbedienung kann auf der Testumgebung ohne PyQt5 nicht interaktiv geprüft werden.
