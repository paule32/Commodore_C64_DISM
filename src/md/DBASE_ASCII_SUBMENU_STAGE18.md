# dBase Qt5 Stage 18 – ASCII-Rahmen nur für Popup-Untermenüs

Stage 18 übernimmt den zuvor separat getesteten Qt5-Menücode in die produktive
`d64qt5.dll`-Bridge.

## Aufbau

Die Hauptmenüleiste bleibt ein normales `QMenuBar`-Widget. Nur aufgeklappte
`QMenu`-Popups werden als `AsciiPopupMenu` erzeugt und erhalten einen
CP437/Terminal-artigen Zeichenrahmen.

Verwendete Zuordnung:

- `B9` → `╣`
- `BA` → `║`
- `BB` → `╗`
- `BC` → `╝`
- `C8` → `╚`
- `C9` → `╔`
- `CA` → `╩`
- `CB` → `╦`
- `CC` → `╠`
- `CD` → `═`
- `CE` → `╬`

Der C++-Code verwendet die Unicode-Box-Drawing-Codepoints, damit die Darstellung
nicht von der Quelltextkodierung abhängt. Für den Rahmen wird `Terminal`, danach
`Courier New`, danach der System-Fixed-Font gewählt.

## Bestehende UI

Die beiden Lupen bleiben erhalten. `Konsole` ist immer als Tab vorhanden. Der
`DEBUG`-Tab wird weiterhin ausschließlich durch `SET DEBUG ON` eingeblendet und
mit `SET DEBUG OFF` entfernt.

Der äußere Seitenrahmen bleibt 3 Pixel stark. Die Trennkante direkt oberhalb der
Statusleiste ist 2 Pixel stark und verwendet dieselbe Farbe wie
`SET BORDERCOLOR TO`.

Der Texteditor behält Margin, Padding und Dokumentrand von 0 Pixel.

## Keine Compiler-ABI-Änderung

Für Stage 18 sind keine neuen C-ABI-Exports erforderlich. Der bestehende dBase-
Codegenerator und die bisherigen PE32/PE32+-Imports bleiben unverändert.
