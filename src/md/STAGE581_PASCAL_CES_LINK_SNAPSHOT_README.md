# Stage 581 – CES-Einstellung bis zur Pascal-PE32-EXE verbindlich weiterreichen

**Basis:** `d64_dism_stage580.zip` (ohne Änderungen am Pascal-Frontend oder der Runtime-DLL).

## Fehlerbild und Ursache

Die Einstellung **Windows → 32-Bit → Debug → CES - Check Early Start**
wird in der `.pro`-Projektdatei korrekt als `CheckEarlyStart = false` erfasst.
Der UI-Wechsel synchronisierte den bisher global gespeicherten Wert zwar,
aber der Linker nahm ihn nochmals unabhängig aus `stage527_debug_options('pe32')`.
Das war in der IDE besonders problematisch bei Fallbacks auf frühere Writer-
Stufen oder wenn die globalen Einstellungen zwischenzeitlich geändert wurden.
Es gab somit **keinen unveränderlichen CES-Wert als Teil des Linkauftrags**.

Die eigentliche Loader-Implementierung bedingt CES bereits korrekt: Bei
`ces_enabled=False` enthält der Loader keine CES-spezifische `MessageBoxA`-
Diagnose und keine CES-Fehlertexte. Das generelle D64I-DLL-Resolving (inklusive
`LoadLibraryA` / `GetProcAddress`) bleibt technisch erforderlich und ist
**nicht** mit CES-Diagnosecode zu verwechseln.

## Korrektur

- Im Hauptpfad `assemble_generated_document()` wird der aktuell sichtbare
  Debug-Checkbox-Zustand einmal zu Beginn des Linkvorgangs in
  `ces_for_build` gesichert.
- Ausschließlich der PE32-Linker erhält `ces_enabled=bool(ces_for_build)`.
  Der PE64-Linker bleibt unverändert.
- Der ausdrückliche Wert wird von `link_coff32_inputs()` über
  `link_coff32_objects()` und die vier Stage-Writer-/Wrapper-Ebenen bis zu
  `_build_pe32_mszip_loader()` übertragen, inklusive Stage-169-Fallback,
  Stage-209-D64I-Packer, Größenvergleich und optionalem komprimiertem Loader.
- `_pe32_rebuild_with_mszip_loader()` erhält den gleichen expliziten Parameter.
- Für externe/Legacy-Aufrufer ohne `ces_enabled` bleibt die bisherige
  Kompatibilität zum globalen Debug-Profil bestehen.
- Das Protokoll vermerkt den echten Build-Snapshot als `PE32 CES (Link-Snapshot):
  ON` oder `OFF`.

## Testnachweise

`python -m pytest -q test_stage581.py test_stage549.py`

**11 Tests erfolgreich** (5 neue und 6 Stage-549-Tests).

Die neuen Tests prüfen:
1. Projekt-CES OFF trotz bewusst auf ON gesetztem globalen Debug-Zustand.
2. Weitergabe des Werts vom Stage-172-Wrapper über Stage-209 und Stage-169 bis
   zum Loader-Rebuild; danach Gegenprobe CES ON.
3. Echte PE32-Loaderbytes mit und ohne CES-Meldungstexte/`MessageBoxA`.
4. Speichern und Einlesen von `CheckEarlyStart = false` für PE32 bei
   unabhängig aktiviertem PE64-Profil.
5. Durchgängige Parameterweitergabe vom GUI-Build und COFF-Eingang.

**Einschränkungen:** Die Testumgebung kann weder die native PyQt5-Oberfläche
noch eine Windows-EXE starten. Der Test der gesamten Parameterkette verwendet
an der Übergabe vom Writer zum finalen Loader-Rebuild einen Test-Dummy;
der Loader selbst wird zusätzlich als realer Maschinenbyte-Stream geprüft.
Ein vollständiger EXE-Roundtrip unter Windows sollte erfolgen.

## Windows-Gegenprobe

1. In `pascal.pro` CES für **Windows → 32-Bit → Debug** deaktivieren.
2. Pascal-Programm neu kompilieren, assemblieren und **linken**.
   Nicht eine alte EXE über `Start` verwenden.
3. Im Protokoll `PE32 CES (Link-Snapshot): OFF` prüfen.
4. Bei erneutem Aktivieren und Linken `...: ON` erwarten.
5. Bei CES OFF dürfen im **tatsächlich erzeugten** PE32-Loader keine
   CES-Fehlertexte `CES: LoadLibraryA failed (DLL)` oder
   `CES: GetProcAddress failed (symbol)` und kein CES-`MessageBoxA`-Pfad
   vorhanden sein. Ein komprimierter Loader muss vor einer Textsuche
   dekomprimiert werden.

**Anmerkung:** `CES` steuert die zusätzlichen diagnostischen Fehlerpfade des
Bootstrappers, **nicht** den gesamten Bootstrapper. Für gepackte EXEs bleiben
`.loader`, `LoadLibraryA` und `GetProcAddress` auch bei CES OFF erforderlich.
