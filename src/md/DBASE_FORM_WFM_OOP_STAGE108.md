# Stage 108 – dBase WFM / FORM-OOP / Shadow-Rectangle

## Designer

- `Border -> Shadow Color` zeichnet den harten Schatten als gefülltes Rechteck hinter der Designer-Komponente.
- Die vorhandene Shadow-Position/Offset-Logik bleibt erhalten.
- `Border -> Color` und `Border -> Shadow Color` besitzen jeweils einen `...`-Button für `QColorDialog`.
- Die gewählte Custom-Farbe wird in die ColorComboBox übernommen und sofort angewendet.

## WFM-Dateien

`*.wfm` ist jetzt das Designer-Dateiformat für dBase-Formulare.

Beim Öffnen einer WFM-Datei wird der OOP/Form-Quelltext geparst und in die Graphics Scene übertragen. Beim Speichern wird die aktuelle Form wieder als dBase-OOP-Quelltext geschrieben.

Unterstützte Kernsyntax der ersten FORM-Stufe:

- `PARAMETER` / `LOCAL`
- `B = NEW ParentForm(...)`
- `B.Init(...)` / `B.Open()`
- `CLASS <Name> OF FORM` / `ENDCLASS`
- `PROPERTY name = value`
- `THIS.Property = value`
- `WITH (THIS)` und `WITH (THIS.Control)` / `ENDWITH`
- `THIS.Control = NEW PUSHBUTTON(THIS)`
- `THIS.Container = NEW CONTAINER(THIS)`
- verschachtelte Controls wie `THIS.Container1.PushButton1`
- `NEW FONT("Arial", 12, .T., .T., .T.)`
- `Font.bold`, `Font.italic`, `Font.underline`, `Font.stroke`
- Event-Zuweisungen wie `onClick`, `onMouseMove`, `onMouseRButton`
- `.T.` / `.F.`, Strings, Integer und Float

PUSHBUTTON und CONTAINER bilden den initialen Runtime-Kern. Der Designer-Mapper ist bereits so aufgebaut, dass weitere Komponenten aus der linken Komponentenleiste ergänzt werden können.

## Compiler

`d64dbase.py` enthält die neue Stage-34-WFM-Erweiterung. Normale dBase-Programme laufen weiterhin durch den bisherigen Compilerpfad. Wird `CLASS ... OF FORM` erkannt, wird der FORM-OOP-Pfad verwendet.

Der FORM-Pfad erzeugt für PE32 und PE32+ Aufrufe für:

- `DBaseQtFormCreate`
- `DBaseQtControlCreate`
- `DBaseQtWidgetSetGeometry`
- `DBaseQtWidgetSetText`
- `DBaseQtWidgetSetBackColor`
- `DBaseQtWidgetSetBorderColor`
- `DBaseQtWidgetSetBorderWidth`
- `DBaseQtWidgetSetRadius`
- `DBaseQtWidgetSetFont`
- `DBaseQtFormOpen`

## Qt5-Runtime

Die mitgelieferten `d64qt5_bridge.cpp/.h/.def/.pro` enthalten die dazugehörigen neuen C-ABI-Exports. Die bestehende `d64qt5.dll` muss aus diesen Quellen neu gebaut werden, damit ein kompiliertes WFM-Programm die neuen FORM-Funktionen auflösen kann.

## Noch bewusst offen

Event-Eigenschaften (`onClick`, `onMouseMove`, `onMouseRButton`, …) werden bereits geparst, im Designer erhalten und beim Speichern wieder ausgegeben. Die native Callback-Dispatch-/Methodenbindung ist in dieser ersten FORM-Stufe noch nicht aktiviert. Das ist der nächste logische Runtime/OOP-Schritt.

Ebenso werden unbekannte zukünftige Komponenten im WFM-Modell bereits toleriert; die native Runtime-Unterstützung wird schrittweise auf die komplette linke Komponentenliste erweitert.

## Tests

- Python-Syntaxprüfung für `d64_dism.py` und `d64dbase.py`
- Exaktes Benutzer-Template geparst
- verschachtelter `CONTAINER` geprüft
- `NEW FONT` und boolesche Font-Werte geprüft
- PE32 FORM-Codegenerierung geprüft
- PE64 FORM-Codegenerierung geprüft
- Legacy-dBase-Compilerpfad geprüft
- statische GUI-/Runtime-Schnittstellenprüfungen durchgeführt

Eine native visuelle PyQt5/Qt5-Ausführung war in der Testumgebung nicht verfügbar.
