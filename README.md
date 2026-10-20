# Commodore_C64_DISM
A Commodore C-64 Disassembler and Disk-Image Information Viewer and de-packer

### [Link](https://www.paypal.com/ncp/payment/CUBXY9QPTPHRU) for a Sponsor Donat
### [Link](https://kallup.net/downloads) to download a ZIP Archive for ready to run Windows 64-Bit Pro execution binary and all needed DLL file's.
---

# d64_dism – Illustrierter Projektatlas

**Integrierte Entwicklungsumgebung, Retro-Compiler, Werkzeuge und 
Lernmodule**
**Stand:** 15. Oktober 2026

![Architektur des d64_dism-Projekts](d64_dism_Projektuebersicht_Stage420_assets/architektur.png)

## Projektidee

- Eine stark erweiterte Python-/PyQt5-IDE mit Projekten, Docking-Arbeitsflächen, Quelltext- und Binärwerkzeugen.
- Eigene Übersetzungs-, Assembler- und Linkerbausteine für C64, Amiga und Windows-PE; zusätzlicher dBase-/WFM-Zweig.
- Fachwerkzeuge für C64-Grafik, Ressourcen, Dokumentation, Serverkonfiguration, Datenbanken sowie Mathematik und Lernen.

---

## 01 Entwicklungsumgebung und Projektarbeit

Das gemeinsame Fundament der verschiedenen Compiler-, Designer- und 
Lernbereiche.

### Oberfläche

Verschiebbare Werkzeugleisten und skalierbare Docks; zentraler 
Dokumenteditor mit Registerkarten. Themes einschließlich Hell/Dunkel, 
Statusfelder, Favoriten und zuletzt verwendete Dateien.

### Projekte

Projekt-/Informationen-TreeList und Dateisystemansicht mit 
Arbeitsverzeichnis. `.pro`-Projekte, Projekteinstellungen je 
Plattform-/Compilerprofil und persistente Dateizuordnung.

### Editoren und Komfortfunktionen

- Syntaxhervorhebung, Zeilennummern, Zoom, Suchen (Strg+F/F3), Bearbeiten-Aktionen mit Undo/Redo und Zwischenablage.
- F2-/Compile-/Assemble-/Start-Abläufe mit zielabhängigem Verhalten; Quelltexte und erzeugte Ausgabe in getrennten Ansichten.
- Hex-Viewer: acht Bytes pro Zeile (4+4), PETSCII-Spalte, C64Pro-Font und JSON-Mapping für 256 PETSCII-Codes.
- F1-/CHM-Kontexthilfe, Protokoll-Dock, Fortschrittsanzeige bei längeren Disassemblierungen.
- Neue C64-BASIC-/Assembler-Dateien zunächst als ungespeicherte Vorlagen; erst beim Speichern entsteht die Datei.

### Projektbaum – typische Bereiche

| Knoten / Arbeitsbereich | Verwendung |
|---|---|
| BASIC, ASM, Pascal, C, LISP, Prolog, LOGO, dBase | Quellcodedateien, Module und sprachspezifische Editoren |
| C= 64 Sprites / Ressourcen | Hardware-Sprites, Bitmap-Sprites, Character-/Screen-Ressourcen |
| Tabellen / Formulare / Berichte | DBF-Daten, WFM-Designer, SQL-, Report- und Etikettenobjekte |
| Resourcen / Archive / Wissensdatenbanken | Windows-Ressourcen, COFF-Objekte, PROLOG-Datenbanken |

---

## 02 C64-Disketten, Disassembler und VICE

Die ursprüngliche Retro-Funktion bildet weiterhin einen eigenständigen 
Arbeitszweig.

### D64- und PRG-Werkzeuge

- D64 öffnen, Verzeichnis und BAM anzeigen; Programme extrahieren, Startadresse untersuchen und PRGs disassemblieren.
- MOS 6502/6510-Code mit Operanden und Mnemonics anzeigen; optionale Live-Hilfe und Kontextinformationen.
- Binär-/RAM-Images, Start-Up-Analyse und Hexansicht mit PETSCII-/Zeicheninterpretation.
- Disassemblierung im Worker-Thread mit bytebasiertem Fortschritt und Statusanzeige.

### Zwei Wege zur VICE-Ausführung

![Zwei Wege zur VICE-Ausführung](d64_dism_Projektuebersicht_Stage420_assets/vice_ausfuehrungswege.png)

- **BASIC direkt → VICE:** Hostdaten per Remote Monitor; `LOAD SPRITE` -> RAM `$3000`.
- **BASIC → Compiler → VICE:** Spritebytes im PRG eingebettet; `SCREEN / DRAW / ERASE`.

### VICE-Integration

- Direkttransfers von BASIC-Zeilen/Programmen; ASM-PRGs byteweise in den C64-RAM übertragen.
- Binary Remote Monitor v2: Register/PC setzen, einzelne Instruktionen ausführen, Programmausführung fortsetzen.
- D64-Image mit 1541-BAM, Verzeichnis und PRG-Sektorketten erzeugen; Image auf Laufwerk 8 einlegen und erste PRG-Datei autostarten.
- Konfigurierbare VICE-Settings (`vice.ini`), Laufwerk-8-Verzeichnis und projektlokale Sprite-Datenvorbereitung.

> **Hinweis:** Die Konfiguration eines bereits laufenden VICE und die 
Laufwerksbelegung können sich vom VICE-Neustart unterscheiden. Zahlreiche 
Integrationstests sind quellcode-/CPU-basiert, nicht echte 
Windows-Emulator-End-to-End-Tests.

---

## 03 C64-Zeichen-, Pixel- und Sprite-Werkzeuge

Retro-Grafikdesigner und neue Software-Sprite-Arbeit.

### 16 C64-Farbindexwerte

Palette schematisch; die Farbdarstellung ist hardware-/emulatorabhängig.

![16 C64-Farbindexwerte](d64_dism_Projektuebersicht_Stage420_assets/c64_farbpalette.png)

### Hardware-Sprite-Editor

24×21 HiRes bzw. 12×21 Multicolor; transparente Pixel. 
VIC-II-Farbregister, gemeinsame MC-Farben sowie 2×-Skalierung. 
`.spr`/`.sprite`/`.bin` als echte 63-/64-Byte-Sprite-Rohdaten; 
Projektablage.

### Bitmap-Sprite-Editor

Stage 416: frei einfärbbares Raster, 16 C64-Farbindexwerte und Transparenz 
je Pixel. 24×21 Standard, bis 128×128; mehrere Sprites, Duplizieren und 
Löschen. `.bmsprite`/`.bmspr`: binär mit `C64BMSP1`-Header, kein JSON.

### Weitere C64-Designer

- Character-Editor: bis zu 255 editierbare 8×8-Zeichen.
- Paletten-Editor: 16 VIC-II-Farben bearbeiten und Quellcode exportieren.
- Text-Screen-Editor: 40×25 Zeichen mit einzelnen Zellfarben.
- Pixel-Screen-Editor: 320×200 Pixel mit 16-Farben-Werkzeugen.
- BASIC-Editor: C64-Schrift, Bildschirmtastatur, PETSCII, Nummerierung und eigene Zeilen-/Spaltendarstellung.

> **Hinweis:** Ein 16-Farben-Bitmap-Sprite kann nicht unverändert in jeder 
Zelle 16 Farben anzeigen: Im VIC-II-Multicolor-Bitmap gelten vier Farben 
je 8×8-Zelle, darunter die globale Hintergrundfarbe.

---

## 04 C64-BASIC – Bildschirm- und Software-Sprites

Stage 413–417 erweitert BASIC V2 um eine eigene Sprite-/Grafiksyntax.

| Befehl | Ergebnis |
|---|---|
| `LOAD "name.spr",8,1` | PRG-Datei vom D64-Laufwerk 8 via KERNAL LOAD |
| `LOAD SPRITE "name.spr"` | Sprite vom Windows-Host; direkt über Monitor oder zur Compilezeit eingebettet |
| `LOAD SPRITE "name.bmsprite"` | 16-Farben-Bitmap-Sprites als Compiler-Ressource |
| `SCREEN ON` / `SCREEN OFF` | Multicolor-Bitmap aktivieren / vorherigen VIC-Zustand wiederherstellen |
| `SPRITE SOFTWARE ON` / `OFF` | Software-Zeichenbefehle aktivieren / deaktivieren |
| `SPRITE DRAW N,X,Y` | Software-Sprite mit Transparenz zeichnen |
| `SPRITE ERASE N` | Sprite entfernen und verbleibende Szene neu aufbauen |
| `SCREEN WAIT` | Bitmapanzeige bis Tastendruck anhalten |

### Beispiel – C64-BASIC zum Maschinencode

```basic
10 LOAD SPRITE "figuren.bmsprite"
20 SCREEN ON
30 SPRITE SOFTWARE ON
40 SPRITE DRAW 0,100,80
50 SCREEN WAIT
60 SPRITE DRAW 1,140,80
70 SPRITE ERASE 0
80 SCREEN OFF
```

> **Hinweis:** In Stage 417 ist die Bitmap-Zeichenszene zur Compilezeit 
vorbereitet. Die Nummern/Koordinaten sind zunächst konstant; X muss im 
Multicolor-Modus gerade sein. Direkter VICE-BASIC-Debugtransfer 
unterstützt SCREEN/DRAW/ERASE noch nicht.

---

## 05 Compiler-Sprachen und Zielsysteme

d64_dism vereint mehrere Frontends. Der Sprachumfang unterscheidet sich 
deutlich je Sprache und Plattform.

| Frontend | Codebasis / Funktionen | Ziele laut Projektcode |
|---|---|---|
| BASIC | BASIC V2, C64-Grafik-/Datei-/Sprite-Erweiterungen, internes 6510-ASM | C64-PRG; BASIC-Interpretertransfer an VICE |
| Pascal | ANTLR-Frontend, Units/PUI, Records, Arrays, statische Klassen | C64, Amiga sowie Windows-PE-Zweig |
| C | ANTLR-Frontend, Präprozessor/Makros, Kontrollfluss, Typen | C64 und Amiga; Windows-PE-Werkzeuge |
| dBase | DBF/SQL/WFM, Stringfunktionen, Konsolen-/GUI-Runtime | Windows PE32/PE32+ |
| PROLOG | Unifikation, Listen, Choice-Points, Trail, assert/retract, Wissen-Browser | Windows PE32/PE32+ |
| LISP / LOGO / ELAN | Eigene Frontend-/Generatorpfade und Sprachbeispiele 
| Unterschiedlicher, teils begrenzter Zielumfang |

### Integrierte Übersetzungsbausteine

- MOS6510-Assembler mit Sprungweitenbehandlung; Motorola-68k-Assembler und Amiga-Hunk-/ADF-Ausgabe.
- COFF32/COFF64-Objekterzeugung, interne Windows-PE-Linker, Import-/Export-Unterstützung, Laufzeit-Bibliotheken.
- ANTLR-Lexer und -Parser für C und Pascal; Compiler liefern menschenlesbaren Assembler zur weiteren Bearbeitung.
- Projektprofile für Windows 32/64-Bit und Commodore/Amiga-Targets; Compile / Assemble / Start.

> **Hinweis:** „Frontend vorhanden“ belegt keinen vollständigen 
Sprachstandard oder eine für jede Kombination bestätigte ausführbare 
Ausgabe. Die Modul-READMEs nennen jeweils die tatsächlich unterstützten 
Teilmengen.

---

## 06 Windows-Compiler, Ressourcen und Laufzeit

Eigenständige PE-/COFF-Werkzeuge neben der C64-Welt.

### PE-Toolchain

Integrierter IA-32/PE32-Assembler und COFF32-Writer. PE32-/PE32+-Linker, 
COFF-Archive sowie DLL-Imports/-Exports. Win32-Startprogramme, 
MSZIP-Image-Packer und Workstation-Runner.

### Ressourcen & GUI

RC-Skriptcompiler zu `.res` und COFF-Resource-Objekten. Ressourcen-Editor 
mit Syntaxmarkierung, Zeilennummern und Minimap. 
Windows-Manifest-Projektoptionen; dBase-WFM-Formdesigner und 
Qt5-C-ABI-Bridge.

### Entwicklung und Laufzeit

- Workstation-Mode mit separatem PE32-/PE32+-Startpfad und Session-Host.
- Win32-Launcher mit Watchdog, Konsolenlog und Fallback-Fehlerdialog.- Debugfenster mit projektbezogenen Darstellungsoptionen; Thema hell/dunkel.
- Windows-Grafikziele und Direct2D-/Direct3D-Runtime-Werkzeuge im Werkzeuge-Menü.

### Build-Grenzen

Die internen Compiler und Assembler sind ein wichtiges Projektziel. 
Einzelne Bridges/Runtimes benötigen dennoch passende 
Qt-/MinGW-Buildumgebungen und sind nicht zwangsläufig beim IDE-Start 
automatisch gebaut.

---

## 07 dBase, Datenbanken und Formulardesign

Ein vollständiger zweiter Anwendungsschwerpunkt, nicht nur ein 
Sprachfrontend.

### Datenbankschicht

- DBF-Dateien lesen und schreiben; Tabellendesigner, Datenraster, Feldtypen, Mehrtabellen-Arbeitsfläche.
- SQL-Builder mit Design-/View-Bereichen, Tabellenbeziehungen, Sortierung, Daten-Navigation.
- ODBC-Login und DSN/DBQ-Konfiguration, einschließlich 32-/64-Bit-Helferweg.
- Bericht-Builder mit Datenfeldern, PDF/Druck; Etiketten-Designer mit Vorlagen und druckfertigem Layout.

### Formular-/WFM-System

- Visueller Formdesigner, Eigenschafteneditor, Komponenten- und Border-/Schattensteuerung.
- Dark-/Light-Mode, Controls, Event-/Timer-Properties und projektgebundene WFM-Dateien.
- Qt5-Bridge `d64qt5.dll` für native dBase-Programme mit Konsole/DEBUG-Ausgaben.
- dBase-Compiler mit String-, Klassen- und Präprozessorunterstützung.

### Entwicklungswerkzeuge für Daten

| SQL + DBF | Bericht + Etikett |
|---|---|
| Quellen wählen, Beziehungen einzeichnen, Abfrage testen. SQL-Ergebnis anzeigen und in Report verwenden. | Layout visualisieren, Datenbankfelder platzieren, PDF exportieren. Speichern/Laden projektbezogener Entwürfe. |

---

## 08 Lernen, Elektronik, Dokumentation und Server

Zusätzliche integrierte Werkzeuge außerhalb klassischer Compiler-Aufgaben.

### Mathematik & Wissen

Einheitskreis, Sinus/Kosinus, Formel-Designer, Zahlenmauern. Fibonacci, 
Pascal-Dreieck, Primzahlen, Geometrie, Zinsrechnung. MineSweeper, Memory 
und weitere Lernspiele.

### Geo & Naturwissenschaft

Deutschland-/England-/Frankreich-Karten und Fluss-Overlays. Periodensystem 
mit Detailansicht und Chemie-Baukasten. E-Baukasten mit Bauteilen, 
Schaltplan und Simulationsansätzen.

### Musik, Sprache, Medien

Musik-Keyboard / Klavier mit Notenbereich. Retro-Speech-Runtime und 
Sprachsynthese-Module. WYSIWYG-HTML-Editor und Lokalisierungswerkzeuge.

### Dokumentation & Server

CHM-Hilfe und Doxygen-Dokumentationsoberfläche für Pascal/C++. 
BIND9/DynDNS-, OpenSSL- und Apache-Dock-Panels. Qt-Themes, Übersetzungen, 
Ressourcen und Hilfedialoge.

> **Hinweis:** Einige spezialisierte Module wurden über viele 
Entwicklungsstufen ergänzt. Der Quellcode belegt ihre Einbindung; 
Bedienungsumfang und Laufzeitqualität sind abhängig von benötigten 
externen Programmen, Assets und Betriebssystemen.

---

## 09 Optimierung – Programme deutlich kompakter

Die jüngsten Stages konzentrieren sich auf die Verringerung des 
generierten MOS6510-Programmcodes.

| Schalter | Aufgabe |
|---|---|
| STA reducer  * Stage 418 | Wiederholte STA-Folgen zu Literal-/RLE-Tabellen plus Decoder verdichten. |
| Bitmap-Clear * Stage 419 | 40 STA-Seitenschreibungen durch eine selbstmodifizierende Seiten-Löschroutine ersetzen. |
| CALL reducer * Stage 420 | Unerreichbaren C64-BASIC-Runtime-Code nach Kontrollfluss-/Referenzanalyse entfernen. |

### Beispielmessung: C64-Bitmap-Sprite-Programm

![Größenvergleich mit Reducern](d64_dism_Projektuebersicht_Stage420_assets/optimierung_groessenvergleich.png)

| Optimierung | PRG-Größe |
|---|---:|
| Ohne Reducer | 2.359 B |
| Nur CALL | 1.587 B |
| Nur STA | 1.889 B |
| STA + CALL | **1.117 B** |

**Stage-420-Vergleich:** Beide Reducer senken die PRG-Größe von 2.359 auf 1.117 Bytes (ca. 53 %).

### Entwicklungsschritte (Auswahl)

![Entwicklungsschritte von Stage 393 bis Stage 420](d64_dism_Projektuebersicht_Stage420_assets/stage_zeitstrahl.png)

| Stage | Entwicklung |
|---|---|
| 393 | Hex + PETSCII |
| 396 | HW-Sprites |
| 404 | Binäre `.spr` |
| 409 | D64/VICE |
| 413 | `LOAD SPRITE` |
| 416 | Bitmap-Editor |
| 417 | Software-Sprites |
| 418–420 | Optimierer |

---

## 10 Entwicklungsstand, Risiken und nächste Meilensteine

Diese Übersicht trennt implementierte Codefunktionen von vollständig 
bestätigten Laufzeitergebnissen.

### Im Archiv nachvollziehbar

- `d64_dism.py` umfasst rund 140.000 Zeilen; Stage-420-ZIP enthält rund 400 Projektdateien mit Modulen und Tests.
- Stage 393–420 besitzt separate technische Änderungsdokumente; für CALL-/STA-Reducer liegen Regressionstests und echte Assembler-PRG-Vergleiche vor.
- Das C64-BASIC-, Sprite- und VICE-Teilsystem wurde mehrfach anhand konkreter hochgeladener Programme korrigiert.

### Nicht als vollständig bestätigt ausgeben

- Ende-zu-Ende-Tests aller GUI-Module unter Windows, sämtlicher VICE-/WinUAE-Konfigurationen und aller PE-/Amiga-Ziele.
- C64-Bitmap-Software-Sprites mit dynamischen Koordinaten und Animationen; Stage 417 arbeitet vorwiegend mit konstanten Szenen.
- Generelle CALL-Reducer-Sicherheit für beliebigen, externen und indirekt referenzierten Assemblercode.
- Unbegrenzte 16-Farben-pro-Pixel-Darstellung auf echter VIC-II-Hardware; Zellfarbgrenzen bleiben bestehen.

### Empfohlene nächste Meilensteine

| Priorität | Konkretes Vorhaben |
|---|---|
| 1 | Windows-GUI-/VICE-Regressionssuite für `LOAD SPRITE`, `SCREEN/DRAW/ERASE` und Disk-Image-Autostart. |
| 2 | Dynamische Software-Sprites: Bewegungs-/Kollisionsroutinen, RAM-Sicherheit und Farbkonfliktstrategien. |
| 3 | Compiler-Optimierung mit sicheren Symbol-/Funktions-Roots, testbarer Callgraph-Ausgabe und Größenreport. |
| 4 | Automatisierter Build- und Funktionstest über C64, Amiga, PE32 und PE32+. |

### Quellengrundlage

`d64_dism.py`, Module, README-Dateien, Stage-Dokumente 393–420) sowie im 
Projekt bereitgestellte Entwicklungsnotizen. Frühere Entwicklungsstände 
werden nur als Kontext erwähnt, soweit der aktuelle Stage-420-Code sie 
weiterführt.

---


Preview
![Preview](img/screen0021.png)


Step 1

![Preview](img/screen00A1.png)

After the Application start, click the "Open" menu item.
An other Dialog will open that display the File System.
Navigate to your Data that you would like to edit.


Step 2

![Preview](img/screen00A2.png)


Step 3

![Preview](img/screen00A3.png)


Step 4

![Preview](img/screen00A4.png)


Step 5

![Preview](img/screen00A5.png)

After you Compile, and Assemble the Form / Application you have navigate to
the example/dbase Directory. You will find a .exe cution file as result of
Compile, and Assemble. You should be able to start the Application.
Make sure, you have access to the **D64QT5.DLL** in the same folder as the
exe file resides.

If you have luck, a new Workstation will be open with a blank screen; and 
the application.

Have fun in coding with dBASE...


For **FibuDev**:

![Preview](img/screen0013.png)

This Picture shows the test.exe which is the result of Compile, and 
Assemble the examples/dbase/test.wfm. The finally file a size of rounded 
3.500 Bytes (packed with **win32api** packing functions. The unpacked file
have a size of rounded 7.200 Bytes (also a save of 3.000 Bytes).

## A note for the Cyper Security:
The packaged file is transparent, and can be re-expand rewardly to check
for malware or other hidden stuff in the original dBASE Compiler.

## NO WARANTEES
I give no warantees for any damage that result of packed code by other 
parties of Software Provider.
I will give my best to not remove seals by, and with other Software.


Preview - New Source Code Editor Layout for dBASE Compiler
![Preview](img/screen00A6.png)


Preview - Resource-Editor / Compiler
![Preview](img/screen0019.png)


Preview - Prime Solver
![Preview](img/screen0020.png)


Preview - E-Baukasten
![Preview](img/screen0018.png)


Preview - Report Designer
![Preview](img/screen0017.png)


Preview
![Preview](img/screen0015.png)


Preview
![Preview](img/screen0016.png)


Preview
![Preview](img/screen0012.png)


Preview
![Preview](img/screen0011.png)


Preview
![Preview](img/screen0010.png)


Preview
![Preview](img/screen0009.png)


Preview
![Preview](img/screen0008.png)


Preview
![Preview](img/screen0007.png)


Preview
![Preview](img/screen0006.png)


Preview
![Preview](img/screen0005.png)


Preview
![Preview](img/screen0004.png)


Preview A<br>
![Preview](img/screen0001.png)


Preview
![Preview](img/screen0002.png)


Preview
![Preview](img/screen0014.png)


Preview
![Preview](img/screen0022.png)


Preview
![Preview](img/screen0023.png)


Preview
![Preview](img/screen0024.png)
