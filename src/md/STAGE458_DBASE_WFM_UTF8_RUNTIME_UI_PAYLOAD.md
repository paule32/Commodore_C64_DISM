# Stage 458 – WFM UTF-8 String-Runtime und PE-Formular-JSON

Verbindliche Basis: **d64_dism_asm_457.zip**.

## UTF-8 Runtime in libd64_qt5.dll

Die WFM-Codegenerierung ersetzt die pro Aufruf eingebettete UTF-8-Zeichen-Kopierschleife
und die x87-Double-zu-Integer-Konvertierung durch diese zusätzlichen **C-Exports**:

| Export | Bedeutung |
|---|---|
| `DBaseUtf8Substring` | `$(text,start[,count])` (1-basierte UTF-8-Zeichenpositionen) |
| `DBaseUtf8Upper` | `!(text)` oder `UPPER(text)` |
| `DBaseUtf8Lower` | `LOWER(text)` bzw. `LCASE(text)` |
| `DBaseUtf8SubstringUpper` | Fused `!($(text,start[,count]))` bzw. `UPPER($(...))` |
| `DBaseUtf8SubstringLower` | Fused `LOWER($(text,start[,count]))` |

Die fünf Funktionen sind als zusätzliche **Namensexporte 1006–1010** in
`d64qt5/d64qt5_bridge.def` eingetragen; bestehende Ordinals 1–64 bleiben unverändert.
Die Datenrepräsentation ist die der bisherigen WFM-Value-Slots: UTF-8-Zeiger + explizite
Byte-Länge und Start/Count als `double`. Der DLL-Code besitzt den Ergebnis-Puffer nicht:
**der Compiler alloziert genau einen Ausgabepuffer über den bisherigen `__dbase_malloc`**.
Damit wird kein Speicher zwischen unterschiedlichen CRT-Heaps alloziert/freigegeben.
Die übernommene WFM-Slot-Lifetime bleibt unverändert (keine neue Freigabe-Strategie).

Die DLL gibt die erzeugte Byte-Länge oder `UINT32_MAX` als Fehlercode zurück.
Start und Count werden zu 32-Bit-Ganzzahlen abgeschnitten; negative/nicht-finite
Werte werden auf 0, große Werte auf INT_MAX begrenzt. Start ist 1-basiert,
Start <= 0 entspricht Position 1, Count <= 0 liefert den leeren String.
Ein fehlender Count-Parameter kopiert bis zum Ende.

Die bereits in `d64_dbase_case_tables.inc` vorhandenen Unicode-Tabellen und
`dbase_case_buffer()` werden wiederverwendet. `ß` bleibt beim Uppercase erhalten.
Die Fused-Varianten wählen zuerst **ohne Kopie** den Byte-Bereich des UTF-8-Teilstrings
und konvertieren ihn unmittelbar in den einzigen Zielpuffer.

Die WFM-Assembler-Emitter für PE32/PE32+ liegen in
`d64dbase/wfm_string_runtime.py`. Für PE32+ sind die sechs Argumente der
Substring-Funktionen an die Microsoft-x64-Aufrufkonvention angepasst (Shadow Space,
Stackausrichtung, 5. und 6. Parameter). Andere dBASE-Codegenerator-Pfade und die
bestehenden String-Exports bleiben unverändert.

**Wichtig:** Wegen der neuen Export-Namen muss `libd64_qt5.dll` aus den aktualisierten
`d64qt5`-Quellen für PE32 und PE32+ neu gebaut und zum Programm ausgeliefert werden.
Die aktuellen DLL-Binärdateien aus Stage 457 enthalten diese fünf Exporte nicht.

## `Form1.ui.json`: Was ist tatsächlich in der EXE?

`external UI components` muss für die jeweilige Architektur eingeschaltet sein.
Die daneben angelegte `.ui.json` ist lediglich eine **lesbare Sidecar-Datei**.
Der Compiler serialisiert das Formular und bettet die Bytes direkt unter dem
Assembler-Symbol `__dbase_wfm_external_ui_payload` in `.data` des Programms ein.

- `compress json` **aus**: JSON-Bytes unkomprimiert in `.data`, unabhängig vom PE-Packer.
- `compress json` **an**: Qt-`qCompress`-kompatibel vor der Assemblierung komprimiert
  (4-Byte-Big-Endian-Länge + zlib), dann in `.data` gelinkt.
- Der vorhandene PE-D64Z/MSZIP-EXE-Packer verarbeitet **`.text`**, nicht automatisch
  `.data`. Er komprimiert deshalb die JSON-Bytes nicht noch einmal. Es wird
  keine separate `.ui.json` als eigene Datei in der EXE gelinkt.
- Die Qt5-Bridge liest den eingebetteten Datenblock beim Programmstart via
  `DBaseQtFormApplyExternalUi`. Kein JSON-Sidecar ist zur Laufzeit erforderlich.

Zum Nachweis im PE32/PE32+-Image (gepackter `.text`-Bereich ist unproblematisch):

```powershell
python -m d64dbase.wfm_external_ui "T:\\Pfad\\MeinProgramm.exe"
```

Die zusätzliche unabhängige Prüfroutine `find_embedded_form_ui()` erkennt die
beiden Stage-456-Payload-Varianten anhand der Bytes im PE-Image und gibt
Formularname, Offset, JSON-Rohgröße und Kompressionsstatus aus.

## Tests

- Native C++-Tests (g++, ohne Qt-Installation): `test_stage458_native_runtime.cpp`;
  Teilstring, Umlaute, scharfes s, ungültige/übergroße Grenzen, Lower und Upper.
- WFM-Compiler und vollständig gelinkte PE32-/PE32+-EXEs:
  `test_stage458_wfm_utf8_runtime.py`; einzelne und fusionierte Stringoperationen,
  Imports und JSON-Blöcke im **fertigen** gelinkten Image.
- Gezielte Regressionen einschließlich Stage 443–457: 114 bestanden,
  1 übersprungen (Linux-Testumgebung, kein nativer Windows-/Qt5-Ladevorgang).
- Stage-450/452/453-NTFS-Tests sind durch die Stage-455-Umstellung auf
  D64Z/MSZIP-DLL-Packing historisch überholt und weiterhin **nicht erfolgreich**;
  diese Tests dürfen nicht als Regression von Stage 458 interpretiert werden.

Ein realer Windows-`LoadLibrary`-/WFM-Laufzeittest mit neu gebauter Qt5-Bridge
ist weiterhin erforderlich. Das EXE-Packing selbst ist wegen der Windows-
Cabinet/MSZIP-Abhängigkeit unter Linux nicht ausgeführt worden.
