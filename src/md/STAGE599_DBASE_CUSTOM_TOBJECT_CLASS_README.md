# Stage 599 – dBASE: `CLASS TObject OF CUSTOM ENDCLASS`

Verbindliche Grundlage: `d64_dism_stage598.zip`.

## Ursache

Der produktive dBASE-PRG-Parser (`d64dbase/compiler.py`) kannte `CLASS/ENDCLASS` bisher nicht als Top-Level-Anweisung. Das Metadatenmodell (`d64dbase/class_model.py`) enthielt gleichzeitig bereits eine eingebaute Klasse `TObject`, die nicht benutzerdefiniert neu registriert werden konnte.

## Implementiert

Die folgenden Formen sind als **leere Klassendeklarationen** im dBASE-PRG-Compiler gültig:

```dbase
CLASS TObject OF CUSTOM ENDCLASS
```

```dbase
CLASS TObject OF CUSTOM
ENDCLASS

CLASS TMyObject OF TObject
ENDCLASS
```

- `CUSTOM` ist ein Marker für eine benutzerdefinierte **Wurzelklasse** ohne Elternklasse, nicht der Name einer Elternklasse.
- Nur ein ausdrückliches `OF CUSTOM` darf die eingebaute `TObject`-Metadatendefinition durch eine benutzerdefinierte Definition ersetzen.
- Bereits vorhandene Ableitungen von `TObject`, `FORM` etc. werden über denselben Klassennamen aufgelöst.
- Deklarationen werden als `DBaseClassDefinition`-Knoten mit Name, Elternklasse, `custom`-Kennzeichen und Quellposition erhalten; sie werden nicht irrtümlich als ausführbare Anweisungen interpretiert.
- Fehlende `ENDCLASS`, doppelte Klassennamen, unbekannte Basisklassen, Vererbungszyklen und verschachtelte Klassen liefern kontrollierte Compilerfehler.
- Der Präprozessor (`#define`, ...), der Kommentarparser, normale PRG-Anweisungen und WFM-Formulare bleiben erhalten.
- Aktualisierte historische ANTLR-Grammatik als Dokumentation; die eigentliche PRG-Implementierung nutzt den Python-Parser.

## Wichtige Grenze

Stage 599 führt **Klassendeklarationen und Klassenmetadaten** ein, nicht vollständige benutzerdefinierte Objekte zur Laufzeit. Objektinstanziierung, VTables, benutzerdefinierte Methodenaufrufe und Speicherverwaltung sind noch nicht als allgemeines PRG-Klassenbackend implementiert. Eine Klassendeklaration mit Methodeninhalt löst deshalb jetzt eine präzise Fehlermeldung aus – Code wird nicht stillschweigend verworfen. Die vorhandenen WFM-/FORM-Verarbeitungswege sind davon unabhängig.

## Tests

- 14 neue Tests in `test_stage599.py`, erfolgreich.
- Bestehende Stage-592-/593-/593-format-/594-/595-/596-/597-/598-Tests einzeln erfolgreich (69 Tests), zusammen 83 Tests.
- PE32 und PE64 Assemblertext für die leere benutzerdefinierte `TObject`-Deklaration erzeugt.
- WFM-Formulartest `CLASS TestForm OF FORM\nENDCLASS` erfolgreich.
- Python-Syntaxprüfung der geänderten Module erfolgreich.

Ein nativer Windows-GUI-/PE-Laufzeittest ist nicht durchgeführt worden; eine allgemeine Klasseninstanziierung ist hier noch nicht implementiert.
