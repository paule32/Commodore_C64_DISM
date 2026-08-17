# Stage 61 – PROLOG Wissen-Browser: Parent-Pfeil und pfadgebundene Alternativen

## Ziel

Der sichtbare Button eines gewählten Fakts bzw. jedes folgenden Entscheidungslevels besitzt rechts einen `▼`-Button, wenn unter diesem Parent weitere Werte möglich sind. Ein Klick auf `▼` öffnet die vorhandene Alternativen-ComboBox. Deren Inhalt stammt ausschließlich aus dem Parent-Pfad des geklickten Buttons.

## Beispiel

Für:

```prolog
obst(apfel, gesund, rot).
obst(apfel, gesund, gruen).
obst(apfel, essbar, ja).
obst(birne, gesund, gruen).
```

ergibt sich:

```text
[obst ▼]                 -> ComboBox: apfel, birne
[obst] -> [apfel ▼]      -> ComboBox: essbar, gesund
[obst] -> [apfel] -> [gesund ▼]
                           -> ComboBox: gruen, rot
```

## GUI-Verhalten

- `KnowledgeLevelButton.arrow_button` ist sichtbar, sobald `alternatives` nicht leer ist.
- Das gilt auch für den Root-/Prädikatbutton.
- Die ComboBox ist im Normalzustand verborgen.
- `▼` berechnet den Parent-Prefix und ruft `alternatives_for_level(predicate, parent_prefix)` auf.
- Die ComboBox zeigt nur diese Kind-Alternativen.
- Mehr als zehn Alternativen bleiben wie in Stage 58 durchsuchbar (`MatchContains`).
- Eine Auswahl wird in das Eingabefeld übernommen; `Prüfen +` validiert sie über den PROLOG-Resolver und fügt sie als Kind des geklickten Parents ein.
- Wird ein älterer Parent geöffnet und ein anderes Kind gewählt, werden frühere abhängige Sub-Level ersetzt.
- Löschen verwirft ComboBox-Kontext und Statuslabel; beides wird aus dem verbleibenden Pfad neu erzeugt.
- Grün: `weitere Alternativen vorhanden`.
- Rot: `keine weiteren Alternativen`.

## Tests

```text
628 Tests
628 erfolgreich
0 Fehler
```

Die PyQt5-Oberfläche konnte in der Containerumgebung nicht nativ angezeigt werden. Die GUI-Quellpfade und das PROLOG-Wissensmodell wurden durch Regressionstests geprüft.
