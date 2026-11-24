# Stage 689 – Turbo-Hilfe: Lesbare Hinweis- und Fehlerdialoge

**Verbindliche Grundlage:** `d64_dism_stage688.zip`.

## Ursache

Der F2-Hinweis beim Kompilieren ohne markierten Haupt-Eintrag hat den
Dark-Mode bisher über `getattr(self.parent(), "dark_mode_enabled", False)`
ermittelt. Der unmittelbare Parent des Hilfecompilers kann aber ein
`QDockWidget` sein, das diese Eigenschaft nicht besitzt. Bei aktiviertem
Dark-Mode wurden die Farben des `QMessageBox`-Inhalts dann teils vom
Windows-/Qt-Stil geerbt und konnten zu schlecht lesbarem Text führen.
Weitere Fehlermeldungen verwendeten `QMessageBox.critical()` bzw.
`QMessageBox.warning()` ohne explizite Theme-Anpassung.

## Änderung

In `turbo_help_gui.py` wurden die Hilfsmethoden `_help_message_box()` und
`_show_help_message()` ergänzt. Die erste sucht entlang der Qt-Elternkette
nach der bereits vorhandenen `MainWindow._create_message_box()` und
benutzt diese inklusive Paletten-/Stylesheet-Behandlung für Dark und Light.
Falls der Editor allein gestartet wird, setzt sie eine explizit aus der
Anwendungspalette abgeleitete Hell-/Dunkel-Formatierung für Hintergrund,
Meldungstext und Schaltflächen.

Betroffen sind:

- F2-Hinweis beim fehlenden Haupt-Eintrag;
- Kompilierfehler (z. B. nicht vorhandene `.thlp`-Datei oder ungültige Includes);
- Warnungen beim Speichern und ungültiger `.thlp`-Dateiendung;
- Fehler beim Öffnen und Schreiben einer Hilfedatei.

Die Kompilierlogik, Dateiformate, Projektsettings und Dateipfade bleiben
unverändert.

## Tests

`pytest -q test_stage689.py test_stage688.py test_stage687.py test_stage686.py test_stage685.py test_stage684.py test_stage683.py`

37 Tests bestanden; 5 neue Stage-689-Tests überprüfen u. a. die
Elternkettensuche, die Hell-/Dunkel-Fallbackfarben und den F2-Fehlerpfad.
Der GUI-Test unter Windows mit tatsächlichem Qt5-Stil steht noch aus.
