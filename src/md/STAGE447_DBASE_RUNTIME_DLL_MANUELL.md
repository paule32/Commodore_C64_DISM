# Stage 447 – dBASE Runtime DLL manuell erstellen

## Grundlage
- Verbindliche Grundlage: `d64_dism_asm_446.zip`.
- Keine externen Compiler oder `make`-Aufrufe; native **interne** COFF-Assembler und PE-Linker.

## Hauptmenü
- `Werkzeuge -> dBASE Runtime PE32 DLL erstellen`
- `Werkzeuge -> dBASE Runtime PE32+ DLL erstellen`

Beide Befehle erzeugen eine neue `d64_dbase_console.dll` in dem **jeweiligen projektspezifischen Zielverzeichnis**. Ist dort kein Pfad konfiguriert, wird das aktuelle Arbeitsverzeichnis benutzt. Erfolg und Ausgabepfad erscheinen im Protokoll und in der Statusleiste; Fehler werden als GUI-Warnung und im Protokoll angezeigt.

## Projekt-Einstellungen
- `Projekt-Einstellungen -> Windows -> 32-Bit -> Umgebung`
- `Projekt-Einstellungen -> Windows -> 64-Bit -> Umgebung`

In der Seite `Umgebung` (Übersicht unter **Eingabe** sowie `Umgebung -> Eingabe`) befindet sich die Gruppe `dBASE Runtime` mit drei Steuerelementen in **einer Reihe**:

1. `dBASE Runtime DLL erstellen` (ruft den passenden Build auf),
2. Verzeichniseingabefeld,
3. `...` für die Verzeichnisauswahl.

Jeder Architektur-Tab besitzt ein **eigenes** Verzeichnisfeld. Die Pfade werden in der `.pro`-Projektdatei im jeweiligen `Settings.Windows.32Bit.Environment` beziehungsweise `Settings.Windows.64Bit.Environment` unter `DBaseRuntimeDLLDirectory` gespeichert. Relative Pfade werden projektbezogen gespeichert und beim Laden aufgelöst. Projekte ohne diesen Eintrag bleiben kompatibel.

## Ablauf

1. Gewünschte Architektur wählen (PE32 oder PE32+).
2. Ausgabeverzeichnis eintragen oder über `...` auswählen.
3. Auf `dBASE Runtime DLL erstellen` klicken oder den passenden Menüeintrag verwenden.
4. Der interne Assembler erzeugt COFF und der interne Linker erzeugt die Windows DLL.
5. Vor der Übernahme werden die PE-Maschinenkennung (i386 oder AMD64) und die Exporte `DBaseConsoleEnsure`, `DBaseConsoleWrite`, `DBaseConsoleShutdown`, `DBaseConsoleSetTitle` geprüft.
6. Die Datei ersetzt die Zieldatei **erst nach erfolgreicher Validierung**. Ein fehlgeschlagener Build lässt eine bestehende DLL bestehen.

Das **manuelle** Erstellen unterscheidet sich vom bereits vorhandenen **automatischen Deployment** aus Stage 446, das die passende DLL für benötigende Programm-Builds weiterhin neben die erzeugte EXE bereitstellt.

## Geänderte Dateien
- `d64_dism.py`: Hauptmenü, Settings-Controls, Pfad-Speicherung, gemeinsamer Build-Handler.
- `d64dbase/runtime_builder.py`: Neuer manueller, validierter, atomarer DLL-Build.
- `test_stage447_manual_dbase_runtime.py`: 7 Tests, darunter echte PE32/PE32+-DLL-Erzeugung.
- `STAGE447_DBASE_RUNTIME_DLL_MANUELL.md` (dieses Dokument).

## Einschränkung
Der Code wurde mit automatisierten Tests geprüft, aber die tatsächliche visuelle Bedienung in Windows/PyQt5 konnte in dieser Linux-Testumgebung nicht durchgeführt werden.
