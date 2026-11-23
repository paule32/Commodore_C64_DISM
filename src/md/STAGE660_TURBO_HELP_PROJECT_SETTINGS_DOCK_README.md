# Stage 660 – Projekt-Einstellungen neben dem Hilfecompiler

Verbindliche Basis: `d64_dism_stage659.zip`.

## Bedienung

- Bereits sichtbare Projekt-Einstellungen werden beim Öffnen des Hilfecompilers nicht mehr verborgen. Waren sie geschlossen, werden sie nicht ungefragt eingeblendet.
- Projekt-Einstellungen lassen sich auch nach dem Öffnen des Hilfecompilers über das bestehende Hauptmenü öffnen.
- Die benutzerdefinierte Titelleiste unterstützt jetzt das Drag-and-Drop-Andocken der Projekt-Einstellungen links und rechts. Dazu das Fenster an der Titelleiste ziehen und über dem angezeigten Andockziel loslassen. Bei aktivem Hilfecompiler belegt dieser die gegenüberliegende Seite. Die beiden Dockbreiten können per Splitter angepasst werden.
- Der bisherige Settings-Vollflächenmodus wird beim Übergang zum Hilfecompiler geordnet beendet, bevor ein neuer Workspace-Snapshot entsteht. Beide Docks lassen sich unabhängig schließen. Die explizite Seitenwahl der Einstellungen bleibt beim Schließen des Hilfecompilers erhalten.
- Die exklusiven Workspaces anderer Werkzeuge sowie die bisherige Projekt-/Dateisystem-Snap-Logik bleiben erhalten.

## Implementierung

Nur `d64_dism.py` wurde im Anwendungsquelltext verändert: `DockTitleBar`, `DockSnapOverlay`, die exklusiven Werkzeug-Workspaces und die Projekt-Einstellungen. Die Qt5-Bridge und erzeugte Programme sind nicht betroffen. Der Neubau einer DLL ist nicht erforderlich.

## Prüfung

`pytest -q test_stage660.py test_stage654.py test_stage658.py test_stage655.py test_stage659.py test_stage604.py`

Ergebnis: 35 bestanden (10 neue, 25 bestehende Tests). Die neuen Tests führen die produktiven Workspace-/Snap-Methoden mit Qt-ähnlichen Testobjekten aus; sie prüfen beide Seiten, das Schließen, das Wiederherstellen und den Wechsel anderer Werkzeuge. Zusätzlich wurde die Python-Syntax mit für Python 3.13 normalisierten Lazy-Imports geprüft. Kein nativer Windows-/PyQt5-Drag-and-Drop-Test, da PyQt5 in der Testumgebung nicht installiert ist.
