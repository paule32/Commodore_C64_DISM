# Stage 107 – Brush Gradient und Border Shadow Color

## Brush / Gradient

Unter dem Brush-Root gibt es jetzt `Gradient`. Die ComboBox zeigt links eine
gezeichnete Vorschau und rechts den Namen. Verfügbar sind `Ohne Gradient`,
lineare horizontale/vertikale/diagonale Varianten, radiale Varianten und ein
konischer Gradient.

`Brush.Background` ist die Startfarbe und `Brush.Foreground` die Endfarbe.
Änderungen wirken sofort auf die aktuell selektierte Komponente. Ein aktiver
Gradient hat Vorrang vor dem Pattern; bei `Ohne Gradient` wird ein vorher
gewähltes Pattern wieder sichtbar.

## Border / Shadow Color

Der Border-Root enthält jetzt `Shadow Color`. Diese Farbe wird nur für die
Hard-Shadow-Stile verwendet. Sie ist unabhängig von der Border-Masterfarbe und
von den vier individuellen Farben von Left/Top/Right/Bottom.

Beide neuen Eigenschaften werden von Kopieren/Ausschneiden/Einfügen übernommen.
