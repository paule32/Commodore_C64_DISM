# Stage 533 — Korrektur für Foo.Free / _jit_free (PE32)

## Fehler

Das hochgeladene `test_raise(3).exe` besitzt einen D64Z/MSZIP-komprimierten
PE32-Programmcode. Die Zeichenkette `ennndddeee` ist im komprimierten Image
vorhanden und der Aufruf zu ihrer Ausgabe liegt im Normalzweig nach dem
`try..finally`-Block. Der Ablauf endet jedoch bei `Foo.Free` nach dem Aufruf
der Destruktorkette, weil die zugehörige `libd64_runtime.dll` in `_jit_free`
eine endlose Rekursion enthält.

`jit_object_free` -> VMT.Destroy (TFoo, TFaz) ->
`jit_object_instance_free` -> `_jit_free` -> `_jit_free` -> ...

Quelle in Stage 532:
`runtime/compiler/memory.cc`, Funktion `_jit_free`.
`runtime/memory.cc` hatte diesen Fehler bereits korrigiert.

## Änderung

Die fehlerhafte Funktion verwendet jetzt den geladenen `msvcrt.dll`-Import
`p_free(ptr)` statt sich selbst aufzurufen. Das ist die eigentliche
Quellcodekorrektur. Der Quellcode der Qt5-DLL wurde nicht verändert.

Die drei identischen ausgelieferten Kopien von `libd64_runtime.dll` enthalten
zudem eine **gezielte Binärkorrektur** des vorhandenen PE32-Builds. Es wird
lediglich ein relativer `CALL` geändert:

* RVA 0x23D4: früheres Ziel `_jit_free` (RVA 0x23B6)
* neues Ziel `_jit_dispose_memory` (RVA 0x2217)

`_jit_dispose_memory` übergibt den bereits auf dem Stack liegenden Zeiger an
`p_free` über die gleiche cdecl-ABI. Der PE-Checksum-Wert wird korrigiert.
Der Binärpatch ist als sofort testbarer
Hotfix gedacht; ein vollständig **neu aus den korrigierten Quellen gebautes**
DLL ist für spätere Veröffentlichungen zu bevorzugen. Die normale DLL-Größe,
Exporttabelle und Importnamen bleiben unverändert.

## Windows-Test

1. Alte `libd64_runtime.dll` sichern.
2. `libd64_runtime.dll` aus Stage 533 bzw. der separaten Hotfix-ZIP neben
   `test_raise.exe` kopieren. Andere gleichnamige DLLs in DLL-Suchpfaden
   vermeiden. `libd64_qt5.dll` nicht ersetzen.
3. `test_raise.exe` aus der Eingabeaufforderung starten.
4. Nach `TFaz Destroy` sollte nun der normale Ablauf zurückkehren und
   `ennndddeee` sichtbar werden.
5. Weiterhin `Application.Free` prüfen, da es denselben Runtime-Pfad verwendet.

### Einschränkung

Eine native Windows-Ausführung der DLL/EXE war in der Analyseumgebung nicht
möglich. Bestätigt sind die fehlerhafte DLL-Disassemblierung, die
Quellcodekorrektur, die Binärpatch-Adressen und die Integrität des ZIPs.
Damit ist die Ursache nachgewiesen, eine Laufzeitbehebung auf Windows aber
noch nicht bestätigt. Die DLL ist ein PE32-Build für 32-Bit-Prozesse.
