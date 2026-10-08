CHM Viewer – Topic-Pfeile + eigene Titelleiste
=================================================

Basis:
- chmviewer.py mit Python-generierten Web-Scrollbar-Pfeilen

Neu:
1. Themen/Topic-Scrollbars:
   - Native Qt-Scrollbars der Themen-, Schlüsselwort- und Favoriten-Bäume
     erhalten gelbe Pfeile (#ffd84a), direkt durch Python/QPainter.
   - Die Web-Topic-Seite erhält zusätzlich Python-injizierte Pfeilbuttons
     oben/unten bzw. links/rechts als Fallback für QtWebEngine-Versionen,
     die ::-webkit-scrollbar-button nicht sichtbar rendern.

2. Eigene Titelleiste:
   - Hauptfenster ist Qt.FramelessWindowHint.
   - Titelleiste wird vollständig mit QPainter gezeichnet.
   - Dark Mode: Verlauf von Schwarz über Dunkelgrau nach Grau.
   - Buttons: Minimieren, Maximieren/Wiederherstellen, Schließen.
   - Buttons/Icons werden in Python gezeichnet.
   - Doppelklick auf Titelleiste maximiert/wiederherstellt.
   - Ziehen an der Titelleiste verschiebt das Fenster.

3. Fensterrahmen:
   - sichtbarer 3-Pixel-Rahmen
   - 8 transparente Resize-Griffe:
     links, rechts, oben, unten und vier Ecken
   - passende Resize-Mauszeiger
   - Größenänderung respektiert minimumWidth/minimumHeight
   - Resize-Griffe verschwinden im maximierten Zustand

Prüfung:
- Python-Syntaxprüfung via py_compile: OK

Hinweis:
- Die Web-Topic-Pfeile werden aus Python per JavaScript in die geladene
  HTML-Seite eingesetzt, weil Chromium/QtWebEngine die CSS-Pseudoelemente
  für Scrollbar-Buttons je nach Version nicht zuverlässig anzeigt.

IC SVG Bibliothek – flexible externe Bauteilliste

Dateien:
- ic-svg-library.html: komplette Oberfläche
- data/components.js: empfohlene externe Bauteildaten für CHM/HelpNDoc
- data/components.json: JSON-Spiegeldatei für PHP/APIs

Webserver-Struktur:
/data/components.js
/data/components.json
/b0/74LS00.svg ...
/b90/74LS00.svg ...
/b180/74LS00.svg ...
/b270/74LS00.svg ...

Neue Bauteile werden nur in components.js ergänzt.
Unterstützte Felder: id, name, description, category, family, type, gates, 
inputs, package, file, rotations.

Die HTML-Seite lädt components.js über:
[::CustomServer::]/data/components.js

Warum JS statt fetch(JSON): Ein normales externes Script ist für lokal 
entpackte CHM-Seiten robuster und vermeidet typische CORS-Probleme von 
fetch/XHR.
