# Stage 686 – Turbo-Hilfe-Blätter öffnen / bool-Rückgabewert absichern

**Verbindliche Basis:** `d64_dism_stage685.zip`.

## Gemeldeter Laufzeitfehler

```text
File "d64_dism.py", line 125924, in _project_turbo_help_open
    editor.load_document(path)
AttributeError: 'bool' object has no attribute 'load_document'
```

Der Stage-685-Aufruf hat lediglich auf `None` geprüft, obwohl eine GUI-/Slot-Variante
von `show_turbo_help_compiler_dock()` einen booleschen Wert zurückgeben kann.
Ein `bool` besitzt keine Methode `load_document`.

## Änderung

`d64_dism.py`, Methode `_project_turbo_help_open()`:

1. Die Quelle wird wie zuvor als echtes `.thlp`-Blatt aufgelöst; fehlende Dateien
   werden mit der bereits verwendeten (Dark-Mode-fähigen) Warnung gemeldet.
2. Nach `show_turbo_help_compiler_dock()` wird nur ein Objekt mit aufrufbarer
   `load_document`-Methode verwendet. Bei booleschem Rückgabewert wird mit
   `_turbo_help_active_editor()` der echte Editor aus dem Fenster- oder
   Dock-Kontext wiedergefunden. Dieser Helper prüft auch auf gelöschte Qt-Wrapper.
3. Falls kein gültiger Editor existiert, erscheint eine Fehlermeldung statt
   einer unbehandelten `AttributeError`.
4. Bereits vorhandene, noch ungespeicherte Hilfe-Tabs werden wieder über die
   Stage-684-Logik in den Vordergrund geholt.
5. Neue Blätter, die Stage 685 beim Hinzufügen auf der Festplatte anlegt,
   durchlaufen denselben abgesicherten Öffnungspfad.

Die verschachtelte Projektbaumstruktur, Haupt-Eintrag-Markierung,
Turbo-Hilfe-Suchpfade, Includes, F2-Kompilierung sowie bestehende Compiler-
und Linker-Funktionen bleiben unverändert.

## Geänderte Dateien

- `d64_dism.py` – abgesicherte Editorauflösung für Turbo-Hilfe-Blätter
- `test_stage658.py` – einen alten Test-Fake auf das in Stage 685 geänderte
  Anlegen echter `.thlp`-Dateien aktualisiert; die Fehlerschutz-Assertion bleibt bestehen
- `test_stage686.py` (neu) – Tests für Boolean-Slot-Rückgaben,
  neues Projektblatt, fehlenden Editor und nicht vorhandene Quelldatei
- `STAGE686_TURBO_HELP_BOOL_EDITOR_OPEN_FIX_README.md` – diese Dokumentation

## Prüfung

```sh
python -m pytest -q \
    test_stage686.py test_stage685.py test_stage684.py test_stage683.py \
    test_stage662.py test_stage658.py test_stage654.py
```

Ergebnis in der Entwicklungsumgebung: **37 bestanden**.
Die native Qt5-Oberfläche unter Windows konnte hier nicht visuell ausgeführt werden.
