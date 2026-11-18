# Stage 597 – getrennte EXE/DLL-Projekte, Modulzuordnung und Dark Mode

Verbindliche Quelle: `d64_dism_stage596.zip`.

## Projekt-Informationen

- Das Eingabefeld **Pascal** wurde aufgeteilt in **Pascal EXE** und **Pascal DLL**.
- Neue Eingabefelder **dBASE EXE** und **dBASE DLL** unterhalb der Pascal-Felder.
- Die Eingabefelder BASIC, Prolog, Assembler und Lisp bleiben erhalten.
- Neben jedem Feld befindet sich der vorhandene Verzeichnis-Icon-Button für einen
  Text-Eingabedialog. **OK** übernimmt, **Abbrechen** verwirft die Änderung.
- Die übergeordnete Projekt-ComboBox zeigt für die Profile unterschiedliche
  `Programm: <Name EXE>`- und `Bibliothek: <Name DLL>`-Einträge.
- Die zweite Spalte der TreeList enthält projekt- und zielbezogene Comboboxen,
  z. B. `Pascal: Programm — Foo`, `Pascal: Bibliothek — FooPlugin`,
  `dBASE: Programm — DBApp`, `dBASE: Runtime — DBRuntime`.
- Module- und Unit-Knoten können selbst eine Zuordnung besitzen: eine Vorgabe
  für untergeordnete Blätter. Eine individuelle Blattzuordnung geht vor.
- Die Kopfzeile der TreeList und die Buttons der Namensfelder besitzen
  ausdrücklich getrennte Dark-/Light-Mode-Stile. Die beiden Spalten behalten
  ihren durch den Benutzer veränderbaren Trenner.

## dBASE-Modulknoten

- Unter `dBASE-Programme` steht `Module` als **erster** Unterknoten.
- Das Kontextmenü des Hauptknotens und das Modul-Menü beginnen mit **Neu: Modul**.
- Im Modul-Menü stehen zusätzlich die bestehenden Datei-Anlegeaktionen des
  dBASE-Hauptknotens, Hinzufügen und Einträge löschen zur Verfügung.
- Neue `.prg`-Module werden direkt als Dateiblätter im Modul-Zweig eingefügt;
  sie werden im dBASE-Quelltexteditor geöffnet, nicht als weitere Knoten.
- Die neue Projektdatei-Sektion lautet `Category.dbase.modules`.

## Pascal-Module/Units und Build

- Unter `Pascal-Programme -> Windows PE32 / Windows PE32+ -> Module / Unit`
  stehen die beiden Zieltypen `Pascal: Programm` und `Pascal: Bibliothek` zur
  Auswahl. Jeweils der passende Profilname wird angezeigt.
- Die Kontextmenüs verfügen zusätzlich über **Neu: Modul** bzw. **Neu: Unit**;
  sie legen eine echte, anfänglich minimale `.pas`-Datei im Zweig an.
- Das aktive Projektprofil beeinflusst die Auswahl der zum Build gehörenden
  Pascal-Module und -Units. Die `PROGRAM`/`LIBRARY`-Quellkopfprüfung bleibt
  verbindlich; ein falscher Hauptmodultyp wird nicht stillschweigend umgedeutet.
- Beim Pascal-Windows-Build wählt die übergeordnete ComboBox die EXE-/DLL-Art,
  den Projektquellensatz und den **Dateinamen** des Ausgabeimages. Der interne
  DLL-Linker erhält denselben Namen.
- Die dBASE-EXE-Ausgabe verwendet ebenfalls das gewählte dBASE-EXE-Profil.
  Für `dBASE: Runtime` werden Zuordnung und Name gespeichert. Das bisherige
  eigenständige Runtime-DLL-Buildwerkzeug bleibt bestehen; **beliebige**
  dBASE-`.prg`-Dateien werden nicht fälschlich als DLL kompiliert.

## Rückwärtskompatibilität / Speicherung

- Die Abschnitte `[Project.NamedTargets]` und `[Project.NamedTargetFiles]`
  speichern weiterhin Namen, Zielwahl und Zuordnung.
- Alte `pascal`- bzw. `dbase`-Namen werden, wenn noch keine getrennten
  Felder existieren, initial in beide Zielprofile übernommen.
- Absichtlich leere neue Namen bleiben leer und werden nicht aus den alten
  Feldern zurückgesetzt.
- Alte nur sprachbezogene Blattzuordnungen werden weiterhin akzeptiert.
  Neue Zuordnungen werden als `pascal|program`, `pascal|library`,
  `dbase|program` bzw. `dbase|library` gespeichert.
- Ordner-Zuordnungen verwenden stabile Kennungen der Form
  `@group:pascal:pe32:modules`. Dateizuordnungen sind wie zuvor relativ zur
  Projektdatei speicherbar.

## Prüfungen

- `python -m unittest -q test_stage597`: **8/8** erfolgreich.
- `test_stage596`: **11/11** erfolgreich.
- `test_stage595`: **12/12** erfolgreich.
- `test_stage594`: **10/10** erfolgreich.
- `test_stage593`: **6/6** erfolgreich.
- `test_stage592`: **12/12** erfolgreich.
- Python-Syntax der geänderten Dateien mit lokalem 3.15-Lazy-Import-Fallback
  erfolgreich überprüft.
- Die gepackte ZIP-Datei wurde auf Integrität geprüft.
- Ein nativer GUI-Test mit PyQt5 und Windows-PE32-/PE64-End-to-End-Build ist
  hier nicht erfolgt.
