# Stage 654 – Turbo Help: Projektblatt ohne Editor-AttributeError öffnen

**Verbindliche Basis:** `d64_dism_stage653.zip`.

## Gemeldeter Fehler

Beim Anklicken eines `.thlp`-Blatts unter `Projekt-Informationen → Turbo Help`
meldet `ExplorerWindow._project_turbo_help_open()`:

```
AttributeError: 'ExplorerWindow' object has no attribute 'turbo_help_compiler_editor'
```

In Stage 653 wurden Dock und Editor in `show_turbo_help_compiler_dock()` nur
im Zweig `if dock is None:` angelegt. Bei bereits existierendem Dock und
fehlendem Editor-Attribut wurde anschließend dennoch direkt auf
`self.turbo_help_compiler_editor.load_document(...)` zugegriffen.

## Korrektur

Die Änderungen betreffen ausschließlich `d64_dism.py`:

1. `ExplorerWindow.__init__()` initialisiert
   `self.turbo_help_compiler_dock` und `self.turbo_help_compiler_editor` explizit
   mit `None`.
2. `show_turbo_help_compiler_dock()` prüft die Existenz **beider** Objekte.
   Besteht das Dock bereits, gewinnt es den vorhandenen `TurboHelpEditor`
   über `dock.widget()` zurück. Besteht nur das Dock ohne verwendbaren Editor,
   wird ein Editor erzeugt und mit dem Dock verbunden. Besteht der Editor
   ohne Dock, bleibt der Editor mitsamt Tabs erhalten und wird erneut eingehängt.
3. Die Methode gibt den gültigen Editor zurück. `_project_turbo_help_open()`
   und `_project_turbo_help_new()` benutzen diese Rückgabe statt eines
   ungeprüften Attributzugriffs.
4. Die aktuelle Projektliste wird beim Öffnen synchronisiert, ohne bereits
   geladene `.thlp`-Dateien doppelt als Tabs einzufügen (Deduplikation durch
   `TurboHelpEditor.load_document()`).
5. Beim Entfernen eines ungespeicherten Projektblatts wird der Editor
   ebenfalls sicher ermittelt.

Unverändert: `libd64_qt5.dll`, `App.hlp`-Format, F1-Navigation, F2-Kompilierung,
und das Verbot eines externen `turbo_help_host.exe`.

## Tests

- `test_stage654.py`: **5 erfolgreich**; echte `ExplorerWindow`-Methoden werden
  aus dem Source extrahiert und mit Qt-kompatiblen Test-Doubles aufgerufen:
  * Erster Blattklick vor Erzeugung des Hilfe-Docks.
  * Wiederholter Klick erzeugt weder ein zweites Dock noch einen zweiten Editor.
  * Bestehendes Dock ohne Editor-Attribut verwendet das bereits enthaltene
    Editor-Widget weiter.
  * Bestehendes Dock ohne Editor-Widget erzeugt und bindet einen Editor.
  * Fehlende `.thlp`-Datei zeigt eine Fehlermeldung, ohne einen Editor zu starten.
- `test_stage650.py` bis `test_stage653.py`: **25 erfolgreich**.
- Hauptquelltext nach Test-Normalisierung der Python-3.15-`lazy`-Imports
  ohne Syntaxfehler kompiliert.

**Einschränkung:** Ein nativer Windows-/PyQt5-GUI-Test war in der
Linux-Testumgebung ohne PyQt5 nicht möglich.

## Installation

Den vollständigen Stage-654-Quellstand anstelle von Stage 653 verwenden,
oder nur die geänderte `d64_dism.py` übernehmen. Ein Neubau der Qt5-Bridge
ist **nicht erforderlich**.
