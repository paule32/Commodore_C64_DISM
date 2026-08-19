# Stage 128 – Workstation global shutdown, application hide, maximize bounds

## Workstation EXIT

Nach der vorhandenen JA/NEIN-Bestaetigung beendet der OWNER:

1. Keyboard-Guard,
2. alle Console-/GUI-Child-Prozesse per registriertem Global-Shutdown-Signal,
3. wartet bis zu ca. 3 Sekunden auf deren normalen Runtime-Cleanup,
4. beendet verbliebene Child-Prozesse mit `TerminateProcess` (alle Threads),
5. baut die Owner-Runtime, Datenbanken, Sessions und Qt-Fenster ab,
6. zerlegt erst in `D64WorkstationFinalizeLeave()` Bottom-/Left-Panel,
   Desktop-Handles und Workstation-Mutex.

Damit bleibt die Workstation bis zuletzt bestehen und laufende Child-Prozesse
halten nach EXIT keine neu zu erzeugenden EXE/OBJ-Dateien mehr offen.

## X eines Anwendungsfensters

Console- und WFM-Hauptfenster werden nur verborgen.

Vor dem Hide werden:
- Qt-Fokus geloest,
- `grabKeyboard()` geloest,
- `grabMouse()` geloest,
- Win32 Focus/Capture fuer das Fenster geloest.

`QApplication::setQuitOnLastWindowClosed(false)` verhindert, dass eine nur
verborgene Anwendung ungewollt beendet wird.

Ein globales Workstation-EXIT verwendet nicht WM_CLOSE, sondern die registrierte
Nachricht `dBase2Many.D64Workstation.GlobalShutdown`, sodass der normale
Hide-Pfad nicht mit dem echten Shutdown kollidiert.

## Maximieren

`WM_GETMINMAXINFO` wird fuer Console- und WFM-Hauptfenster abgefangen.
Der maximale Bereich ist:

- links: `WORKSTATION_PANEL_WIDTH + 4`
- oben: `4`
- rechts: Bildschirmbreite - 4
- unten: Bildschirmhoehe - BottomPanel - 4

Damit ueberdeckt ein maximiertes Child-Fenster weder das linke noch das untere
Workstation-Panel.
