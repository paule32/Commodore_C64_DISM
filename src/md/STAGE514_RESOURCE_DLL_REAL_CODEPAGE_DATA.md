# Stage 514 – Ressourcen-DLLs mit tatsächlich codepageabhängigen Daten

Basis: Stage 513 (`d64_dism_asm_513.zip`).

## Fehlerursache

Der vorherige DLL-Builder nutzte die Codepage-Auswahl vor allem zur Auswahl
von `win32|win64/unicode|utf8|ascii`. Anschließend wurden `ResourceEntry`-Objekte
unverändert in `.res`, `.o` und `.dll` geschrieben. Wenn beispielsweise
`#pragma code_page(1200)` in der RC-Datei stand und der Build auf ASCII oder
UTF-8 gestellt wurde, konnten die RCDATA-Textdaten weiterhin UTF-16LE sein.

## Korrektur

- Der ausgewählte Build-Modus wird für die tatsächliche Neukompilierung des
  **RC-Quelltextes im Speicher** verwendet, falls die ursprünglich kompilierten
  Einträge eine andere Codepage tragen. Die Originaldatei wird nicht verändert.
- Der alte `#pragma code_page(...)`-Wert wird für den konkreten Build
  überschrieben (für alle Ressourcen dieses Builds einheitlich).
- `RCDATA`-Stringliterale und `DLGINCLUDE`-Text erhalten tatsächlich die
  gewählte Kodierung:
  - Unicode = UTF-16LE, Codepage 1200
  - UTF-8 = UTF-8, Codepage 65001
  - ASCII = US-ASCII, Codepage 20127
- In ASCII nicht darstellbare RCDATA-Zeichen führen **vor** dem Schreiben der
  Ausgabedateien zu einem Kompilierfehler – keine stillschweigende Datenvernichtung.
- `IMAGE_RESOURCE_DATA_ENTRY.CodePage` in der DLL erhält die gewählte Codepage.
- Die Ausgabeordner bleiben `win32|win64/unicode|utf8|ascii` und enthalten je
  `<RC-Basisname>.res`, `.o` und `.dll`.
- Ein echter Windows-Standard-`RT_STRING`-/`RT_MENU`-Eintrag muss weiterhin
  gemäß der Microsoft-Ressourcenformate UTF-16LE verwenden. Diese Bytes *dürfen
  nicht* in ASCII oder UTF-8 umkodiert werden, sonst würden `LoadString` und
  Menü-Ressourcenloader ungültige Daten erhalten.

## Zusätzliche Codepage-Textdaten für STRINGTABLE und MENU

Für ASCII/UTF-8 erzeugt der DLL-Builder zusätzlich eigenständige, benannte
Ressourcen, die tatsächlich bytekodierte Texte enthalten:

- `D64_STRING_CP` mit derselben Block-ID wie die ursprüngliche STRINGTABLE.
  Format: `D64STR01` (8 Bytes), Codepage als little-endian uint32, danach
  16 × (Stringlänge in Bytes als little-endian uint32 + Textbytes).
- `D64_MENU_CP` mit derselben ID wie die ursprüngliche MENU/MENUEX-Ressource.
  Format: `D64MENU1` (8 Bytes), Codepage uint32, Anzahl uint32,
  anschließend pro Menübefehl in der Menü-Reihenfolge die Byte-Länge uint32
  und die Textbytes.
- Unter ASCII werden dort nicht darstellbare Unicode-Zeichen durch `?`
  ersetzt; der unveränderte Windows-Standardtext bleibt zusätzlich erhalten.
- Diese zusätzlichen Ressourcen sind über `FindResource` mit ihrem
  Typnamen abrufbar. Sie sind **kein** Ersatz für `LoadString` oder `LoadMenu`.
- Im Unicode-Modus gibt es **keine** zusätzlichen Codepage-Spiegel; es werden
  die regulären Windows-Ressourcen geschrieben.

Somit unterscheiden sich die Binärinhalte der drei Buildvarianten auch bei
STRINGTABLE-/MENU-Projekten, während alle DLLs kompatible Windows-Ressourcen
enthalten. Ein *vollständig UTF-16LE-freies* RT_STRING/RT_MENU/RT_DIALOG ist
innerhalb des Windows-Ressourcenformats technisch nicht möglich.

Für bereits kompilierte `.res`-Dateien ist eine verlustfreie Rekodierung ohne
zugehörige `.rc`-Quelldatei nicht möglich; ein erzwungener abweichender
Codepage-Build wird deshalb abgelehnt.

## Prüfung

- Sechs Varianten x86/x64 × Unicode/UTF-8/ASCII aus einer einzigen
  unveränderten RC-Datei erstellt.
- Tatsächliche Bytes des `RCDATA`-Textes, PE-Machine-Typ und Codepage-Felder
  der Ressourcenverzeichnisse überprüft.
- Windows-Standard-STRINGTABLE/MENU und ihre zusätzlichen Codepage-Textblöcke
  geprüft.
- Fehlerfall ASCII nicht darstellbarer RCDATA-Zeichen und Vermeidung
  unvollständiger Ausgabe geprüft.
- 120 gezielte Tests bestanden (Stand Erstellung).
- PyQt5-Laufzeit unter Windows nicht visuell getestet.
