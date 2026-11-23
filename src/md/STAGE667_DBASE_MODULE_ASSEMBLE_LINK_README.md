# Stage 667 – dBASE Module: COFF-Assembler und PE-Linker getrennt

Verbindliche Basis: **d64_dism_stage666.zip**. Die Änderung ist auf die
ausgewählten Blätter unter **Projekt-Informationen → dBASE Programme → Module**
und Windows PE32/PE32+ beschränkt. Andere dBASE-/Pascal-Buildabläufe bleiben erhalten.

## Bedienung

1. Unter **dBASE Programme → Programme** das Hauptprogramm (*.prg) normal
   kompilieren und in dessen erzeugtem ASM-Tab **Assemble** ausführen.
   Dadurch existiert die zur Architektur passende **`Hauptprogramm.o`**.
   Der bisherige Programme-Build kann zusätzlich eine EXE erzeugen.
2. Unter **dBASE Programme → Module** das gewünschte `.prg`-Blatt auswählen
   und zu editierbarem Assemblertext kompilieren.
3. Im erzeugten Assembler-Tab des Moduls steht **Assemble | Link**.
   **Start** ist zunächst unsichtbar.
4. **Assemble** erzeugt **nur** ein relocierbares Microsoft-COFF-Objekt
   (`.o`, i386 für PE32, AMD64 für PE32+); kein PE wird an dieser Stelle gelinkt.
5. **Link** prüft beide Objekte und linkt das Hauptprogramm zusammen mit dem
   ausgewählten Modul zu einer Windows-EXE im konfigurierten Ausgabeordner.
   Der EXE-Dateiname folgt dem Projektnamen, z. B. `AppDB.exe`.
6. Erst nach erfolgreichem Link erscheint **Start** und startet die erzeugte EXE,
   ohne sie erneut zusammenzubauen.

Die Buttons werden anhand des *aktuell ausgewählten Projektbaumblatts*
gesteuert. Die Freigabe von Start wird zurückgenommen, wenn der ASM-Text
oder ein beteiligtes `.o` nach dem Link verändert wird. Die normale
Pascal-/dBASE-Programme-Ansicht behält ihren ursprünglichen Ablauf.

## COFF-Symbole und Einstieg

Der dBASE-Frontend-Compiler erzeugt derzeit für jedes `.prg` eine vollwertige
Laufzeit einschließlich `_start` und privater Runtime-Symbole. Daher bekommen
**alle im ausgewählten Modul definierten privaten COFF-Symbole** einen stabilen,
pfadabhängigen Namespace. Seine internen Relocations werden darauf angepasst;
explizit exportierte Symbole bleiben öffentlich. Dadurch kann das Modulobjekt
zusammen mit dem eigenständigen Programme-Objekt gelinkt werden, ohne dessen
`_start` durch einen zweiten Einstieg zu ersetzen.

**Einschränkung:** Es muss genau **ein** Hauptprogramm unter
`dBASE Programme → Programme` im aktuellen, zugeordneten Projekt vorhanden
sein. Mehrere separat erzeugte vollständige Programme enthalten jeweils einen
`_start` und werden daher *nicht* stillschweigend mit einem willkürlich
ausgewählten Einstieg gelinkt. Weitere Dateien für den gemeinsamen Link sind
als Module anzulegen. Auch werden die Top-Level-Anweisungen des zusätzlichen
Modulobjekts nicht automatisch gestartet; ein Modul benötigt passende
Aufruf-/Exportschnittstellen. Die modulübergreifende dBASE-API ist keine
Bestandteil dieser Stage.

Die COFF-Architektur wird geprüft, fehlende Objekte werden nicht heimlich
übersetzt; bei einem Fehlversuch bleibt Start ausgeblendet. Vorhandene
Manifest-, PE-Compact-, Signier- und Turbo-Help-Schritte werden beim Linken
beibehalten.

## Betroffene Dateien

- `d64_dism.py`: GUI-Zustand, Signale, Assemble-Objektpfad, Link und Start.
- `dbase_module_coff.py` (neu): deterministisches COFF-Symbol-Namespace und
  Prüfung der Link-Eingaben.
- `test_stage667.py` (neu): Tests mit echten generierten dBASE-/COFF-Objekten
  für PE32 und PE32+, einschließlich der GUI-Handler.

## Tests/Plattform

Die Python-Tests benutzen die vorhandene native COFF32/COFF64-Toolchain
unter Linux und verifizieren Windows-PE-Maschinenkennungen sowie die
Editor-Button-Logik. Die große `d64_dism.py` wird für den Syntax-Test unter
Python 3.13 mit neutralisierten Python-3.15-`lazy import`-Zeilen kompiliert.
PyQt5/Windows ist in der Testumgebung nicht installiert: Ein **visueller
Windows-PyQt5-Laufzeittest ist noch erforderlich**.

An `libd64_qt5.dll` wurde nichts geändert; es ist kein DLL-Neubau nötig.
