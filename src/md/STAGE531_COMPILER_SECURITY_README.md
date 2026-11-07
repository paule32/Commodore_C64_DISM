# Stage 531 – Compiler / Sicherheit / Stack / Protector Cookie

## Ausgangsbasis

Verbindliche Basis: `d64_dism_stage530.zip` (unveraenderte Dateien uebernommen).

## Projekt-Einstellungen

In jeder Windows-Architektur gibt es unter dem TreeList-Hauptknoten `Compiler` einen neuen Unterknoten `Sicherheit`:

- `Windows -> 32-Bit -> Compiler -> Sicherheit`
- `Windows -> 64-Bit -> Compiler -> Sicherheit`

Rechts wird eine eigenstaendige, scrollbar aufgebaute Einstellungsseite mit der GroupBox `Stack: ` und der Checkbox `Protector Cookie` angezeigt. Der Anfangswert ist fuer beide Architekturen `False` (deaktiviert).

Die Checkbox besitzt pro Architektur einen eigenen Zustand; geaenderte Werte markieren das Projekt als veraendert. Werte werden auch beim Schliessen bzw. beim Neuanlegen des Projektes wieder auf `False` gesetzt.

## `.pro`-Persistenz

Unabhaengige Abschnitte:

```ini
[Settings.Windows.32Bit.Compiler.Security]
Title = Windows 32Bit Compiler Sicherheit
ProtectorCookie = false

[Settings.Windows.64Bit.Compiler.Security]
Title = Windows 64Bit Compiler Sicherheit
ProtectorCookie = false
```

Fehlende Abschnitte in aelteren Projektdateien fuehren jeweils zum Default `false`.

## Abgrenzung

Dies ist eine GUI-/Projektdatei-Erweiterung. Das Anwaehlen der Checkbox erzeugt in Stage 531 **noch keinen** Stack-Canary-Code und veraendert weder den Loader noch die Compiler-Runtime. Die spaetere Implementierung benoetigt die Instrumentierung der generierten Funktionsprologe/-epiloge plus Schutzwertinitialisierung und eine Fehlerbehandlung pro Zielarchitektur. Die Checkbox benennt daher eine reservierte Konfigurationsoption.

## Testumfang

- `test_stage531.py`: 6 gezielte Testfaelle (AST-/GUI-Struktur, Navigation, getrennte Steuerung, INI-Roundtrip, Legacy-Defaults, Projektlebenszyklus) bestanden.
- Stage 530: 8 alte Tests bestanden.
- Stage 529: 2 alte Tests bestanden.
- Stage 528: 2 alte Tests bestanden (separater Lauf).
- Der Stage-527-Gesamttest wurde wegen langer Laufzeit nicht abgeschlossen.

PyQt5 ist in der aktuellen Testumgebung nicht installiert. Eine visuelle Ausfuehrung der GUI unter Windows wurde nicht bestaetigt.
