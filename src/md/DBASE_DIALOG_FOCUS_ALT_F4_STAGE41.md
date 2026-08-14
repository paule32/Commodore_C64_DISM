# Stage 41 - Dialog-Sichtbarkeit und Alt+F4

Stage 41 baut auf Stage 40 auf.

## OWNER-Hauptfenster verstecken

Das Schliessen des OWNER-Hauptfensters beendet die Workstation weiterhin nicht.
Vor `g_window->hide()` werden jetzt jedoch alle aktuell sichtbaren Qt-Top-Level-
Fenster dieser Anwendung verborgen. Damit bleiben Login-, Warn- oder andere
Dialoge nicht frei auf dem Workstation-Desktop sichtbar.

Die dabei verborgenen Fenster bekommen die Property
`dbaseHiddenWithMainWindow=true`. Beim Klick auf das DB-Icon werden nur diese
Fenster wieder eingeblendet. Das zuvor aktive Dialogfenster wird ueber einen
`QPointer<QWidget>` schwach gemerkt und nach dem Restore wieder aktiviert.
Damit bleibt z. B. der Fokus im Login-Dialog erhalten, ohne einen ungueltigen
Zeiger zu riskieren, falls der Dialog inzwischen geloescht wurde.

## JOINED-Anwendungen

Stage 40 bleibt unveraendert: JOINED-Anwendungen wie BTX.exe werden beim
Schliessen vollstaendig beendet und bereinigen Dialoge, Dateien, DATABASE,
Sessions und Runtime-Speicher.

## Alt+F4

Alt+F4 ist keine Aktion des Workstation-Panels. Der OWNER-Keyboard-Guard
ermittelt mit `GetForegroundWindow()` das fokussierte Fenster und mit
`GetAncestor(..., GA_ROOTOWNER)` das zugehoerige Hauptfenster der Anwendung.
`WM_CLOSE` wird ausschliesslich an dieses Root-Owner-Fenster gesendet.

Dadurch gilt insbesondere:

- Fokus im Login-Passwortfeld -> Alt+F4 schliesst/versteckt die Hauptanwendung.
- Der Login-Dialog wird nicht isoliert per Alt+F4 geschlossen.
- OWNER -> Hauptfenster plus sichtbare Dialoge werden verborgen; Workstation bleibt.
- JOINED -> normaler Stage-40-Gesamt-Cleanup.
- Das Workstation-Panel selbst wird durch Alt+F4 nicht geschlossen.

## Tests

`tests/test_dbase_owner_dialog_visibility_altf4_stage41.py` prueft die neuen
Pfade. Der vollstaendige Python-Regressionslauf umfasst 451 Tests und ist gruen.
