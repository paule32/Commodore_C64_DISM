# Stage 457 – Resource Editor Menü, Dock-Workspace und RC-Vorlagen

**Verbindliche Basis:** `d64_dism_asm_456.zip`.

## Werkzeugmenü

Im Hauptmenü **Werkzeuge** steht unmittelbar oberhalb des vorhandenen Eintrags
**Resource Builder** der neue Eintrag **Resource Editor**. Die Aktion ruft den
bereits existierenden Windows-Ressourcen-Editor auf. Sie übergibt ausdrücklich
keinen `QAction.triggered`-Boolean an die `path`-Argumentstelle.

## Docking-Verhalten

Wenn das Resource-Editor-Dock sichtbar wird, werden alle anderen *zu diesem
Zeitpunkt sichtbaren* Docking-Fenster ausgeblendet, **außer** dem Dock
**Projekt / Informationen** (`right_dock`). Dies gilt auch bei anderen
Öffnungswegen, etwa über Projekt- und Kontextmenüs. Das Protokoll-Dock ist
**keine** Ausnahme. Auch die bisher sichtbare zentrale Arbeitsfläche wird
vorübergehend ausgeblendet.

Beim Schließen des Editors werden nur die zuvor sichtbaren Docks und die
zuvor sichtbare zentrale Arbeitsfläche wieder angezeigt. Zuvor versteckte
Docks bleiben versteckt. Eine bereits versteckte Projekt-/Infoansicht wird
nicht erzwungen sichtbar gemacht. Die Wiederherstellung ist idempotent.

## Ressourcenvorlagen

Unterhalb der bestehenden Leiste `RC → RES`, `COFF32`, `COFF64` und
`Aktualisieren` folgt eine eigene Leiste mit **Dialog**, **Text**, **Icon**,
**Bitmap**, **Cursor**, **RCDATA**. Alle sechs Aktionen fügen RC-Quelltext an
der Cursorposition der Registerkarte `RC-Quelltext` ein.

- **Dialog:** direkt übersetzbare `DIALOGEX`-Vorlage mit Titel, Font,
  statischem Text, OK- und Abbrechen-Schaltfläche.
- **Text:** `STRINGTABLE`-Block mit eindeutiger numerischer ID.
- **Icon, Bitmap, Cursor:** klassische RC-Dateiverweise (`.ico`, `.bmp`,
  `.cur`). Die Bilddateien müssen im gleichen Verzeichnis liegen oder
  die Dateiverweise müssen angepasst werden.
- **RCDATA:** ein kompilierbarer Beispieldatenblock.

Wiederholte Dialogeinfügungen erhalten eigene IDs (`IDD_DIALOG_1`,
`IDD_DIALOG_2`, ...). Das zugehörige Modulpaar ist
`resource_rc_templates.py` und `WindowsResourceEditorWidget.insert_resource_template`
in `d64_dism.py`. Der Text wird im Editor als geändert gekennzeichnet und
kann regulär als `.rc` gespeichert werden. Für schreibgeschützte binäre
`.res`-Dateien wird keine Änderung durchgeführt.

## Prüfungen

- `python -m py_compile d64_dism.py resource_rc_templates.py`
- `python -m pytest -q test_stage457_resource_editor_menu_workspace_templates.py`
  (14 Tests bestanden)
- `python -m pytest -q test_stage457_resource_editor_menu_workspace_templates.py
  test_stage442_roman_numerals_fact.py test_stage444_roman_columns_darkmode.py`
  (24 Tests bestanden)
- Tatsächliches Parsen und Kompilieren von `DIALOGEX`, `STRINGTABLE` und
  `RCDATA` über den internen RC-Compiler (ohne PyQt-Abhängigkeit).

Die tatsächliche Qt5-Fensterdarstellung auf Windows wurde hier nicht
visuell getestet.

## Zusatzkorrektur – Absturz beim Öffnen zuletzt verwendeter Projekte

Stage 456 konnte beim Öffnen eines letzten Projekts folgenden Fehler auslösen:
`RuntimeError: wrapped C/C++ object of type QTabWidget has been deleted`
bei `DBaseTableDesignerWidget.set_project_column_widths()`.

**Ursache:** Beim Verlassen des Tabellen-Workspaces entfernte
`_unmount_dbase_table_designer_central()` die zentrale Tabellen-Designer-Seite
mittels `removeTab()` und stellte sie anschließend mit `page.deleteLater()`
zur Löschung an. Die Referenz `dbase_table_designer_widget` blieb bestehen;
beim nächsten Projekt-Laden griff die Anwendung dadurch auf ein bereits von
Qt gelöschtes `table_tabs` zu.

**Korrektur:** `removeTab()` und `hide()` bleiben bestehen, die Seite wird aber
bei temporärem Workspace-Wechsel nicht mehr gelöscht. Der Designer und die
enthaltenen Tabellen-Tabs werden beim nächsten Öffnen weiterverwendet.
Dies verhindert auch den Verlust noch geöffneter Tabellen beim Wechsel zwischen
Arbeitsbereichen. Die tatsächliche Freigabe erfolgt mit dem Besitzer beim
Beenden der Hauptanwendung.

**Test:** `test_stage457_dbase_designer_reopen.py` führt dreimal das
Abmelden/Wiederanmelden des zentralen Tabellen-Workspaces durch, nutzt dabei
die echte Python-Methode `set_project_column_widths` mit einem simulierten
Qt-Objektlebenszyklus und stellt sicher, dass kein `deleteLater()` aufgerufen
wird. Test erfolgreich. Ein nativer Windows-PyQt5-Laufzeittest steht aus.
