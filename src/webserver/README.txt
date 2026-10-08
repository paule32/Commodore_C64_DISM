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
Unterstützte Felder: id, name, description, category, family, type, gates, inputs, package, file, rotations.

Die HTML-Seite lädt components.js über:
[::CustomServer::]/data/components.js

Warum JS statt fetch(JSON): Ein normales externes Script ist für lokal entpackte CHM-Seiten robuster und vermeidet typische CORS-Probleme von fetch/XHR.
