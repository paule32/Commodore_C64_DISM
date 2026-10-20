# Stage 451 – WFM-Code-/Datenoptimierung und NTFS-Komprimierung

**Verbindliche Basis:** `d64_dism_asm_450.zip`. Änderungen nur an
`d64_dism.py`, `d64dbase/pe_dll_pack.py` sowie neu
`d64dbase/wfm_optimizer.py` und den Stage-451-Tests.

## 1. NTFS-Fehler 5 bei „pack dll“

`set_ntfs_compression()` versucht die Komprimierung weiterhin über
`FSCTL_SET_COMPRESSION`. Der Handle wird jetzt mit `GENERIC_READ | GENERIC_WRITE`
geöffnet, um abweichende Windows-Zugriffskontrollen zu berücksichtigen.
Bei Zugriffs-/Freigabefehler 5/32 bzw. errno 5/13/32 folgt als zweiter
**Windows-eigener** Weg `compact.exe /C /I /Q <DLL>`. Der Komprimierungsstatus
wird danach per `GetFileAttributesW` überprüft, der PE-Dateiinhalt per SHA-256.
Andere Fehler werden nicht kaschiert. Wenn beide Verfahren fehlschlagen,
bleibt ein vorhandenes gültiges Ausgabeartefakt erhalten und es erscheint
eine konkrete Meldung über NTFS/Schreibrechte/Dateisperre.

Dies ist **NTFS-Dateisystemkomprimierung**, keine selbstentpackende, portabel
gepackte PE-Datei. Das NTFS-Komprimierungsattribut bleibt beim Kopieren oder
ZIP-Archivieren nicht unbedingt erhalten. Das PE-Format bleibt Windows-ladbar.
Ein geschützter Ordner oder ein nicht-NTFS-Dateisystem kann nicht per Code
umgangen werden.

## 2. Checkbox „const pool“

Unter Windows → 32-Bit / 64-Bit → Umgebung → Eingabe → dBASE Runtime befindet
sich eine zweite, standardmäßig deaktivierte Checkbox `const pool`.
Sie wird **je Zielarchitektur** separat als `DBaseRuntimeConstPool` in
`Settings.Windows.32Bit.Environment` beziehungsweise
`Settings.Windows.64Bit.Environment` der Projektdatei gespeichert.

Bei Aktivierung verwendet die WFM-Codegenerierung einen binär exakten
IEEE-754-Schlüssel zur Wiederverwendung identischer 64-Bit-Zahlenkonstanten.
Dies erhält den Unterschied zwischen `+0.0` und `-0.0` sowie spezielle
Bitmuster. Vergleiche mit der einfachen positiven `0` und `1` benutzen zudem
`fldz`/`fld1`, sofern dies ohne Änderung der Vorzeichenbit-Semantik möglich ist.
Ohne Aktivierung bleibt die bisherige Einzelkonstanten-Erzeugung erhalten.

## 3. Sprungoptimierung (Priorität 2)

`d64dbase.wfm_optimizer.optimize_wfm_branches()` optimiert nur die automatisch
erzeugten `__dbase_wfm_flow_*`-Kontrollflussmarken. Ein bedingter Sprung über
einen unbedingten Sprung wird mit invertierter Bedingung verkürzt; direkte
Sprünge zum unmittelbar folgenden Label entfallen. Kommentare,
handgeschriebene Labels, Fremd-Labels und nicht benachbarte Instruktionen
werden nicht verändert. Die Optimierung ist unabhängig von `const pool` aktiv.

## 4. Property-Tabellen-Deduplizierung (Priorität 3)

Bereits internierte Property-Strings werden nun zusätzlich zur Wiederverwendung
**vollständiger identischer Property-Datensatzfolgen** genutzt. Die DATA-Tabelle
wird nur einmal erzeugt, die Aufrufstellen verwenden dieselbe unveränderliche
Tabellenadresse. Das bisherige kompakte PE32-/PE32+-Recordformat bleibt
unverändert. Die Optimierung ist unabhängig von `const pool` aktiv.

## 5. Teststand und Einschränkungen

- Stage 451: 8 neue Tests: Persistenz-/GUI-Anbindung, beide Architekturen,
  DLL-kompatible WFM-EXE-Linktests, Property-Deduplizierung und
  NTFS-Access-Denied-Fallback-Simulation.
- Regressionen Stages 441–450: 107 weitere Tests erfolgreich.
- 27 Projektverwaltungstests erfolgreich.
- 43 ältere GUI-Tests haben alle Testfälle bestanden, der gemeinsame
  Pytest-Prozess wurde nach dem Testlauf jedoch nicht beendet.
- Python-Syntax, COFF/PE32/PE32+-Linkpfade und ZIP-Integrität überprüft.
- **Kein direkter Windows-/NTFS-Laufzeittest** in dieser Umgebung möglich;
  insbesondere darf Erfolg des kompakten Windows-Fallbacks unter den
  konkreten Dateisystem- und Berechtigungsverhältnissen nicht unterstellt werden.

Beispiel `TestAndNotXor`: 9 auf 2 Zahlkonstanten, Assemblertext
PE32/PE32+ um jeweils 431 Zeichen kürzer (Vergleich `const pool` an/aus,
alle anderen Stage-451-Optimierungen identisch).
