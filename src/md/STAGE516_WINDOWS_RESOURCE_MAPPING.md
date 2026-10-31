# Stage 516 – Windows-Projekteinstellungen / Umgebung / Ressourcen

Basis: Stage 515. Die Projekt-Einstellungen unter Windows -> 32-Bit bzw. 64-Bit -> Umgebung -> Ressourcen besitzen eine GroupBox **Mapping:**.

| Zeile | Einstellung | Standard |
|---|---|---|
| ASCII | `ASCII, without UTF - 16 LE Copy` / `ASCII with UTF - 16 LE Copy` | without |
| UTF - 8 | `UTF - 8, without UTF - 16 LE Copy` / `UTF - 8, with UTF - 16 LE Copy` | without |
| Unicode | `UTF-16 LE Windows Standard` | fest |

Die Einstellungen gelten pro Architektur unabhängig. Die ComboBox-Änderung synchronisiert den Besitzerzustand und löst bei bereits gespeichertem Projekt automatisch das Speichern aus. Auch das normale explizite Speichern der Projektdatei schreibt die Werte. Für bestehende Projekte ohne die neuen Schlüssel bleibt der Standard `without`.

Im Projekt-INI (Abschnitte `Settings.Windows.32Bit.Environment` und `Settings.Windows.64Bit.Environment`) werden gespeichert:

- `ResourceASCIINativeUTF16Copy=true|false`
- `ResourceUTF8NativeUTF16Copy=true|false`

Beim Klick auf win32 DLL / win64 DLL und bei den manuellen RC→RES/COFF-Schreibaktionen fragt der Ressourcen-Editor die passende Projekteinstellung ab. Für die DLL-Buttons werden weiterhin `.res`, `.o`, `.dll` unter `win32|win64/ascii|utf8|unicode` erzeugt. Für die direkten RC→RES/COFF-Buttons gilt die jeweils gewählte Zieldatei.

## Binärverhalten

- ASCII/UTF-8 **without**: nur die von Stage 515 eingeführten numerisch benannten, codepage-kodierten Ressourcentypen (`0xF004`, `0xF005`, `0xF006`, `0xF010`), ohne zusätzliche Windows-UTF-16LE-Standardressourcen.
- ASCII/UTF-8 **with**: zusätzlich zur codepage-kodierten Form werden native Windows-Ressourcen `RT_MENU=4`, `RT_DIALOG=5`, `RT_STRING=6`, `RT_VERSION=16` aufgenommen, soweit im Quelltext vorhanden. Ihre Nutzdaten sind gemäß Windows-Spezifikation UTF-16LE.
- Unicode: ausschließlich Windows-Standardformat, unabhängig von den beiden Schaltern.

**LoadStringA und LoadStringW:** Beide Funktionen greifen auf reguläre `RT_STRING`-Blöcke zu. `LoadStringA` konvertiert für den Aufrufer in die Windows-ANSI-Codepage, **nicht zwangsläufig UTF-8**. `LoadStringW` liefert UTF-16-Zeichen. Ohne native Kopie können die Sonderressourcen nur über `FindResource`/`LoadResource` mit eigener Dekodierung gelesen werden. `LoadMenu` und `DialogBox` benötigen für direkte Nutzung ebenfalls native Formate.

Die bisherigen Schutzprüfungen gegen explizit breite Strings und erkennbare UTF-16-/UTF-32-Textdaten in nichtnativem RCDATA sowie der Ausschluss benannter Ressourcen-IDs bei strengem ASCII-/UTF-8-Format sind beibehalten. Für die Zusatzkopien können diese nativen Daten auftreten.

## Validierung

- 115 frühere Ressourcen-Regressionstests erfolgreich, separat ausgeführt.
- 15 neue Mapping- und Projektdatei-Tests erfolgreich, separat ausgeführt: sechs Architektur-/Codepage/Copy-Modus-Kombinationen, PE-Ressourcenverzeichnis, Projekt-INI-Rundreise, Auto-Save-Callback, RC→RES und COFF64.
- Kombinierter Sammellauf und zusätzliche historische Projekttests erreichten beim Prozessabschluss das Zeitlimit; sie werden nicht als vollständig bestanden bewertet.
- Python-Syntaxprüfung erfolgreich. Native Windows/PyQt5-GUI und reale `LoadStringA/W`-Aufrufe noch nicht getestet.
