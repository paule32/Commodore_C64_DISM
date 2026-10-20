# Stage 463: WFM-Header / Modalität / Konstruktor und deutsche Source-Editor-Kontextmenüs

Basis: `d64_dism_asm_462.zip`.

## Formular-Designer / WFM-Header

Beim erneuten Schreiben des Formular-Quelltextes werden nur die vor dem Marker
`** END HEADER -- do not remove this line` vorhandenen benutzerspezifischen
Präambelzeilen mit dem Marker übernommen. Darauf folgen:

```dbase
// Generated on <Datum>
//
PARAMETER bmodal
LOCAL B
B = NEW Form1(51,4)
if bmodal = .T.
   B.ReadModal()
else
   B.Open()
endif

CLASS Form1 OF FORM
    ...
ENDCLASS
```

Der vom Designer erzeugte Aufruf `B.Init(121,2)` entfällt. Die vorhandenen
Methoden und die gesamte Formularklasse werden dahinter geschrieben.

### Constructor

`NEW Form1(51,4)` übergibt seine Argumente beim Programmstart an
`PROCEDURE __init__(p1,p2)` nach dem Aufbau der Formularkomponenten. Die
Argumentanzahl wird für reguläre Signaturen auch bei einer parameterlosen
`__init__()` geprüft. Abweichungen erzeugen einen `AssemblerError` mit
Angabe der erwarteten und übergebenen Anzahl. Die historische variadische
Signatur `__init__(**args, argc)` bleibt unterstützt.

### Modal / Open

Neue *per Namen* exportierte Funktionen in `libd64_qt5.dll`:

- `DBaseQtWfmModalParameter` (Ordinal 1013): Liest optional den
  Windows-Programmparameter `bmodal` via `CommandLineToArgvW`. Standard `.F.`;
  unter anderem `.T.` / `.F.` als ersten Positionsparameter,
  `/bmodal`, `bmodal=.T.`, `bmodal=false` werden erkannt.
- `DBaseQtFormRun` (Ordinal 1014): trennt modalen Eventloop und nichtmodale
  Verarbeitungswege. Modal wartet auf Fenster-Schließen, unabhängig vom
  Startweg. Nichtmodal aus der IDE (Umgebungsflag `D64_WFM_IDE_LAUNCH=1`)
  wartet bis zur Schließen-Aktion; bei normalem externen Start wird nur die
  aktuell anstehende Ereigniswarteschlange abgearbeitet und danach beendet;
  im Workstation Mode bleibt der Prozess im Sitzungs-Lifecycle.

Der Compiler erzeugt für PE32 und PE32+ einen Aufruf von `DBaseQtFormRun`
nach Erstellung der Form und `__main__`. Der Event-/Callback-Maschinencode
bleibt erhalten. Im Qt-Projekt wird `shell32` für `CommandLineToArgvW`
eingebunden. Die 64 ursprünglichen ABI-Ordinal-Exporte bleiben unverändert.
Für den WFM-Start ist eine **neu gebaute** Qt5-Bridge mit den beiden neuen
Exporten erforderlich.

## Source-Editoren: deutsche Kontextmenüs

Eine gemeinsame Übersetzungsfunktion ändert nur die sichtbaren Texte von
Qt-Standard-QActions, ohne sie zu ersetzen. Die realen QAction-Kürzel,
Auslöse-Verbindungen, Aktiviert-Zustände und `addSeparator`-Objekte bleiben.

| Bisher | Anzeige |
|---|---|
| Undo, Ctrl+Z | Rückgängig, STRG + Z |
| Redo, Ctrl+Y | Wiederherstellen, STRG + Y |
| Cut, Ctrl+X | Ausschneiden, STRG + X |
| Copy, Ctrl+C | Kopieren, STRG + C |
| Paste, Ctrl+V | Einfügen, STRG + V |
| Delete | Löschen |
| Select All, Ctrl+A | Alles auswählen, STRG + A |

Die gemeinsame Funktion wird vom Haupt-Source-Editor (inkl. C64-BASIC,
Assembler und seinen VICE-Zusatzaktionen), Resource-Code-/Hex-Editor,
Doxygen-Editor, Apache-Konfigurations- und Lokalisierungseditor verwendet.
Spezialaktionen werden nicht übersetzt oder entfernt.

## Prüfungen

- 80 automatisierte Tests bestanden, einer wegen fehlender Windows-/Qt-Runtime
  übersprungen: darunter vollständige WFM-PE32-/PE32+-Assemblierung und
  -Verlinkung, Constructor-Mismatch, ABI-Prüfsumme, JSON/BIN, DLL-Payload,
  UTF-8 und Resource Editor.
- Kontextmenü-Test prüft erhaltene Separator- und QAction-Identität und
  unveränderte Tastaturkürzel.
- Python-Syntaxprüfung der IDE erfolgreich.
- Windows-`LoadLibrary`-/interaktiver Qt5-Test ist auf diesem Linux-System
  **nicht erfolgt**. Ein Laufzeitnachweis für modale/nonmodale Fenster unter
  Windows muss noch erbracht werden.
