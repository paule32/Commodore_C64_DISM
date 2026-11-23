# Stage 643 – Interner Turbo-Vision-Dateidialog und mehrbenutzerfähiges VFS

**Verbindliche Basis:** `d64_dism_stage642.zip`.

## Neues Verhalten unter „Datei → Öffnen...“

Die Menüaktion erstellt **keinen Editor mehr vor der Dateiauswahl**. Nach dem Verlassen des Qt-Popup-Menüs wird ein internes, modales `QWidget` innerhalb von `QPlainTextEdit::viewport()` eingeblendet. Die vorhandene `D64TurboModalLayer` übernimmt die Eingabesperre für andere Fenster. `Escape` und „Abbrechen“ verlassen den Dialog ohne neue Editorinstanz.

Nur wenn eine Datei erfolgreich ausgewählt wurde, wird für unterstützte Quell- und Textdateien (`.prg`, `.wfm`, `.txt`, `.ini`, `.json`, `.sql`, `.pas`, `.md`, `.h`, `.cpp`, `.c`) ein eigener blauer Turbo-Vision-Editor erstellt. `.prg` und `.wfm` werden als Text geöffnet, mit UTF-8 und CP1252/Systemcodepage-Fallback. Andere Dateitypen erhalten eine **interne** Informationsmeldung, statt einen leeren Editor zu öffnen.

## Dialogfelder

* Oben: `Suchen` mit Filter für Dateinamen des aktuellen Ordners.
* Links: anklickbare Verzeichnisse **und Dateien** mit eigenen Icons; `..` navigiert zurück.
* Rechts: Verzeichnisse und Benutzerdateien in den Spalten `Name`, `Datum`, `Größe`; Einfachklick markiert, Doppelklick auf Verzeichnis navigiert bzw. auf Datei öffnet.
* Zwischen beiden Bereichen: verschiebbarer `QSplitter`.
* Unter den Bereichen: `Dateiname` und Eingabefeld.
* Unterste Zeile links: `Verz. Hinzufügen`, `Löschen`; rechts: `OK`, `Abbrechen`, `Hilfe`.
* `Verz. Hinzufügen`: **eingebetteter**, eigener modaler Unterdialog mit Eingabefeld, `OK`, `Abbrechen`, `Hilfe`.
* Löschen: eingebettete Sicherheitsabfrage, nur **Dateien oder leere Verzeichnisse** löschbar; Mountpoints dürfen nicht gelöscht werden.
* Bei `Speichern unter...` folgt vor dem Überschreiben eine eingebettete Bestätigung.

## Virtuelle Verzeichnisstruktur

Der Benutzer sieht nur:

```
/
├── Alle Benutzer/
└── Dokumente/
```

Unter jedem Mountpoint kann er Unterordner erstellen. `..` am Mountpoint führt lediglich zur **virtuellen Wurzel** zurück. Es gibt keine Möglichkeit, in die Host-Verzeichnisse `_Benutzer` oder andere private Benutzerverzeichnisse zu navigieren.

Nach der DLL-Initialisierung wird das EXE-gebundene Verzeichnis wie bisher anhand von `QCoreApplication::applicationFilePath()` erzeugt. Es enthält Host-Mounts, deren echte Namen in der UI nicht erscheinen:

```
<AppLocalDataLocation>/dBase2Many/Anwendungen/<EXE-Name>-<Hash>/
├── _Alle_Benutzer/
└── _Benutzer/<SHA256-der-Benutzeridentität>/Dokumente/
```

Bei einer **erfolgreichen** dBASE-`SESSION`-Anmeldung wird die authentifizierte Login-Identität als VFS-Benutzer verwendet; alte Editoren müssen vor dem Wechsel geschlossen werden, und eine abgebrochene Speicherabfrage verhindert den Wechsel. Ohne dBASE-SESSION bleibt die Host-Benutzeridentität der Fallback. Vorhandene Dateien aus dem Stage-626-Pfad `Dokumente/` werden einmalig zum privaten Host-Fallback migriert, nicht zum neuen Session-Benutzer.

Jede VFS-Lese-, Schreib-, Lösch- oder Auflistungsoperation löst den virtuellen Pfad neu auf. Absolute Pfade, `..`-Komponenten, unzulässige Windows-Dateinamen sowie Symlink-Ausbrüche werden abgewiesen. `QSaveFile` sorgt weiterhin für atomisches Speichern.

### Wichtige Sicherheitsgrenzen

Die Isolation gilt **für die in dieser Qt5-Bridge implementierten Datei- und Editoroperationen**. Sie ersetzt keine Betriebssystem-Zugriffssteuerung und beschränkt **nicht automatisch** selbst programmierte dBASE-Datei-I/O- oder FFI-Funktionen. `AppLocalDataLocation` gehört zum aktuellen Windows-Host-Benutzer: „Alle Benutzer“ wird zwischen den dBASE-Anwendungs-Logins **innerhalb desselben Windows-Profils** geteilt. Für eine wirklich betriebssystemübergreifende, für verschiedene Windows-Accounts gemeinsame Ablage wären ein separat konfigurierter Host-Speicherort und passende NTFS-ACLs erforderlich.

## Geänderte Dateien

* `d64qt5/d64_turbo_editor.hpp` – VFS, interne Dialogoberfläche, eingebetteter Verzeichnisdialog, gemeinsame Öffnen-/Speichern-Auswahl und Textdateiladen.
* `d64qt5/d64qt5_bridge.cpp` – Menüaktion, verzögerte Popup-Freigabe, Öffnen erst nach Auswahl und Benutzerwechsel bei authentifizierten Sessions.
* `test_stage628.py` – bisherige, nun obsolete Menüerwartung aktualisiert.
* `test_stage643.py` – neue gezielte VFS-/GUI-Integrationsprüfungen.
* `build_and_deploy_dbase_editor_stage643.bat` – aktualisierte Qt5-/MinGW32-DLL erstellen und deployen.

## Installation und Prüfung

1. Alle Anwendungen beenden, die `libd64_qt5.dll` geladen haben.
2. Unter Windows `build_and_deploy_dbase_editor_stage643.bat` im Projektordner aufrufen.
3. dBASE-EXE erneut starten; `Datei → Öffnen...` wählen. Ohne Auswahl darf **kein Editor** entstehen.
4. `Dokumente` öffnen, über `Verz. Hinzufügen` ein Unterverzeichnis erstellen, per `..` zurücknavigieren.
5. Mit `.prg` und `.wfm` aus den gemappten Verzeichnissen die Texteditoren aufrufen.
6. Verschiedene SESSION-Login-Identitäten prüfen: `Dokumente` muss für jeden Benutzer eine andere Dateiablage zeigen, `Alle Benutzer` dieselbe innerhalb des Windows-Profils.

**Tests:** Die Python-Regressionen prüfen die C++-Integrationsstruktur. Eine vollständige native Qt5-/MinGW32-Kompilierung, ein GUI-Test und ein Mehrbenutzer-Akzeptanztest unter Windows können hier mangels Toolchain nicht durchgeführt werden.
