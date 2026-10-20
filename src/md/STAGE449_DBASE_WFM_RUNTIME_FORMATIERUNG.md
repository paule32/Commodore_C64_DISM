# Stage 449 – gemeinsame dBASE/WFM-Runtime-Formatierung

**Verbindliche Basis:** `d64_dism_asm_448.zip`. Die Datei `c64_dbase_runtime.dll` bleibt die **einzige dBASE-Runtime-DLL**. Keine neuen Menüeinträge und keine Änderungen an den Architektur-/Zielverzeichnis-Feldern in den Projekteinstellungen.

## Neue Exporte (in beiden DLL-Architekturen)

* `DBaseStringLengthN(const char *text, uint32_t maximum) -> uint32_t`: nullsichere, **begrenzte Byte-Längenmessung**; insbesondere für den 96-Byte-WFM-Zahlenformatpuffer, nicht als Unicode-Codepoint-Zähler.
* `DBaseWfmClassifyType(uint32_t type) -> uint32_t`: `0` für NULL/unbekannt, `1` für STRING (`type=3`), `2` für OBJECT (`type=4`), `3` für NUMBER (`type=1,2`). Innerhalb der Formatierungsroutine wird die gleiche kürzere **Inline-Klassifikation** benutzt (STRING/OBJECT-Vergleich und numerischer Bereichstest) statt je fünf Einzelvergleichen. Ein DLL-Funktionsaufruf pro Kleintypprüfung wird vermieden.
* `DBaseWfmFormatValue(const ValueSlot *value, char *numeric_buffer, FormatResult *result) -> void`: Formatierung aller WFM-Werte. STRING gibt den ursprünglichen Pointer und seine explizite **UTF-8-Bytelänge** zurück, OBJECT mit gültigem Pointer liefert `<object>`, NULL sowie unbekannte/ungültige Pointer liefern `<null>`. INTEGER/FLOAT werden weiter mit `_gcvt(..., 15, ...)` formatiert und durch `DBaseStringLengthN(...,96)` auf eine maximal 96 Bytes lange Suche begrenzt. Nur die **Textaufbereitung**, nicht die Qt5-Ausgabe, wird verlagert.

### Übergabe und Datenlayout

Die beiden internen Assemblerziele benutzen dieselbe API unter ihrem jeweiligen ABI: **PE32** `cdecl` (Aufrufer räumt Argumente ab); **PE32+** Windows-x64 (RCX, RDX, R8 + reservierter Shadow Space). Die `ValueSlot`-Daten sind wie im bestehenden WFM-Compiler direkt hintereinander in `.bss` abgelegt und brauchen deshalb keine zusätzliche Kopie:

| Feld | PE32 Offset | PE32+ Offset |
|---|---:|---:|
| `uint32 type` | 0 | 0 |
| `double number` | 4 | 4 |
| `char *pointer` | 12 | 12 |
| `uint32 length` | 16 | 20 |

`FormatResult`: `pointer` bei Offset 0 und `uint32 length` an Offset 4 / 8. Die zurückgegebenen Pointer zeigen in das bestehende Slot- oder Formatpufferspeichergebiet beziehungsweise auf DLL-interne Konstanten. Der Aufrufer behält die Kontrolle über die Lebensdauer und ruft **anschließend** `DBaseQtConsoleWrite(pointer, length, newline)` auf. Kein Qt-Import in der Runtime.

### Änderung am WFM-Ereigniscode

Früher wurde **für jede `?`-/`??`-Ausgabe eines Memory-Slots** die Typverzweigung samt gesonderter `strlen`-Schleife und `_gcvt`-Aufruf ausgegeben. Ab Stage 449 wird die Adresse des zusammenhängenden Memory-Slots sowie der vorhandene Zahlenpuffer an die gemeinsame `DBaseWfmFormatValue`-Funktion übergeben. Danach folgt nur noch die bekannte Qt5-Ausgabe. Die bisherige 96-Byte-Pufferreservierung im WFM-Startpfad bleibt erhalten.

## Toolchain und Bereitstellung

Die zwei bestehenden Wege aus Stage 447 („Werkzeuge → dBASE Runtime PE32/PE32+ DLL erstellen“ sowie „Projekt-Einstellungen → Umgebung → dBASE Runtime DLL erstellen“) verwenden unverändert `d64dbase.runtime_builder.create_runtime_dll`. Die Exportprüfung berücksichtigt nun elf Exporte statt acht; ältere DLLs mit nur acht Exporten sind nicht kompatibel und werden durch die neuere Projektdatei ersetzt. Auch die automatische Bereitstellung neben den erzeugten EXE-Dateien bleibt aktiv.

| Ziel | Gepackte DLL |
|---|---|
| PE32 | `d64dbase/bin/pe32/c64_dbase_runtime.dll` |
| PE32+ | `d64dbase/bin/pe64/c64_dbase_runtime.dll` |

## Regression und Abgrenzung

Tests liegen in `test_stage449_wfm_format_runtime.py` und den bisherigen Stage-Tests. Geprüft werden 11 reale DLL-Exporte, COFF/PE-Link, der symbolgenaue Slotaufbau, Formatter-Aufrufe für mehrere WFM-Ausgabeanweisungen, die Wiederverwendung des Build-Menüs, Null-/Typsemantik und Byte-Längenbegrenzung. **Windows-Laufzeitausführung wurde hier nicht durchgeführt.** Multithread- oder parallele Ausgabepfade sind unverändert durch die bereits zuvor gemeinsam genutzten WFM-Zahlenpuffer eingeschränkt.
