# Stage 42 – Anwendungs-Mutexe und flackerfreies Restore

Stage 42 baut auf Stage 41 auf.

## 1. Ein Singleton pro Hauptanwendung

Neben dem globalen Workstation-Mutex besitzt jetzt jede d64qt5-Hauptanwendung
einen eigenen Windows-globalen Mutex. Der Name wird aus dem normalisierten,
kleingeschriebenen vollständigen EXE-Pfad über einen 64-Bit-FNV-1a-Hash gebildet:

    Global\dBase2Many.D64Application.<HASH>

Dadurch haben z. B. DB und BTX getrennte Mutexe. Zwei gleichnamige EXE-Dateien
aus verschiedenen Verzeichnissen gelten ebenfalls als verschiedene Anwendungen.

Der Anwendungs-Mutex wird in `D64WorkstationPrepare()` vor dem Workstation-Rollen-
Mutex angelegt und erst in `D64WorkstationFinalizeLeave()` wieder geschlossen.
Eine zweite Instanz derselben EXE startet deshalb keine zweite Runtime.

## 2. BTX-/Programmstart ohne Race

`D64WorkstationLaunchProgram()` verwendet zusätzlich pro Zielanwendung:

    Global\dBase2Many.D64Application.<HASH>.LaunchGate
    Global\dBase2Many.D64Application.<HASH>.InstanceReady

Der LaunchGate serialisiert auch sehr schnelle Mehrfachklicks. Solange die erste
neue Anwendung ihren Instance-Mutex und ihr Hauptfenster noch nicht vollständig
angelegt hat, kann kein zweiter Start durchrutschen.

Ist der Instance-Mutex bereits vorhanden, wird `CreateProcessW()` nicht erneut
aufgerufen. Stattdessen wird das bestehende Hauptfenster auf dem Workstation-
Desktop gesucht und aktiviert.

## 3. Hauptfenster-Markierung

Jedes Hauptfenster erhält bei `D64WorkstationActivate()` eine Win32-Window-
Property:

    dBase2Many.D64ApplicationWindow.<HASH>

Dadurch kann die Workstation das richtige Hauptfenster direkt finden. Login-,
Warning- und sonstige Dialoge tragen diese Property nicht und werden deshalb
nicht mit einer Hauptanwendung verwechselt.

## 4. Kein zusätzlicher Desktop-Wechsel

Der kurze sichtbare Blitz beim BTX/DB-Ablauf kam nicht von einem erneuten
`SwitchDesktop()`. Der JOINED-Zweig von `D64WorkstationActivate()` enthält auch
weiterhin ausdrücklich keinen Desktop-Wechsel.

`SwitchDesktop(g_work_desktop)` wird nur vom OWNER beim erstmaligen Aktivieren
der Workstation ausgeführt. Beim normalen JOINED-Start oder DB-Restore bleibt
der Benutzer permanent auf demselben Workstation-Desktop.

## 5. Flackerfreier JOINED-Start

Eine JOINED-Anwendung läuft bereits auf einem sichtbaren Desktop. Deshalb wird
ihr erster Qt-Frame nun zunächst mit `Qt::WA_DontShowOnScreen` vorbereitet:

1. logisch `show()`
2. 80x25-Raster und endgültige Geometrie berechnen
3. natives HWND erzeugen
4. verstecken / `WA_DontShowOnScreen` entfernen
5. genau einmal real sichtbar machen

Dadurch wird kein unfertiges Zwischenlayout mehr gezeichnet.

## 6. Flackerfreier DB-Restore

Beim Wiederherstellen des OWNER-Hauptfensters wird ebenfalls zuerst offscreen
das Raster korrigiert. Außerdem wird das Hauptfenster nicht mehr kurz aktiviert,
bevor ein zuvor fokussierter Login-Dialog wiederhergestellt wird.

War beim Verstecken z. B. der Login-Dialog aktiv, wird direkt dieser Dialog
wieder nach vorn geholt. Der sichtbare MainWindow→Login-Z-Order-Sprung entfällt.

## 7. Tests

Neuer Test:

    tests/test_dbase_application_mutex_no_flash_stage42.py

Gesamtlauf:

    462 Tests
    462 erfolgreich
    0 Fehler
