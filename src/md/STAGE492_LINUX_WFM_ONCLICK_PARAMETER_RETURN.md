# Stage 492 – Linux-WFM: Parameter und RETURN in onClick-Prozeduren

Basis: Stage 491 (`d64_dism_asm_491.zip`).

## Anlass

Stage 491 verweigerte beim Linux-Build von `Form1.wfm` eine Ereignisprozedur wie
`PushButton1_onClick(Sender)` oder eine `FUNCTION ... RETURN ...` mit
`Linux-Qt5-Ereignisprozedur ...: Parameter oder Rueckgabewerte noch nicht implementiert`.
Die Einschränkung wurde durch eine echte Ereignisparameter-Weitergabe ersetzt.

## Implementierung

- `d64dbase/linux_frontend.py`: WFM-Prozeduren/Funktionen für `OnClick` akzeptieren
  jetzt null, einen oder zwei gewöhnliche Parameter. Sie werden zur **Laufzeit**
  gebunden, nicht fälschlich als Konstanten ausgewertet.
- Beim Signal `QAbstractButton::clicked(bool)` bekommt der erste Parameter den
  `Sender` (als native X11-Fenster-ID unter Qt/XCB, sonst 0), ein zweiter
  Parameter den `Checked`-Status. Ein einzelner Parameter mit dem Namen
  `Checked` erhält direkt den booleschen Status.
- Namen von Parametern dürfen beliebig gewählt werden; das Mapping erfolgt
  positionsabhängig. Variadische oder mehr als zwei Parameter verursachen
  einen präzisen Quellfehler, da `clicked(bool)` solche Argumente nicht liefert.
- Bekannte Ausdrucksformen mit Ereignisvariablen (`? Sender`, `LOCAL X = Checked`,
  `RETURN Sender`, `MessageBoxA(Sender, ...)`), einfache Text-Zuweisungen und
  direkte `RETURN MessageBoxA(...)`-Rückgaben werden verarbeitet.
- `PROCEDURE` darf nur `RETURN` ohne Ausdruck enthalten; `FUNCTION` muss einen
  Rückgabewert zurückgeben. Eine Qt-`clicked`-Signalverbindung verwendet diesen
  Wert nicht; der Compiler erzeugt daher eine Warnung.
- Parameterlose `PROCEDURE`-Handler behalten das bisherige kompakte JSON-Format.
  Methoden mit Argumenten bzw. `FUNCTION` verwenden Objektmetadaten
  `{parameters, kind, actions}`.
- `d64qt5/d64qt5_linux_form.cpp`: Qt5 liest diese Metadaten, befüllt die
  Ereignisvariablen beim Klick und verarbeitet die neuen Befehle `set_var`,
  `print_value`, `settext_value`, `return` und `ffi_return`. X11-Handles von
  Kindwidgets werden dem zugehörigen übergeordneten Qt-Fenster zugeordnet.
- PE32-/PE64-Windows-WFM-Codeerzeugung wird nicht geändert.

## Beispiel

```dbase
CLASS Form1 OF FORM
THIS.PushButton1 = NEW BUTTON()
THIS.PushButton1.OnClick = CLASS::PushButton1_onClick

PROCEDURE PushButton1_onClick(Sender, Checked)
    ? "Hallo aus dem Qt5-Terminal"
    ? Sender
    LOCAL Zustand = Checked
    ? Zustand
    RETURN
ENDCLASS
```

Für die `FUNCTION`-Form kann `RETURN MessageBoxA(Sender, "Text", "Titel", 0)`
verwendet werden. Der Rückgabewert ist innerhalb der Ausführung vorhanden,
wird vom Signal `clicked(bool)` selbst jedoch nicht konsumiert.

## Tests und Grenzen

- 90 gezielte Regressionstests (Stages 486–492) erfolgreich auf Linux.
- ELF32-/ELF64-Erzeugung und dynamische Qt5-ABI-Imports sind geprüft.
- Keine echte Qt5-Oberflächen-/Klickprüfung auf diesem Testsystem, weil
  `Qt5Widgets`-Entwicklungsdateien nicht installiert sind.
- Unter Ubuntu nach dem Update `d64qt5/build_linux.sh` erneut ausführen,
  damit die geänderte `libd64_qt5.so` neu gebaut wird.
- Das Linux-WFM-Backend bleibt hinsichtlich dynamischer dBASE-Ereignislogik
  auf den dokumentierten Teilumfang begrenzt. Nicht implementierte Anweisungen
  erzeugen weiterhin einen Quellfehler statt einer scheinbaren Erfolgsmeldung.
