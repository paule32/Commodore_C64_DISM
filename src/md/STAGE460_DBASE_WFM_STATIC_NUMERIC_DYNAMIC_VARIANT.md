# Stage 460 – dBASE/WFM Speicheroptimierung (PE32 und PE32+)

**Verbindliche Basis:** `d64_dism_asm_459.zip`.

## Projekt-Einstellungen

Der bestehende Navigationsknoten `Compiler → dBASE → Optimierung` erhält rechts unterhalb von `Visuelle Elemente` die GroupBox **Variablen und Speicher**:

* **static numeric internal slots** (Standard: aus): Nur vom WFM-Compiler generierte und dauerhaft numerische temporäre Slots erhalten die ursprüngliche ABI-kompatible Struktur (`type`, `num`, `ptr`, `len`) mit einmalig gesetztem `type=1` und `ptr=len=0` in initialisierten Daten. Der Eventcode speichert nur den Double-Zahlenwert. Das betrifft u.a. `ISKEYBOARD`/`ISMOUSE`-Druckwerte, direkte `ISUPPER`/`ISLOWER`-Druckwerte und die Ausgabeslots von `LEN`. Namen, die im WFM-Quelltext explizit vorkommen, bleiben aus Vorsicht dynamisch.
* **dynamic typed variables** (Standard: aus): Häufig wiederholte numerische Typ- und Nullfeld-Zuweisungen und vollständige Variant-Kopien rufen einen eigenen gemeinsamen Inline-Helfer in `.text` auf. Zwei mögliche interne Labels: `__dbase_wfm_assign_numeric_header` und `__dbase_wfm_copy_variant`. Die Helfer werden ausschließlich bei tatsächlicher Verwendung emittiert. String- und Objekt-Zuweisungen nutzen weiter die bisherigen korrekten Pointer-/Längenpfade.

Die Schalter sind unabhängig voneinander und unabhängig von `external UI components` und `compress json`. Die Einstellungen werden je Architektur in den INI-Sektionen `Settings.Windows.32Bit.Compiler.dBASE.Optimierung` beziehungsweise `Settings.Windows.64Bit.Compiler.dBASE.Optimierung` unter `StaticNumericInternalSlots` und `DynamicTypedVariables` gespeichert. Die internen Keys heißen `__windows_pe32_dbase_static_numeric_slots__`, `__windows_pe32_dbase_dynamic_typed_variables__` und analog für `pe64`. Ältere Projekte laden beide Optionen als `false`.

## Unveränderte WFM-Slot-ABI

| Feld | PE32 Offset / Größe | PE32+ Offset / Größe |
| --- | --- | --- |
| `type` | 0 / 4 | 0 / 4 |
| `num` | 4 / 8 | 4 / 8 |
| `ptr` | 12 / 4 | 12 / 8 |
| `len` | 16 / 4 | 20 / 4 |

Die Optimierungen verändern **keine** externen DLL-Exporte und keinen Loader-ABI-Vertrag. Dynamische dBASE-Variablen werden nicht als statisch numerisch eingestuft; beim Zuweisen einer Zahl werden Typ, Pointer und Länge auch nach einem vorausgehenden String-Wert korrekt aktualisiert. `__dbase_wfm_copy_variant` kopiert sämtliche Felder. Der gemeinsame Helper verwendet nur volatile Register und erhält den x87-Nutzwert beziehungsweise überträgt ihn vollständig.

Hinweis: Der bestehende PE32-Linker kann initialisierte `.data` zusammen mit dem Code in einer **schreibbaren `.text`-Sektion** ablegen. Bei PE32+ erscheint `.data` getrennt. Der Generator stellt `.data` ausdrücklich bereit, aber die endgültige Sektionsstruktur hängt vom internen PE-Linker ab. Das ist keine Änderung von Stage 460.

## Größenvergleich eines Event-Testformulars

Gemessen am Testformular mit mehrfach `ISKEYBOARD`, `ISMOUSE`, `LEN`, `ISUPPER` sowie `STORE`-Typwechsel und Variant-Kopie. Ausgegeben sind virtuelle `.text`-Bytes (PE-Sektionsausrichtung nicht berücksichtigt):

| Optionen `static`/`dynamic` | PE32 `.text` | PE32+ `.text` |
| --- | ---: | ---: |
| aus / aus | 2406 | 3014 |
| an / aus | 2330 | 2838 |
| aus / an | 2294 | 2950 |
| an / an | 2314 | 2838 |

Die wirkliche Dateigröße der Test-EXE bleibt wegen der PE-Dateiausrichtung bei PE32 **4.096** und bei PE32+ **5.120 Bytes**. Die absolute Ersparnis ist formularabhängig; bei kleinen Formularen kann die Kombination wegen der zusätzlichen Helfer geringfügig mehr Code benötigen als eine Einzeloption. Es wird keine Byte-Einsparung garantiert, sondern durch beide Checkboxen nur der jeweils ausgewählte Codegenerierungsweg gesteuert.

## Prüfungen

* `python -m py_compile d64_dism.py`
* `pytest` gegen Stage 441/443/445–449/451/454–460, ohne obsolete NTFS-Stages 450/452/453: **154 bestanden, 1 übersprungen**.
* Acht echte Builds mit internem COFF-Assembler/PE-Linker: PE32 und PE32+ × 4 Schalterkombinationen; verifiziert `MZ`, interne Helfersymbole, richtige Slot-Offsets und statische/variable Slot-Ausgabe.
* Zusätzlicher Alias-Regressionsfall für explizit benannte interne WFM-Variablen.

Ein interaktiver Windows-/PyQt5-GUI-Laufzeittest ist in dieser Umgebung nicht möglich; PE-Builds und Projekt-/Quelltextprüfung sind hingegen durch Tests belegt.
