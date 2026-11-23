# Stage 650 – „Hilfe → Über ...“ in Turbo Vision - dBASE

**Basis:** `d64_dism_stage649.zip` (alle bisherigen Projektdateien erhalten).

## Änderung

Menü `Hilfe -> Über ...` im eingebetteten Turbo-Vision-Fenster (`d64qt5/d64qt5_bridge.cpp`):

```text
Turbo Vision  -  dBASE
Copyright (c) 2026 Jens Kallup - paule32
Alle Rechte vorbehalten.

Built with: Python and Qt5 Framework,
```

Die `\n`-Sequenzen sind echte Zeilenumbrüche, einschließlich einer Leerzeile vor „Built with“. Die gewünschte abschließende Kommasetzung wurde beibehalten.

Die Ausrichtung des Nachrichtentexts ist ausschließlich bei diesem Aufruf `Qt::AlignCenter`. Die wiederverwendbare `D64TurboMessageBox` (`d64qt5/d64_turbo_messagebox.hpp`) besitzt dazu einen **optionalen** Ausrichtungsparameter mit dem bisherigen Standard `Qt::AlignLeft | Qt::AlignVCenter`. Bestehende Fehler-, Hinweis- und Speicherdialoge bleiben linksbündig. Titelzeile, Rahmen, Buttons, Escape, Dragging und eingebettete Modalität wurden nicht verändert.

## Windows-Build

1. Programme schließen, die `libd64_qt5.dll` geladen haben.
2. `build_and_deploy_dbase_editor_stage650.bat` starten. Ziel standardmäßig `runtime\dbase\pe32`, optional Zielverzeichnis als erstes Argument.
3. Turbo-Vision-Fenster erneut öffnen und `Hilfe -> Über ...` aufrufen.

Für diesen reinen GUI-Patch muss keine dBASE-Quelle erneut kompiliert oder gelinkt werden.

## Tests

`pytest -q test_stage650.py test_stage631.py test_stage634.py test_stage635.py test_stage636.py test_stage637.py`

**Ergebnis:** 46 bestanden. Ein nativer Qt5-/MinGW32-Build und visueller Windows-Test waren in dieser Umgebung nicht möglich (Qt5-Entwicklerpakete nicht installiert).
