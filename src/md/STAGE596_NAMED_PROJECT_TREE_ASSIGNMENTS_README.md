# Stage 596 – Benannte Projekte, Projektart und Datei-Zuordnung

**Verbindliche Basis:** `d64_dism_stage595.zip` (unverändert, soweit nicht unten aufgeführt).

## Benutzeroberfläche

Im Dock **Projekt / Informationen** auf dem Tab **Projekt** gibt es direkt
oberhalb der Projekt-TreeList eine Zeile **Projektname:** mit einer ComboBox.
Jeder nichtleere Sprach-Projektname wird zweimal aufgeführt:

- `Programm: Foo`
- `Bibliothek: Foo`

Bei gleichen Namen in unterschiedlichen Sprachen bleiben die Einträge intern
über ihre Sprach-ID getrennt; ein Tooltip zeigt die betreffende Sprache.

Unterhalb der TreeList befinden sich fünf direkt editierbare Projektfelder:
`BASIC:`, `Pascal:`, `Prolog:`, `Assembler:`, `Lisp:`. Jeder Eintrag hat rechts
neben der Eingabezeile einen Ordner-Button. Dessen Dialog enthält eine
Textzeile mit dem bisherigen Namen; `OK` übernimmt den neuen Namen,
`Abbrechen` lässt die Daten unverändert.

Die TreeList besitzt die Spalten `Datei` und `Projekt`. Die zweite Spalte
enthält für tatsächliche Dateiblätter eine ComboBox mit
`– nicht zugeordnet –` und den fünf benannten Projekten. Auch verschachtelte
BASIC-, Pascal-, Prolog-, Ressourcen- und andere Projektblätter werden
berücksichtigt. Interne Breakpoint-/Bookmark-Zeilen bekommen keine
Projektzuordnung. Die beiden Spalten können über die Trennlinie im
TreeList-Kopf unabhängig verbreitert oder verschmälert werden.

## Persistenz / ältere Projekte

Die vorhandenen `Category.*`-Sektionen bleiben erhalten. Neu hinzu kommen

- `[Project.NamedTargets]` mit `Names` (JSON) und `Selection` (JSON),
- `[Project.NamedTargetFiles]` mit einer JSON-Referenz pro zugeordnetem Blatt.

Die Sprache (`basic`, `pascal`, `prolog`, `assembler`, `lisp`) ist die stabile
Projekt-ID. Das Umbenennen eines Projekts löst deshalb die Zuordnungen nicht
auf. Dateireferenzen werden relativ zur `.pro`-Datei gespeichert und beim
Öffnen wieder auf absolute Pfade umgesetzt. Werden Quellen aus dem Baum
entfernt, entfernt der nächste Speichervorgang deren verwaiste Referenzen.
Alte Projekte ohne diese Sektionen laden mit leeren Namensfeldern und
unveränderter bisheriger Buildfunktion.

## Buildintegration

- **F2 im Projektbaum** kompiliert bei aktiver Auswahl nur markierte Blätter,
  deren zweite TreeList-Spalte dem aktiven benannten Projekt entspricht.
- **Pascal-Projektbuild** filtert sowohl Module als auch Units auf die
  Zuordnung des gewählten Pascal-Projekts und verwendet den oben
  ausgewählten Typ `Programm`/`Bibliothek` für den vorhandenen
  Pascal-`PROGRAM`/`LIBRARY`-Build. Ein expliziter Quellkopf mit der falschen
  Art wird nicht als DLL/EXE umgedeutet, sondern erzeugt eine Fehlermeldung.
- **F2-Objekt-/EXE-Link für andere unterstützte Quellsprachen:** Bei
  vorhandener Projektzuordnung werden nicht stillschweigend weitere
  Dateiblätter aus einem anderen benannten Projekt in denselben Link
  übernommen. Wo die jeweilige Sprache bereits `program`/`library` als
  Quellart unterstützt, wird diese mit der gewählten Buildart abgeglichen.
- Ein als `Bibliothek` bezeichnetes Projekt erzeugt nicht allein deshalb
  gültige DLL-Exporte: Bei Sprachen ohne vorhandene DLL-Codegenerierung
  bleibt die entsprechende Compiler-Unterstützung Voraussetzung.

## Einschränkungen und Prüfstatus

Die grafische Oberfläche kann hier nicht nativ unter Windows mit PyQt5
getestet werden; das CI-Environment enthält kein PyQt5. Die neuen
Metadaten- und GUI-Callback-Regressionsfälle laufen ohne Qt über AST und
Mockobjekte. Die Hauptdatei enthält Python-3.15-spezifische `lazy import`-
Syntax und wurde für die lokale Syntaxkontrolle entsprechend transformiert,
ohne den Originalquellcode zu ändern. Native Linktests stehen ebenfalls aus.

## Änderungen

- `d64_dism.py` – Zwei-Spalten-TreeList, Projektfeld-Editoren, Dialog,
  ComboBox-Synchronisation, `.pro`-Integration und Buildscope.
- `project_named_targets.py` – Python-3.11+-kompatible pure Hilfsfunktionen
  für Namen, IDs, Dateischlüssel und INI-Roundtrip.
- `test_stage596.py` – neue Regressionstests.
