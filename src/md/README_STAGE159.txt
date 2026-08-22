Stage 159 – String-Inventar und gettext-mo-Komponentenmarker

1. Nicht mit tr() umschlossene Strings
--------------------------------------
UNTRANSLATED_STRINGS_ALL.csv:
    12569 String-/F-String-Vorkommen im finalen Stage-159-Quelltext.

UNTRANSLATED_UI_STRINGS.csv:
    799 davon als typische Qt-UI-Texte erkannte Kandidaten.

Spalten:
    Zeilennummer ; String ; Englische Übersetzung

Mehrzeilige Strings werden in der String-Spalte mit dem sichtbaren Marker \n
angegeben. Die englische Spalte wird bewusst nur bei eindeutig bekannten
Übersetzungen gefüllt. Technische Strings und unsichere automatische
Übersetzungen bleiben leer.

Die ALL-Liste enthält absichtlich auch technische Strings, Docstrings,
Assembler-/Compilertexte, Dateiformate, Regex-Teile usw., sofern sie echte
Python-str/F-String-Literale und nicht unter tr(...) liegen.

2. Komponentenmarker
---------------------
Statisch erzeugte Marker: 853

Nach Programmstart erhält jedes erfasste QWidget folgende Properties:

    component.property("mo:marker")
        -> "mo:<eindeutiger-name>"

    component.property("mo:name")
        -> über gettext geladener Komponentenname

    component.property("mo:<eindeutiger-name>")
        -> derselbe übersetzte Komponentenname

Auch QAction-Objekte werden berücksichtigt.

Markerpriorität:
    1. explizites objectName
    2. Python-Ownerattribut, z.B. Klassenname.button_name
    3. bestehende Widget-Hierarchie-ID
    4. Parent/Klasse/Ordinal als Fallback

Versteckte Widgets werden bereits beim Startup markiert. Später erzeugte
Widgets erhalten den Marker über den vorhandenen globalen Show-Eventfilter.

3. tr("mo:name") und gettext
-----------------------------
Für die 853 statisch erkannten Komponenten enthält d64_dism.py die
Tabelle MO_COMPONENT_NAMES mit literal geschriebenen Aufrufen:

    "mo:...": tr("mo:...")

Für dynamisch erzeugte Widgets wird derselbe Lookup über tr(marker) ausgeführt.

tr() wurde nur für den Prefix "mo:" aktiviert. Das bisherige Verhalten aller
normalen tr()-Aufrufe bleibt damit unverändert.

Gesuchte MO-Dateien beim Programmstart:

    locales/<sprache>/LC_MESSAGES/d64_components.mo
    data/locales/<sprache>/LC_MESSAGES/d64_components.mo
    d64_components.mo

4. PO/MO-Dateien
----------------
d64_components.po
    Bearbeitbarer gettext-Quellkatalog.

d64_components.mo
    Bereits kompilierter binärer GNU-gettext-Katalog.

Zusätzlich liegen beide Dateien unter:

    locales/de/LC_MESSAGES/

Das gewünschte Schema wird verwendet:

    msgid ""
    "mo:Komponente.name"
    msgstr ""
    "Beschreibung/String"

MO_COMPONENT_MARKERS.csv enthält die Marker zusätzlich als einfache Liste.

5. Tests
--------
py_compile d64_dism.py: OK
GNU-gettext-MO konnte eingelesen werden und stimmt mit dem PO-Katalog überein.
Native PyQt5-GUI-Ausführung ist in dieser Umgebung nicht verfügbar.
