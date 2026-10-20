# Stage 461 — WFM `.ui.bin` und automatische Auswahl des kleineren EXE-Payloads

**Verbindliche Basis:** `d64_dism_asm_460.zip`. Alle Änderungen sind eine Weiterentwicklung dieses Archivs; Stage 460 bleibt abwärtskompatibel.

## IDE / Projekt-Einstellungen

Unter **Windows → PE32/PE32+ → Compiler → dBASE → Optimierung → Visuelle Elemente** gibt es nun zwischen `external UI components` und `compress json` die Checkbox **`store binary data`**. Sie wird je Architektur getrennt und standardmäßig `false` gespeichert.

INI-Schlüssel: `StoreBinaryData` in `Settings.Windows.32Bit.Compiler.dBASE.Optimierung` bzw. `Settings.Windows.64Bit.Compiler.dBASE.Optimierung`; interne Projektschlüssel `__windows_pe32_dbase_store_binary__` / `__windows_pe64_dbase_store_binary__`.

- `external UI components` **aus**: bisheriger WFM-Assemblerpfad, unabhängig von den weiteren Einstellungen.
- Extern **an**, Binary **aus**, Compress **aus**: `.ui.json` wird lesbar erzeugt; JSON-Bytes in `.data`.
- Extern **an**, Binary **aus**, Compress **an**: `.ui.json`-Bytes im Qt-kompatiblen Format (BE32-Länge + zlib) in `.data`.
- Extern **an**, Binary **an**, Compress **aus**: `.ui.json` und `.ui.bin` als Sidecars; **Binär-Bytes** in `.data`.
- Alle drei **an**: Beide Varianten (kompaktes JSON und WUIB) werden mit derselben zlib-Stufe 9 komprimiert. **Der kleinere tatsächlich komprimierte Payload wird ins PE-Image eingebettet.** Bei Gleichstand erhält JSON den Vorzug. `.ui.json` und `.ui.bin` werden beide erzeugt, sofern die `.wfm`-Quelldatei existiert.

Der Vergleich geschieht während der Codegenerierung **vor Assemblierung und Linken**. Die fertige EXE benötigt **keine** Sidecar-Dateien.

## Format WUIB Version 1

Der neue binäre Payload besitzt die Signatur `WUIB` mit einem Versionsbyte `01`. Danach folgen eine UTF-8-String-Tabelle (LEB128-Längen), ein Formnamen-Index und alle Elemente in derselben Handle-Reihenfolge wie der JSON-Reader. Elementfelder: Pfadindex, vier ZigZag/LEB128-Geometriewerte, optionaler Font (Family-Index, Größe, Flags), Eigenschaften als Stringindex-Paare. Alle Zahlen und Indizes sind auf 32 Bit begrenzt, String-/Elementzahlen und die Gesamtgröße sind begrenzt; fehlerhafte oder abgeschnittene Records werden verworfen.

Der neue C++-Decoder im bestehenden `DBaseQtFormApplyExternalUi` erkennt die `WUIB\x01`-Signatur nach optionalem `qUncompress`, wandelt das Ergebnis in das gleiche Qt-JSON-Modell um und ruft anschließend **denselben** existierenden Widget-Anwendungspfad auf. Event-Callbacks, nativer WFM-Code, Slots und Export-Name/-Ordinal bleiben unverändert. JSON-Bestandsprogramme bleiben mit dem neuen Reader kompatibel. **Bei der ersten Verwendung einer WUIB-EXE muss `libd64_qt5.dll` aus den geänderten Bridge-Quellen neu gebaut werden.**

## Konverter / Analyse

`python -m d64dbase.wfm_external_ui --to-bin Form1.ui.json` erstellt `Form1.ui.bin` aus einer vorhandenen JSON-Datei.

`python -m d64dbase.wfm_external_ui Form1.exe` zeigt vorhandene eingebettete JSON-/WUIB-Payloads an (auch zlib-komprimiert) sowie Dateioffset und das ausgewählte Format.

## Gemessene Datenblöcke (einschließlich Qt-Längenpräfix bei zlib)

| Testformular | JSON kompakt | WUIB | JSON + zlib | WUIB + zlib | Automatische Wahl |
| --- | ---: | ---: | ---: | ---: | --- |
| Form mit 2 Elementen | 263 B | 111 B | 191 B | 122 B | WUIB |
| 200 repetitive Controls | 47.927 B | 5.258 B | 854 B | 1.002 B | JSON |

Die Daten betreffen Payloads **vor** PE-Sektionsausrichtung. Die tatsächliche EXE-Dateigröße kann trotz kleinerem Payload unverändert bleiben.

## Tests

- Binär-/JSON-Roundtrip mit Unicode, Geometry, Properties, Schrift und Fehlerfällen
- `.ui.json`-zu-`.ui.bin`-Dateikonvertierung
- automatische Auswahl beider Komprimierungsformate, auch im Fall eines JSON-Sieges
- **8 reale WFM-Assemblierungen und PE32-/PE32+-Verlinkungen**, alle Schalterkombinationen, Payload-Nachweis **im gelinkten EXE-Image**
- Regressionen aus Stage 455–460: 65 erfolgreich, ein Test übersprungen.

**Offen:** Windows-Laufzeittest des neugebauten Qt5-Readers (Qt5-Entwicklungsbibliotheken stehen in der Linux-Testumgebung nicht zur Verfügung). Die WUIB-Runtime wird hier nicht als Windows-getestet bezeichnet.
