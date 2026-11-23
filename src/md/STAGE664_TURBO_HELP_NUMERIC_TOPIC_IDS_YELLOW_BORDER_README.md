# Stage 664 – Turbo Vision Help: numerische Themennummern und DOS-Fensterlayout

**Verbindliche Basis:** Stage 663. Die Korrektur setzt ausschließlich auf dem bestehenden
Python-Helpcompiler und `libd64_qt5.dll` auf; `turbo_help_host.exe` wird nicht benötigt.

## 1. Themen mit frei wählbarer Hilfenummer

Das `.thlp`-Makro `%topic` akzeptiert wie zuvor Themen **ohne Nummer** und jetzt
zusätzlich eine **optionale dezimale 32-Bit-Hilfenummer** (0 bis 4294967295).
Die Nummer bezeichnet **nicht** den internen GNU-MO-Index oder Datei-Offset.
Sie ist innerhalb eines vollständig kompilierten Projekts eindeutig; doppelte
Nummern in verschiedenen `.thlp`-Dateien oder `%include`-Dateien sind Fehler.

**Beispiel `System.Help.thlp`:**

```text
%topic "index"
%anchor #abschnitt1
<b>Hauptmenü</b>
%link 1234
%link "test"

%topic "test" 1234
<anchor id="beispiel"></anchor>
<b>Dies</b> ist das Hilfethema mit der Nummer 1234.
%ref "index" #abschnitt1

%topic "anderes Thema" 5678
Text eines weiteren Themas.
```

Auch `%ref 1234 #beispiel` ist möglich. Für Definitionen eines Ankers wird
weiterhin das Makro `%anchor #beispiel` unterstützt. Vorhandene Makros ohne
Nummern behalten ihr bisheriges Verhalten.

## 2. GNU-PO-/MO-Ausgabe (ohne proprietäre Dateifelder)

Ein PO-Eintrag darf ein offizielles `msgctxt` besitzen. Würde man `msgctxt` direkt
an `msgid "test"` hängen, änderte sich aber der übliche gettext-Schlüssel.
Darum erzeugt der Compiler **zwei** reguläre GNU-PO-Einträge:

```po
msgid "test"
msgstr "<b>Dies</b> ist das Hilfethema mit der Nummer 1234."

msgctxt "turbo-help-id"
msgid "1234"
msgstr "test"
```

Der erste Eintrag bewahrt die Suche über den Themennamen. Der zweite ist ein
**Alias von der Hilfenummer auf den Themennamen**. Im GNU-MO-Format lautet
der Schlüssel für einen Kontext-Eintrag intern
`turbo-help-id` + Byte `0x04` + `1234`; der Wert ist der Themenname `test`.
Es gibt keine separate Hilfedatei und keine Kopie des eigentlichen Hilfetexts.
Die normale GNU-MO-Sortiertabelle/Offsetberechnung bleibt unverändert.

**Python-Direktzugriff** (liest `AppDB.hlp` als regulären GNU-MO-Katalog):

```python
import gettext

with open('AppDB.hlp', 'rb') as file:
    help_catalog = gettext.GNUTranslations(file)

# Direkt mit Namen suchen
content = help_catalog.gettext('test')

# Mit Hilfenummer suchen: Nummer -> Name -> Inhalt
name = help_catalog.pgettext('turbo-help-id', '1234')
content_by_number = help_catalog.gettext(name)
assert content_by_number == content
```

**Turbo-Vision-Programm (C-ABI über Qt5-Bridge):**

```c
#include "d64qt5_bridge.h"

/* Lädt AppDB.hlp neben AppDB.exe; öffnet Thema "test": */
DBaseQtHelpShowTopicId(1234);

/* F1 bzw. direktes Öffnen des Index-Themas: */
DBaseQtHelpShowMo(NULL);
```

Die neue C-ABI-Funktion `DBaseQtHelpShowTopicId(unsigned int)` trägt den
neuen Export-Ordinal `@1018`. Der bisherige `DBaseQtHelpShowMo` mit `@1017`
bleibt unverändert erhalten. `%link 1234` und `%ref 1234 #beispiel` lösen
den Zahlenalias auch innerhalb des nativen Fensters auf. Der Fenstertitel
zeigt stets den **Themennamen**, nicht den Zahlenalias.

## 3. Fensterlayout in `libd64_qt5.dll`

- **Außenrahmen:** gelb `#FFE600`, 2 Pixel Breite.
- **Schatten:** scharf, 5 Pixel nach rechts und 5 Pixel nach unten versetzt.
- **Textspalte:** DOS-Spalte 1 enthält den Rahmen, Spalte 2 bleibt cyanfarben
  und leer; der Text beginnt in **Spalte 3**. Der linke Einzug richtet sich
  dynamisch nach der aktuellen DOS-Zellbreite (`2 * Zellbreite - 2` Pixel ab
  Textbrowser-Viewport, wobei der 2-Pixel-Fensterrahmen bereits davor liegt).
- **Layout:** die Innenansicht bleibt cyan, die Titelleiste heller; Titel
  `Hilfe:  <Hilfethema>`; F1, Pfeil-Scrollbars, Klick-Fokus, Rasterbewegung
  und Rastergrößenänderung bleiben erhalten.

## 4. Betroffene Dateien

- `turbo_help_compiler.py`: optionale `%topic`-Nummer, eindeutige ID-Tabelle;
  `write_po` erzeugt `msgctxt`-Aliase, `read_po` übernimmt sie in die `.mo`.
- `d64qt5/d64_turbo_help_window.hpp`: nummernbasierte Navigation, gelber
  Rahmen, 5-Pixel-Schatten und blockbasierter Textbeginn.
- `d64qt5/d64qt5_bridge.cpp`, `.h` und `.def`: neue C-ABI-Funktion.
- `test_stage664.py`: neue und bestehende Tests für GNU-MO, Numeric-Aliase,
  Fehlerfälle und GUI-Schnittstellen.
- `build_and_deploy_dbase_editor_stage664.bat`: aktualisierter DLL-Build.

## 5. Test-/Buildstatus

- Die Python-Compiler- und GNU-MO-Funktionen wurden real ausgeführt;
  die GNU-MO-Datei wurde mit `gettext.GNUTranslations` geprüft.
- Qt5-Bridge-Schnittstelle und Fensterlayout wurden statisch überprüft.
- Ein nativer Windows-/Qt5-Build ist hier mangels Qt5-Entwicklungsbibliotheken
  nicht möglich und muss unter Windows nachgeholt werden.

**Windows:** `build_and_deploy_dbase_editor_stage664.bat` baut und deployt
`libd64_qt5.dll`. Weder zusätzliche Help-Host-EXE noch erneute Übersetzung
vorhandener dBASE-Quellen sind dafür nötig. Neue ID-Aliase erfordern jedoch
Neukompilierung der `.thlp`-Quellen (F2), damit `AppDB.hlp` sie enthält.
