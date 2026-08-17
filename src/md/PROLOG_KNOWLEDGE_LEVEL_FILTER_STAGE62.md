# PROLOG Wissen-Datenbank Browser – Stage 62

## Änderungen

### Alternativen direkt unter dem Parent-Level
Der gemeinsame Alternativen-Editor wird nicht mehr im oberen Abfragebereich angezeigt. Ein Klick auf den `▼`-Pfeil eines Level-Buttons verschiebt Label und ComboBox in einen eigenen Host direkt unter diesen Button. Beim Öffnen eines anderen Parents wandern die Controls zu diesem Parent.

### Nur eine Alternative je Parent/Level
Die ComboBox listet weiterhin alle PROLOG-seitig gültigen Alternativen für den jeweiligen Parent-Pfad. Existiert der Child-Button dieses Levels bereits, bleibt dessen Alternative sichtbar, wird aber deaktiviert. Auch manuelle Eingabe desselben Werts wird mit einer Meldung abgewiesen. Eine andere Alternative darf gewählt werden und ersetzt den bisherigen Child-Level samt abhängigen Sub-Leveln.

### Faktenfilter
Oberhalb der linken Fakten-/Regel-TreeList stehen jetzt:

- ein Texteingabefeld zur Filterung nach Fakten-/Regelnamen,
- eine ComboBox mit `Alle` sowie `1` bis `100`,
- ein Filter-Button mit gezeichnetem Trichter-Symbol.

Die Zahl filtert exakt nach der Stelligkeit des Prädikats. `2` zeigt also nur Prädikate mit zwei Argumenten. `Alle` hebt den Arity-Filter auf. Der Namensfilter arbeitet unabhängig davon case-insensitiv.

### Dark-Mode Header
Der Header der Fakten-TreeList verwendet im Dark-Mode jetzt einen dunklen Hintergrund (`#161b22`) und weiße Schrift. Im Light-Mode wird der helle Header mit dunkler Schrift verwendet.

### Statuslabel
Die bestehende Logik bleibt erhalten:

- `weitere Alternativen vorhanden` – grün
- `keine weiteren Alternativen` – rot

Beim Löschen oder Ersetzen eines Levels werden ComboBox und Statuslabel verworfen und anhand des verbleibenden Parent-Pfads neu berechnet.

## Tests

Stage-62-spezifisch: 8/8 erfolgreich.
Gesamtprojekt: 636/636 erfolgreich.
