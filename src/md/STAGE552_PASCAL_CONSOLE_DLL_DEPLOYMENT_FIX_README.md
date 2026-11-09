# Stage 552 – Pascal-EXE startet nach DLL-Build nicht

**Verbindliche Basis:** `d64_dism_stage551.zip`.

## Nachweis aus `packed(9).zip` (8. November 2026)

Das gemeldete Archiv enthält `test_raise.exe`, `test_raise.exe.imports.json`,
`Runtime.dll`, `libd64_runtime.dll` und `libd64_qt5.dll`. Die separat zu
übersetzende **`libd64_console.dll` fehlt**.

Die unveränderte Stage-541-Importliste des EXE-Links weist fünf Imports aus
`libd64_console.dll` aus:

- `d64_console_init`
- `d64_console_newline`
- `d64_console_read_string`
- `d64_console_restore`
- `d64_console_write_text`

Außerdem importiert die mitgelieferte `Runtime.dll` direkt
`d64_console_write_text` und `d64_console_newline` aus derselben DLL.
Alle untersuchten `Runtime.dll`-/`libd64_runtime.dll`-Exports stimmen mit
den dazugehörigen im Archiv vorhandenen Importanforderungen überein.
`test_raise.exe` ist mit dem D64Z/MSZIP-Loader komprimiert. Sein äußeres
PE-Importverzeichnis führt daher primär `cabinet.dll` und `kernel32.dll` auf
und ist **nicht** der vollständige DLL-Abhängigkeitsnachweis. Hierzu muss
`test_raise.exe.imports.json` ausgewertet werden.

Die fehlende Konsolen-DLL ist ein belegter möglicher Startblocker; ohne
Windows-Ausführung und ohne die auf dem Nutzerrechner tatsächlich vorhandenen
Dateien können wir andere Laufzeitfehler nicht ausschließen.

## Warum Stage 551 die Datei nicht immer bereitgestellt hat

In der IDE prüfte die Routine `_stage551_deploy_pascal_console` ihren Bedarf
über einen literalen Suchbegriff im sichtbaren `assembly_source` – und
**erst nach der UI-Meldung** „ASM-Tab erfolgreich assembliert“.
Wenn die Stage-550-Option „Import-Deklarationen in .inc auslagern“ aktiviert
war, stand der Import jedoch nur in der Include-Datei bzw. im Linkmanifest.
Das erlaubte einen scheinbar erfolgreichen Build ohne passende Konsolen-DLL.

## Umsetzung in Stage 552

1. Neue pure-Python-Hilfsdatei `pascal_console_dependencies.py` analysiert
   PE32-/PE32+-Import- und Exporttabellen (ohne externe Python-Pakete),
   das Importmanifest und direkte DLL-Abhängigkeiten von `Runtime.dll`.
2. Die IDE entscheidet **anhand des Linkmanifests**, ob `libd64_console.dll`
   benötigt wird; dies funktioniert auch bei `%include` und bei komprimierten
   EXEs. Die ermittelten DLL-Imports einer lokal vorhandenen `Runtime.dll`
   zählen ebenfalls.
3. Passende `libd64_console.dll` wird **vor einer Erfolgsmeldung** aus dem
   lokalen architekturspezifischen Buildverzeichnis in den EXE-/DLL-Ausgabeordner
   kopiert. Auch eine schon vorhandene DLL wird auf PE-Architektur und alle
   im Link tatsächlich benötigten Exportnamen geprüft.
4. Fehlt die DLL, ist sie aus einer anderen Architektur oder fehlen Exporte,
   bricht die IDE die Erfolgsmeldung ab und protokolliert den Fehler.
5. Die ursprüngliche Prüfung allein gegen `assembly_source.casefold()`
   nach der Erfolgsmeldung entfällt.
6. `test_stage552.py` testet den PE-Leser, Manifest-/Transitiv-Abhängigkeiten,
   Bereitstellung und fehlerhafte/mismatched Exporte. Der veraltete
   Strukturtest in `test_stage551.py` prüft nun die Exportverifikation.

## Reparatur auf dem Windows-Rechner

In der **MSYS2 MINGW32**-Konsole im Projektverzeichnis
`T:\GitHub\dBase2Many\src\asmjit\compiler\frontend\c64`:

```bash
cd runtime/compiler
bash build.console.win32.sh
cp win32/libd64_console.dll ../pascal/test/pe32/libd64_console.dll
```

Wenn dein Projekt einen anderen Ausgabepfad nutzt, die DLL entsprechend
**neben `test_raise.exe`** kopieren. Eine `libd64_console.dll.a` ist nur zum
GCC-Linken gedacht, nicht als Ersatz für die DLL zur Laufzeit.

Symbole prüfen:

```bash
objdump -p ../pascal/test/pe32/libd64_console.dll | grep d64_console
```

Die Ausgabe muss die importierten Namen enthalten. Mit Stage 552 kann der
aktuelle Ausgabeordner zudem nach dem Bauen geprüft werden:

```bash
python pascal_console_dependencies.py runtime/pascal/test/pe32
```

PE32 und PE32+ dürfen keine DLLs gegenseitig austauschen. Für PE64 die
`build.console.win64.sh` und das passende Ausgabeziel verwenden.

## Nachweise / Grenzen

- Das hochgeladene `packed(9).zip` wurde als **PE32** statisch analysiert.
- Die 29 gezielten Tests aus `test_stage550`, `test_stage551` und
  `test_stage552` bestanden.
- Die ursprünglich fehlende DLL ist **nicht im Archiv**; Stage 552 kann nicht
  rückwirkend eine DLL in das bereits erstellte, hochgeladene ZIP hineinfügen.
- Ein nativer Windows-Build/EXE-Start mit der neu gebauten DLL war in dieser
  Laufzeitumgebung nicht verfügbar. Die funktionierende Windows-Ausführung
  bleibt daher unbestätigt.
