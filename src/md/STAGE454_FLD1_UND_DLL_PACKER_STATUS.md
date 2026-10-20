# Stage 454: FLD1 im internen PE32/PE32+-Assembler

Verbindliche Basis: `d64_dism_asm_453.zip`.

## Reparatur: `fld1`

Der WFM-Generator erzeugt bei aktiviertem `const pool` für den Double-Wert
`1.0` die x87-Instruktion `fld1`. Der PE32-Assembler hatte diesen Befehl
weder in der Größenermittlung noch im Byte-Encoder implementiert.

Korrigiert in `d64_dism.py`:

- PE32: Größenermittlung: 2 Bytes; Kodierung: `D9 E8`.
- PE32+: Byte-Encoder: `D9 E8`.
- `fldz` (`D9 EE`) bleibt unverändert.
- WFM `const pool` mit Zahlenliteral `1` bis zur vollständigen PE32-
  bzw. PE32+-EXE-Verlinkung getestet.

## Kein ungesicherter DLL-Packer

Die vorhandene D64Z/MSZIP-EXE-Packer-Implementierung wurde **nicht** direkt
für `c64_dbase_runtime.dll` freigeschaltet. Grund: DLL-spezifische PE
Lade-Semantik. Das ist ausdrücklich eine noch offene Implementierungsaufgabe;
`pack dll` verwendet in Stage 454 weiterhin den NTFS-Weg von Stage 453.

Der bereits erzeugte Runtime-Stand weist im ausführbaren `.text`-Bereich
folgende *Original-PE-Relocations* auf:

- PE32: 43 `IMAGE_REL_BASED_HIGHLOW`-Positionen
- PE32+: 6 `IMAGE_REL_BASED_DIR64`-Positionen

Die vorhandene EXE-D64Z-Routine ist im Linker explizit mit `not dll` gesperrt.
Würde man lediglich diese Sperre entfernen, entpackte die Runtime den
Maschinencode erst **nachdem** der Windows-PE-Loader die Base Relocations
angewandt hat. Die Codezeiger im wiederhergestellten Text enthielten dann
weiter die ursprüngliche ImageBase. Zudem erwartet der EXE-Entpacker keinen
`DllMain(HINSTANCE, DWORD, LPVOID)`-Aufruf und behandelt Fehler als
`ExitProcess`, was für eine DLL unzulässig ist.

Für eine korrekte DLL-Erweiterung des bestehenden Packers ist notwendig:

1. DLL-spezifischen Entry-Adapter erzeugen, der die drei DllMain-Argumente
   sichert und sie an die originale Routine weiterleitet.
2. Die `.text`-Base-Relocations aus der normalen Loader-Relocationbehandlung
   ausklammern und **nach der Entpackung** mit der realen ImageBase anwenden.
3. Relocations und importierte API-Verweise des Entpackers selbst korrekt
   in der neuen PE-Relocation-/Importtabelle verwalten.
4. Exports und ihre RVAs in `.edata` beibehalten, und nur nach erfolgter
   Rekonstruktion der ausführbaren Section in diese Funktionen springen.
5. Auf einem echten Windows-Rechner `LoadLibrary`, `GetProcAddress`,
   Aufruf aller Exporte sowie Freigabe und Laden an verschobener ImageBase
   für PE32/PE32+ prüfen.
6. Falls der gepackte PE-Dateiinhalt nicht kleiner wird, unverpackt bleiben.

Die aktuelle Komprimierungsoption, Einstellungen und Menüs sind absichtlich
unangetastet, damit keine möglicherweise nicht ladbare DLL entsteht.
