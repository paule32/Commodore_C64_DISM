# Stage 58 – PROLOG Wissenswerte, Umlaute, ASM-Mini-Map und Alternativen-ComboBox

## Benannte Wissenswerte und String-Verkettung

```prolog
_apfel = "Ein Apfel ist ".
_apfel_gesund = _apfel + "gesund".
```

Der Compiler materialisiert `_apfel_gesund` als String `"Ein Apfel ist gesund"`.
`+` bleibt fuer zwei numerische Operanden numerische Addition. Bei zwei Strings
ist `+` String-Verkettung. Forward-Referenzen werden aufgeloest; Zyklen und
unbekannte benannte Wissenswerte erzeugen einen Compilerfehler.

Hinweis: Satzzeichen werden nicht entfernt. Mit
`_apfel = "Ein Apfel ist: ".` entsteht folgerichtig
`"Ein Apfel ist: gesund"`.

## Deutsche Umlaute

Benannte Wissenswerte und PROLOG-Atome koennen `ä`, `ö`, `ü`, `ß` sowie die
grossen Varianten in Variablennamen verwenden. Beispiel:

```prolog
_äpfel = "sind gesund".
äpfel(obst).
```

`_Äpfel` bleibt entsprechend der PROLOG-Regel eine Variable, waehrend
`_äpfel` ein benannter Wissenswert ist.

Der externe Datenbankloader normalisiert die relevanten UTF-8-Sequenzen, damit
statisch kompilierte und zur Laufzeit geladene Namen dieselben Atom-IDs treffen.

## Assembler-Editor

Der generierte ASM-Editor verwendet jetzt `SourceEditorWithMiniMap`. Er behaelt
damit den bestehenden `SourceTextEdit` inklusive Gutter, Breakpoints,
Bookmarks, Syntax-Hervorhebung und Navigation und erhaelt rechts dieselbe
`SourceMiniMap` wie der Rohdaten- und Markdown-Editor.

## Wissen-Datenbank-Browser: Alternativen

Alternativen werden fuer den jeweils naechsten noch offenen Level direkt in
einer `QComboBox` oberhalb der ScrollArea angezeigt. Eine Auswahl wird in die
Eingabezeile uebernommen und mit `Pruefen +` ueber denselben Resolver-Pfad wie
eine manuelle Eingabe geprueft.

Nach dem Hinzufuegen wird die ComboBox aus dem neuen Praefix neu berechnet:

```text
obst -> apfel -> gesund
```

zeigt danach nur noch die fuer dieses Praefix moeglichen Werte des naechsten
Levels.

Bei mehr als 10 Alternativen wird die ComboBox editierbar und bekommt einen
case-insensitiven `MatchContains`-Completer.

Direkt unter den Level-Buttons in der ScrollArea steht:

- gruen: `weitere Alternativen vorhanden`
- rot: `keine weiteren Alternativen`

Beim Loeschen eines Levels werden dessen Sub-Level, die ComboBox und das Label
zuerst geloescht. Anschliessend werden ComboBox und Label aus dem verbleibenden
Entscheidungspfad neu aufgebaut.

Die fruehere Pfeil-/Dialog-Auswahl bleibt intern nur als Kompatibilitaetscode
vorhanden; der Pfeil wird nicht mehr eingeblendet. Die sichtbare Auswahl laeuft
zentral ueber die ComboBox.
