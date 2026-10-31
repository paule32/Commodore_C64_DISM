[Deutsch](STAGE495_WFM_NATIVE_QT_FOCUS_EVENTS.md) | [English](STAGE495_WFM_NATIVE_QT_FOCUS_EVENTS.en.md)

# Stage 495 – Native Qt5-Ereignisse OnGotFocus / OnLostFocus

Verbindliche Basis: d64_dism_asm_494.zip.

## Ursache

Stage 494 konnte die Prozeduren im Eigenschaften-Panel erzeugen und auffinden, jedoch
war die native Ausführung auf beiden Plattformen unvollständig:
- In `d64qt5/d64qt5_bridge.cpp` erkannte der Windows-Eventfilter beim Fokuserhalt
  ausschließlich den älteren Namen `OnGetFocus`, nicht `OnGotFocus`.
- In `d64qt5/d64qt5_linux_form.cpp` war nur das Qt-Signal `clicked(bool)` verdrahtet.
  `d64dbase/linux_frontend.py` verweigerte andere Ereignisse bereits im Compiler.

## Implementierung

### Windows PE32 / PE32+

`DBaseQtObjectBindEvent` akzeptiert `OnGotFocus` und die ältere Schreibweise
`OnGetFocus` gleichwertig. Ein `QEvent::FocusIn` ruft den WFM-Callback mit einem
`QObject*` auf; `OnLostFocus` verwendet `QEvent::FocusOut`. `OnClick` wird
unverändert über `QAbstractButton::clicked` verbunden.

Wird einem standardmäßig nicht fokussierbaren Widget explizit ein Fokus-Ereignis
zugewiesen, erhält es `Qt::StrongFocus`. Die Events werden nicht konsumiert;
die normale Qt-Fokusnavigation bleibt erhalten.

### Linux ELF32 / ELF64

Der Compiler akzeptiert `OnGotFocus`, `OnLostFocus`, `OnGetFocus` (Altbestand)
und `OnClick`, jeweils auch für die FORM-Instanz (`THIS`). Das Formular-JSON
enthält jetzt auch `events` auf Formularebene.

Der native `DBaseQtRunFormJson`-Einstieg in `libd64_qt5.so` installiert je
Fokusbindung einen eigenen QObject-Eventfilter für `QEvent::FocusIn` oder
`QEvent::FocusOut`. Qt-Signale und Ereignisse werden nicht verschluckt.
Jeder Filter ruft seine gebundene WFM-Methode über den bestehenden
`runDBaseActions`-Interpreter auf. Es findet keine Erzeugung zusätzlicher
Prozeduren durch die Laufzeit statt.

### Ereignisparameter / Sender

- `PROCEDURE PushButton1_onGotFocus(Sender)` und
  `PROCEDURE PushButton1_onLostFocus(Sender)` akzeptieren maximal einen Parameter.
- Windows: `Sender` entspricht dem `QObject*` der Ereignisquelle im nativen
  WFM-Callback.
- Linux/X11 (`xcb`): `Sender` ist die native `WId`/XID des Widgets.
- Linux/Wayland: Es wird kein X11-Handle erfunden; `Sender` ist 0.
- `OnClick` akzeptiert weiterhin `(Sender, Checked)` und verwendet
  `QAbstractButton::clicked(bool)` wie zuvor.
- Rückgabewerte von Qt-Fokusereignissen beeinflussen die Qt-Fokusentscheidung
  nicht; das bisherige Verhalten für FUNCTIONs bleibt bestehen.

## Beispiel

Siehe `examples/wfm_focus_stage495/Form1.wfm`.

## Bauen

Windows: Die bestehende Qt5-Bridge (`d64qt5/d64qt5_bridge.cpp`) muss zur
aktualisierten `libd64_qt5.dll` neu gebaut werden (über die Projekt-Buildskripte).
Linux: Im Verzeichnis `d64qt5` `./build_linux.sh` ausführen. Das Programm
benötigt die aktualisierte `libd64_qt5.so` neben der ELF-Datei.

## Testnachweise und Grenzen

- 39 gezielte Stage-492/494/495-Tests bestanden.
- 63 direkt betroffene Stage-490/491/492/495-Tests bestanden.
- ELF32/64-WFM-Aufruf und JSON-Metadaten wurden geprüft.
- Native Qt5-GUI konnte in der Testumgebung nicht gebaut bzw. interaktiv
  fokussiert werden, weil Qt5-Entwicklungsbibliotheken fehlen.
- Breite historische GUI-Testläufe waren nicht vollständig abschließbar
  (Zeitlimit); daraus folgt keine Freigabe der Gesamtsuite.
