# Stage 688 – Turbo Hilfe: Projektlokaler Settings-Tab und PO/HLP-Header

**Verbindliche Basis:** `d64_dism_stage687.zip`.

## Bedienung

Ein Klick auf den Projekt-Informationen-Hauptknoten **Turbo Hilfe** öffnet
im vorhandenen Hilfecompiler-Dock den Tab **Settings** (auch bei Doppelklick).
Die Formularfelder sind am Tab `Localize PO/MO → Settings` orientiert:

- `Input file (*.po)` – Pfad zum erzeugten, editierbaren PO-Katalog.
- `Output file (*.hlp)` – Pfad zum erzeugten GNU-gettext-Hilfekatalog.
- `Project-Id-Version`, `Report-Msgid-Bugs-To`, `POT-Creation-Date`,
  `PO-Revision-Date`, `Last-Translator`, `Language-Team`, `Language`,
  `MIME-Version`, `Content-Type`, `Content-Transfer-Encoding`.

Die **ersten Werte** entsprechen den initialen Localize-Headern bzw. den
zugehörigen `QSettings`-Einträgen `localize/header/*`. Nach einer Änderung
werden sie **nur für das aktuelle Projekt** geführt; der Localize-Dialog
wird nicht umkonfiguriert.

Wenn die beiden Dateipfade nicht ausdrücklich geändert wurden, folgen sie
dem aktuell markierten **Haupt-Eintrag**. Beispiel:

```
Haupt-Eintrag: Tutorials/Main.thlp
Input file:     Tutorials/Main.po
Output file:    Tutorials/Main.hlp
```

Bei projektspezifischen relativen Pfaden wird das Verzeichnis der `.pro`-Datei
als Bezugspunkt verwendet. Die Pfade werden als projekt-relative Angaben
serialisiert, wo dies möglich ist.

## Projektpersistenz

Die Projektdatei enthält die zusätzliche Sektion
`[Settings.TurboHelp.PO]` mit JSON im `Values`-Feld, einschließlich der
Headerwerte sowie der explizit eingestellten PO- und HLP-Dateipfade.
Sie wird beim Projektladen gelesen und beim Speichern geschrieben. Änderungen
markieren das Projekt wie andere Einstellungen als modifiziert. Bestehende
Projekte ohne diese Sektion erhalten automatisch die initialen Werte.

## F2 und Linker

Der Projekt-Hilfecompiler verwendet diese Header für die `msgid ""`-Sektion
in der erzeugten `.po`-Datei. Beim Aufbau des binären Hilfekatalogs werden
die gleichen Header als gettext-Metadaten übernommen. Das Dateiformat der
`.hlp` bleibt unverändert: **GNU gettext, intern MO-Format, mit der Endung
`.hlp`**.

**Es wird keine separate `.mo`-Datei gespeichert.** Eine explizit benannte
`Output file (*.hlp)` wird als HLP geschrieben. Da das vorhandene F1-System
den Katalog weiterhin als `<Programmname>.hlp` neben der EXE erwartet,
wird der gleiche Inhalt bei abweichendem Ausgabepfad zusätzlich dorthin
deployt. Bei gleichem Pfad erfolgt nur ein Schreibvorgang.

Alte Projekte, die keine neuen PO/HLP-Einstellungen verwenden, behalten
beim direkten `compile_help_sources`-Aufruf ihre bisherigen Standardausgaben
(`<EXE-Name>.po` und `<EXE-Name>.hlp`).

## Prüfungen

- Gezielte Tests prüfen Localize-Defaultwerte, .pro-Einbindung,
  Hauptdokument-Ableitung, geänderte Verzeichnisse, Header-
  Roundtrip, GNUTranslations-Lesen und das Nicht-Erzeugen von `.mo`.
- Bestehende Tests der Stages 683–687 werden zusätzlich ausgeführt.
- Ein nativer PyQt5-Windows-Laufzeittest steht noch aus.
