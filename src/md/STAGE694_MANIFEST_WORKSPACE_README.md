# Stage 694 (Basis Stage 693)

- Manifest-Gruppe oberhalb der Identity-Attribute, Einbettung optional.
- Ohne externe Datei wird das Manifest aus den Einstellungen erzeugt; Name erforderlich.
- Externe Datei bleibt maßgeblich; bei aktivierter Admin-Option muss sie requireAdministrator enthalten.
- UAC: requireAdministrator bzw. asInvoker; kein Passwort und keine Umgehung der Windows-Abfrage.
- Beschreibung und optionale Per-Monitor-DPI-Awareness; nur für entsprechend implementierte Anwendungen aktivieren.
- Separate PE32/PE64-Daten über vorhandene Projekt-INI-Serialisierung; Änderungen markieren Projekt als geändert. Speichern/Speichern unter sowie bestehendes Speichern beim Schließen des Einstellungsdocks.
- Minimieren darf die Projekt-Einstellungen nicht als geschlossen behandeln. Beim Wiederherstellen hat dieser Workspace Vorrang.
- Bestehende RT_MANIFEST-Einbettung über UpdateResourceW vor Kompaktierung/Signatur bleibt erhalten.

Tests: python -m pytest -q test_stage694.py test_stage693.py (21 bestanden in Linux/Python 3.13). Hauptdatei syntaktisch geprüft mit temporär entfernten lazy-Import-Markern (Original bleibt Python 3.15). Native Qt/Windows-Tests nicht ausgeführt.
