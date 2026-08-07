# Header-Dateien im eingebauten Editor öffnen

Der linke Icon-Bereich behandelt C-Header nun wie C-Quelltexte.

Unterstützt werden durch die vorhandene Kleinschreibung der Dateiendung:

- `.h`
- `.H`
- gemischte Schreibweisen wie `.h`/`.H`

## Verhalten

Ein Doppelklick auf einen Header im linken Datei-Icon-Bereich ruft nun
`open_document(path)` auf. Der Header wird deshalb in einem Dokument-Tab des
integrierten Editors geöffnet und nicht mehr an die externe Standardanwendung
des Betriebssystems übergeben.

Der Filter **C** zeigt jetzt sowohl `.c`- als auch `.h`-Dateien an.

Die vorhandene C-Syntaxhervorhebung für Header wird automatisch aktiviert.
