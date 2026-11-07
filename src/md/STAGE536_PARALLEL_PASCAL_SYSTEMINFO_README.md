# Stage 536 – Paralleler Pascal-Projektbuild und System-Informationen

Ausgangspunkt: unveränderte Stage-535-Projektstruktur. Der Pascal-Compiler,
PE32-/PE32+-Assembler und Linker bleiben die vorhandenen Implementierungen.

## Compiler → Parallelisierung

Unter **Projekt → Einstellungen → Windows → 32-Bit / 64-Bit → Compiler →
Parallelisierung** wird pro Zielarchitektur ein eigenes Einstellungsblatt
angeboten:

- `Automatische CPU-Erkennung`: standardmäßig **an**.
- `Maximale Compiler-Prozesse`: QComboBox mit **1 Prozess**, **2 Prozesse**,
  **3 Prozesse**, **4 Prozesse**; standardmäßig **2 Prozesse**.
- Bei automatischer Erkennung wird die Zahl verfügbarer logischer Prozessoren
  festgestellt und auf die ausgewählte Prozessobergrenze begrenzt. Bei
  deaktivierter Erkennung gilt die gewählte Obergrenze unmittelbar.
- Ändern einer Architektur beeinflusst nicht die andere.

INI-Persistenz in `pascal.pro`:

```ini
[Settings.Windows.32Bit.Compiler.Parallelisierung]
AutomaticCpuDetection = true
MaxCompilerProcesses = 2

[Settings.Windows.64Bit.Compiler.Parallelisierung]
AutomaticCpuDetection = true
MaxCompilerProcesses = 2
```

Alte Projekte erhalten beim Laden dieselben Standardwerte.

## Tatsächliche CPU-parallele Kompilierung

- Der vorhandene Projekt-Builder sammelt `.pas/.pp`-Units aus **Units** und
  zusätzliche Unit-Quellen aus **Module** (nicht das Hauptprogramm).
- Aus den nach Direktivenverarbeitung sichtbaren `USES`-Deklarationen wird ein
  gerichteter Abhängigkeitsgraph gebildet; nicht im Projekt gelistete System-
  und Bibliotheks-Units werden weiterhin vom vorhandenen Pascal-Resolver
  aufgelöst.
- Ein Scheduler läuft in einem `QThread`. Für jede unabhängige Unit wird ein
  **eigener Python-Unterprozess** gestartet, sodass ANTLR und der eigentliche
  Compiler auf mehreren CPU-Kernen laufen können (kein GIL-Flaschenhals).
- Unterprozesse erzeugen `.generated.pe32/64.asm`, `.pui` und `.coff32/64.o`.
  Der integrierte Assembler wird dabei aus `d64_dism.py` importiert; die GUI
  wird nicht gestartet. Der COFF-Build läuft ebenfalls im Compilerprozess.
- Die abschließende Projektverlinkung verwendet die bereits erzeugten
  Objektdateien in der ursprünglichen Projekt-Reihenfolge. Sie beginnt
  **erst nach erfolgreichem Abschluss aller Units**.
- Die `.pui`-Dateien werden per prozessindividuellem temporärem Dateinamen
  geschrieben und anschließend atomar ersetzt. Ein Leser sieht dadurch
  keine halbfertigen PUI-Dateien.
- Beim Fehler eines Unterprozesses wird keine abhängige Unit und **kein
  Hauptprogramm** gestartet beziehungsweise gelinkt. Der Fehler erscheint
  im Protokoll und als GUI-Meldung.
- Änderungen des Quelltextes, die noch nicht gespeichert sind, führen zum
  bisherigen sequenziellen Build. Bereits geöffnete Unit-Editoren erhalten
  nach einem erfolgreichen Parallel-Build die erzeugte ASM-Ausgabe.
- Die Ausgabe von `PASCAL PARALLEL START/OK/ERROR` im Protokoll kennzeichnet
  die Parallelisierungsphase.

Der bewährte sequentielle Pfad bleibt erhalten bei einer effektiv gewählten
Prozesszahl von 1, weniger als zwei Pascal-Units, nicht analysierbaren
Projektabhängigkeiten, unterschiedlichen Compiler-Makroprofilen, aktiviertem
Ordinal-Import-Umschreiber, AT&T-Ausgabesyntax und einer als PyInstaller
gepackten IDE ohne separat verfügbaren Python-Worker. Ein zyklisches USES
führt zur bisherigen Compilerdiagnose.

**Wichtig:** Die zusätzlichen Compiler-Worker importieren den vorhandenen
Projekt-Assembler. Sie brauchen damit dieselbe Python-Version und dieselben
Installationsvoraussetzungen wie die laufende IDE, insbesondere passende
ANTLR4- und Qt5-Module. Die vorgefundenen Python-3.15-`lazy from`-Importe
in `d64_dism.py` wurden nicht verändert.

## Hilfe → System-Informationen

Der neue modale `SystemInformationDialog` übernimmt das aktive Dark-/Light-
Theme. Der Dialog zeigt (mit der Schaltfläche **Aktualisieren**):

- Windows 10/11 auf Grundlage der Buildnummer; Edition Home/Professional,
  DisplayVersion und Build.
- CPU-Hersteller Intel/AMD, Prozessorbezeichnung, OS-Architektur 32/64-Bit,
  physische Kerne und logische Prozessoren.
- Physisch installierter RAM, vom Betriebssystem nutzbarer RAM, aktuell
  verfügbarer RAM; virtuelles Speicher-Commit-Limit und verfügbares Commit.

Die Windows-Daten werden nativ über Registry, `GetLogicalProcessorInformationEx`,
`GetPhysicallyInstalledSystemMemory` und `GlobalMemoryStatusEx` abgefragt;
`wmic.exe`, PowerShell und externe DLLs sind nicht erforderlich. Ein
Windows-API-Feld, das auf dem System nicht verfügbar ist, wird ausdrücklich
als **Nicht verfügbar** dargestellt.

**Hinweis zur Terminologie:** Die von Windows über `GlobalMemoryStatusEx`
ausgewiesenen `ullTotalPageFile`/`ullAvailPageFile` sind das gesamte
Commit-Limit bzw. verfügbare Commit und nicht ausschließlich die Größe der
Auslagerungsdatei. Der Prozess-Adressraum ist wiederum ein anderer Wert.

## Verifikation und Grenzen

- `python -m unittest test_stage536 -v`: Scheduler, Fehlerpfade, Abhängigkeits-
  graph, Unit-Worker (mit gemockten Compiler-/Assemblerfunktionen), `.pro`-
  Roundtrip und Informationsfelder.
- Vorhandene Tests aus Stage 531–535 bleiben unverändert.
- In der Prüfumgebung liegen keine Windows-PyQt5-Oberfläche und kein
  ANTLR4-4.13.2-Frontend vor. Deshalb sind **native Windows-GUI-Tests, ein
  echter vollständiger Pascal-Projektbuild mit zwei Compilerprozessen und
  Laufzeitmessungen noch offen**. Die Tests der Worker-Abläufe verwenden
  Test-Doubles und beweisen nicht den nativen End-to-End-Lauf.

## Windows-Smoke-Test

1. Im Projekt `pascal.pro` mindestens zwei unabhängige, gespeicherte Units
   auswählen, automatische Erkennung eingeschaltet lassen und `2 Prozesse`
   wählen.
2. `Windows → 32-Bit → Compiler → Parallelisierung` konfigurieren.
3. Projekt → Windows PE32 → Programm kompilieren/linken.
4. Im Protokoll müssen zwei `PASCAL PARALLEL START` erscheinen, bevor die
   zugehörigen `OK`-Meldungen folgen (sofern beide Units unabhängig sind).
5. Erzeugtes Hauptprogramm mehrfach aus der IDE und von Hand starten.
6. 64-Bit-Einstellungen unabhängig ändern und analog testen.
7. `Hilfe → System-Informationen` im Dark- und Light-Mode prüfen.
