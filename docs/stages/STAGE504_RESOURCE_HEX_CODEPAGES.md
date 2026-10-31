[Deutsch](STAGE504_RESOURCE_HEX_CODEPAGES.md) | [English](STAGE504_RESOURCE_HEX_CODEPAGES.en.md)

# Stage 504 – Ressourcen-Editor: Hex-Viewer und Codepage-Ausgabe

**Verbindliche Basis:** `d64_dism_asm_503.zip`.

## Behobene Probleme

- Bis Stage 503 zeigte die rechte Spalte der Hex-Ansicht unabhängig vom Codepage-Eintrag nur ein statisches byteweises ASCII-Ersatzbild.
- Der interne RC-Compiler kodierte schmale Zeichenketten in `RCDATA` und `DLGINCLUDE` stets als CP1252, selbst wenn `#pragma code_page(65001)` (UTF-8) oder `#pragma code_page(20127)` (ASCII) gesetzt war. Der im COFF-Header angegebene Codepage-Wert entsprach deshalb nicht zwingend dem Textinhalt.
- Nach Auswahl einer neuen Codepage änderte sich zunächst nur der Eintrag im RC-Quelltext und im ResourceEntry-Metadatum. Die bereits erzeugten Bytefolgen und die Hex-Ansicht wurden nicht neu aufgebaut.

## Umsetzung

1. `format_resource_hex(data, codepage, resource_type=...)` zeigt den **tatsächlichen Byte-Inhalt** links und rechts die passend dekodierten Zeichen. UTF-8 und UTF-16LE werden inkrementell dekodiert, damit Mehrbytezeichen über 16-Byte-Zeilengrenzen nicht kaputtgehen. Steuerzeichen werden als Punkt dargestellt, ungültige Sequenzen als Ersatzzeichen. Die Anzeige ist in ASCII, UTF-8, Unicode sowie für unterstützte weitere CP-Codepages verfügbar.
2. Die Kompilierung von **schmalen** eingebetteten `RCDATA`-/`DLGINCLUDE`-Strings folgt der gewählten Codepage: ASCII=20127, UTF-8=65001, Unicode=UTF-16LE=1200. Die Daten werden mit der passenden Null-Terminierung ausgegeben. Die bisherige Standardcodepage 0 bleibt CP1252-kompatibel. Nicht darstellbare ASCII-Zeichen verursachen eine verständliche Compile-Diagnose statt stiller Datenverluste.
3. Ausdrücklich weite RC-Literale wie `L"Text"` bleiben immer UTF-16LE, weil ihre Schreibweise Unicode verlangt.
4. Bei einer Änderung der ComboBox **Eigenschaften → Codepage** wird das aktuelle, noch nicht gespeicherte `.rc`-Dokument für die Vorschau im Speicher neu kompiliert. Die Datei auf dem Datenträger wird nicht durch einen bloßen ComboBox-Wechsel überschrieben. Hex-Ansicht, Ressourcengrößen und ResourceEntry-Daten werden erneuert.
5. RES und COFF32/COFF64 übernehmen bei neu kompilierbaren Rohdaten die tatsächlich neuen Bytes. Im PE-Resource-Verzeichniseintrag bleibt die gewählte Codepage hinterlegt.
6. Unter **Eigenschaften → Datenformat** steht nun eine Erklärung, ob die Ressource ein natives Windows-UTF-16LE-Layout hat oder frei kodierbare Nutzdaten enthält.

## Windows-Kompatibilität ist zwingend

Bei Microsoft-Ressourcentypen `STRINGTABLE`, `DIALOG`, `MENU` und `VERSIONINFO` sind **Struktur- und Textfelder gemäß Windows-Binärformat UTF-16LE**. Die ComboBox-Codepage kann diese Felder nicht in ASCII oder UTF-8 umschreiben, ohne ungültige Windows-Ressourcen zu erzeugen. Der Hex-Viewer kennzeichnet diese Ausnahme explizit und dekodiert sie korrekt als Windows-UTF-16LE. Codepage ist dort PE-Metadatum, keine Umkodierung der fest definierten Binärstruktur.

Externe Dateien wie `.bmp`, `.ico` oder als Ressource eingebundene Binärdateien behalten ihre ursprünglichen Bytes. Die Codepage-Angabe ist hierfür kein Transcoder. Eine klassische `.res`-Datei speichert im Header keine Codepage und kann ihren ursprünglichen Wert daher nach dem Einlesen nicht zuverlässig wiederherstellen; der vorhandene Schutz in der Eigenschafts-ComboBox bleibt bestehen.

## Beispiel für Rohdaten

```rc
#pragma code_page(65001)
101 RCDATA
BEGIN
    "Grüße"
END
```

Der relevante Bytestrom beginnt in UTF-8 mit `47 72 C3 BC C3 9F 65 00`.
Mit `code_page(1200)` entsteht UTF-16LE: `47 00 72 00 FC 00 DF 00 65 00 00 00`.
Mit `code_page(20127)` und dem Text `Hallo` entsteht `48 61 6C 6C 6F 00`; bei nicht-ASCII-Zeichen meldet der Compiler einen Fehler.

## Prüfungen

- `python -m py_compile d64_dism.py` erfolgreich.
- `test_stage504_resource_hex_codepage.py`: reale RC-Kompilierung für alle drei Codepages, UTF-8-Multibyte-Zeilengrenzen, Unicode, ASCII-Fehler, explizit weite Literale, Windows-STRINGTABLE-Ausnahme, in-memory Vorschau ohne Dateiänderung, RES-Roundtrip sowie COFF32/COFF64-Payload und Codepage-Metadaten.
- Weitere Stage-457-/501-/502-/503- sowie Hex-Regressionstests: **87 bestanden, 7 Subtests bestanden** (gemeinsamer Prüflauf).
- Native PyQt5-GUI-Bildschirmprüfung ist in dieser Umgebung nicht möglich (PyQt5 nicht installiert), daher unter Windows nachtesten.
