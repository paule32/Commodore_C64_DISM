# Gutter Breakpoints und Favoriten

## Bedienung

Der Texteditor besitzt links von den Zeilennummern zwei kompakte Markerspalten:

- linke Spalte: Breakpoint, hellrot
- rechte Spalte: Favorit / Bookmark, hellblau

In der jeweiligen Spalte gilt:

- Linksklick: Marker setzen
- Rechtsklick: Marker löschen

Die Marker werden intern mit `QTextCursor`-Positionen geführt. Bei normalen
Texteinfügungen und Löschungen wandern die Marker deshalb mit ihrem Textblock
mit.

## Favoriten-Menü

Das Hauptmenü `Favoriten` wird aus den hellblauen Gutter-Markern der geöffneten
Quelltext- und generierten ASM-Editoren aufgebaut. Ein Eintrag sieht z. B. so
aus:

    Zeile 42 — test.pas

Ein Klick aktiviert den Dokument-Tab, schaltet auf die passende Editoransicht,
setzt den Textcursor in die Zeile und zentriert sie im Editor.

Wird der Bookmark im Gutter per Rechtsklick gelöscht, wird der Menüeintrag
sofort entfernt.

## PE32-Pascal-Breakpoints

Für Pascal-Programme im Ziel `Windows PE32` und Modus `Console` werden die
roten Breakpoints beim Compile als Quellzeilen-Metadaten an den Pascal-Compiler
übergeben. Die Pascal-Quelle selbst wird nicht verändert.

Der Compiler setzt vor der AST-Anweisung der markierten Quellzeile intern einen
parameterlosen `ReadLn`-Aufruf ein. Dadurch wartet die laufende Konsole am
Breakpoint auf Enter/Return.

Das Verfahren erhält die originalen Quellzeilennummern für Parser- und
Compilerfehler. Änderungen an Breakpoints invalidieren einen vorhandenen Build,
so dass beim nächsten Start erneut kompiliert wird.

Breakpoints in C64-/Amiga-Zielen und im direkt editierbaren generierten ASM-Tab
sind in dieser Stufe visuelle Marker; die ReadLn-Instrumentierung ist gezielt
für Pascal/Windows-PE32-Console aktiviert.
