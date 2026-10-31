[Deutsch](STAGE511_RESOURCE_HEX_ALL_ENTRIES.md) | [English](STAGE511_RESOURCE_HEX_ALL_ENTRIES.en.md)

# Stage 511 – Ressourcen-Hexansicht für alle kompilierten Ressourcen

**Verbindliche Basis:** `d64_dism_asm_510.zip`.

## Ursache

Der Ressourcen-Compiler erzeugte beim Beispiel `Resource32.rc` bereits drei Binäreinträge: `STRINGTABLE (6)`/ID 1 (346 Byte), `STRINGTABLE (6)`/ID 2 (52 Byte) und `MENU (4)`/ID 100 (98 Byte). Der bisherige Hex-Tab zeigte lediglich `entry.data` des ersten/ausgewählten Eintrags. Beim Klick auf einen Typ-Hauptknoten (z.B. `MENU (4)`) fehlte zudem die dortige UserRole; `_resource_selected()` ließ deshalb den vorherigen Hex-Text unverändert stehen.

## Lösung

- **Standardmodus:** Im Hex-Tab ist `Alle Ressourcen anzeigen` aktiviert. Der Formatter `format_resource_collection_hex(...)` zeigt alle kompilierten Resources nacheinander in getrennten Abschnitten mit Typ, ID, Sprache, Codepage und Größe.
- **Einzelansicht:** Checkbox deaktivieren und den Eintrag unterhalb des Typs anklicken. Der Hex-Tab zeigt nur diesen Datensatz.
- **Typ-Ansicht:** Checkbox deaktivieren und `STRINGTABLE (6)` oder `MENU (4)` als Hauptknoten auswählen. Der Hex-Tab zeigt alle Ressourcen dieses Typs.
- **Aktualisierung:** Änderungen an RC-Quelltext/Codepage und neue Ressourcen werden in der Übersicht, der Gruppenansicht und der Einzelansicht aktualisiert. Die Eigenschaften-Tabelle bleibt pro Einzeleintrag.
- **Offsets:** Beginnen in jedem Abschnitt bei `00000000` und beziehen sich nur auf die Nutzdaten des Eintrags; die `.res`-Headers liegen nicht in dieser Ansicht. Es handelt sich ausdrücklich nicht um einen zusammenhängenden Dump des `.res`-Dateiformats.
- **Binärtreue:** Weder die Daten noch RES-/COFF-Ausgaben werden konvertiert. Die bisherige Codepage-basierte STRINGTABLE-Textvorschau bleibt unverändert.
- **Nicht kompilierte Vorlagen:** Diese gehören nicht zur Gesamtübersicht der binären Ressourcen. In der Einzelansicht zeigt ihre Auswahl weiterhin die bekannte Meldung, dass keine Binärdaten vorliegen.

## Beispiel

```text
Ressourcen-Hexansicht: 3 Einträge, 496 Bytes Nutzdaten
...
============ [1/3] STRINGTABLE (6) | ID 1 | LANGID 0x0407 | 346 Bytes | Codepage 1200 ============
Offset    Hex-Bytes ...
00000000  00 00 0C 00 44 00 65 00 | 75 00 74 00 73 00 63 00 ...
...
============ [2/3] STRINGTABLE (6) | ID 2 | LANGID 0x0407 | 52 Bytes | Codepage 1200 ============
Offset    Hex-Bytes ...
...
============ [3/3] MENU (4) | ID 100 | LANGID 0x0407 | 98 Bytes | Codepage 1200 ============
Offset    Hex-Bytes ...
00000000  00 00 00 00 10 00 44 00 | 61 00 74 00 65 00 69 00 ...
```

## Geänderte Dateien

- `d64_dism.py`: Gesamt-Formatter und Hex-Modus-Umschaltung, markierte Gruppen-Knoten, synchronisierte Neuzeichnung.
- `test_stage511_resource_hex_complete.py`: echte RC-Menü-Compilerprüfung, alle drei Hex-Abschnitte, Filter- und Umschaltlogik.

## Tests

- `python -m pytest -q test_stage457_resource_editor_menu_workspace_templates.py test_stage501_session_designer.py test_stage502_session_method_binding.py test_stage503_session_wfm_compile.py test_stage504_resource_hex_codepage.py test_stage505_resource_codepage_live_refresh.py test_stage506_resource_source_codepage_hex_sync.py test_stage507_resource_hex_nulls_groups.py test_stage508_resource_hex_stringtable_preview.py test_stage509_resource_tree_context_menu.py test_stage510_resource_tree_save_menu.py test_stage511_resource_hex_complete.py`: **132 bestanden**.
- Python-Syntaxprüfung erfolgreich. ZIP-Integrität wird beim Erstellen geprüft.
- Die native PyQt5-GUI konnte hier nicht gestartet werden (PyQt5 ist nicht installiert). Sichtprüfung unter Windows bleibt erforderlich.
