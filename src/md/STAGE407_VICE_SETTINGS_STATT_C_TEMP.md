# Stage 407 – VICE-Konfiguration und Laufwerk 8 nicht mehr auf C:\TEMP umstellen

**Verbindliche Grundlage:** d64_dism_asm_406.zip.

## Reproduzierte Ursache

Stage 402–406 erzeugte vorbereitete Sprite-Dateien immer unter
`tempfile.gettempdir()/d64_dism_vice_drive8/<hash>`. Unter Windows ist das
üblicherweise `C:\Users\…\AppData\Local\Temp\...`. Die Startoption `-fs8`
setzte `FSDevice8Dir` dann für die laufende VICE-Sitzung auf diesen Ordner,
selbst wenn die persönliche `vice.ini` ein anderes Laufwerk-8-Verzeichnis
(z. B. auf `T:`) auswählte.

Das ist zunächst **ein Laufwerkspfadproblem**, nicht automatisch eine Änderung
des Speicherortes der VICE-`vice.ini`. VICE erlaubt außerdem explizites Laden
einer Konfiguration über `-config <datei>`.

## Korrektur

- `DISM → VICE-Einstellungen (vice.ini) ...` erlaubt die Auswahl einer
  bestehenden VICE-Konfiguration auf `T:`. Bei einem neuen VICE-Prozess wird
  diese mit `-config <datei>` geladen.
- `DISM → VICE-Laufwerk 8 (Verzeichnis) ...` legt das Verzeichnis fest,
  in das ladbare Sprite-Dateien kopiert werden. Es wird in QSettings unter
  `dism/vice_drive8_path` gespeichert.
- Priorität für die automatische Sprite-Bereitstellung:
  1. ausdrücklich gewähltes Laufwerk-8-Verzeichnis;
  2. `FSDevice8Dir` aus der ausdrücklich gewählten `vice.ini`;
  3. `<BASIC-Projektverzeichnis>/.d64_dism/vice_drive8`.
- Für neue Sprite-Kopien wird `C:\Temp` bzw. `%TEMP%` **nicht** mehr verwendet.
- Die originale binäre `.spr` bleibt unverändert. Die Version auf Laufwerk 8
  enthält zwei zusätzliche Ladeadressbytes (`00 30` für `$3000`).
- Existierende, fremde Dateien werden niemals überschrieben. Eine kleine
  `.d64_dism_vice_generated.json` im Laufwerk-8-Ordner erkennt ausschließlich
  von d64_dism erzeugte Kopien und ermöglicht deren spätere Aktualisierung.
- `DISM → VICE-Pfadzuordnungen zurücksetzen` entfernt die beiden
  zusätzlichen d64_dism-QSettings-Pfadzuordnungen.
- `VICE SETTINGS`, `VICE DRIVE8` und `VICE START` werden protokolliert.

## Hinweise

Ist im gewünschten Laufwerk-8-Verzeichnis bereits eine **originale rohe**
`sprites.spr` vorhanden, verweigert d64_dism das Ersetzen dieser Datei.
Bitte in diesem Fall einen **separaten** Ordner für VICE-Laufwerk 8 wählen,
z. B. `T:\C64\VICE_DRIVE8`.

Ein Start eines PRG direkt außerhalb von d64_dism kann diese Einstellungen
nicht automatisch übernehmen. Ein schon laufender VICE-Prozess lädt eine
später ausgewählte `vice.ini` nicht automatisch neu: VICE schließen und erneut
über d64_dism starten. Änderungen am Laufwerk über den Binary Monitor betreffen
zunächst die laufende Sitzung. In VICE die Einstellungen nicht speichern,
wenn nur ein vorübergehender Sprite-Dateizugriff gewünscht ist.

## Prüfungen

- Python-`py_compile` erfolgreich.
- 30 gezielte Tests (Stage 403/404/406/407) erfolgreich.
- Zusätzlich Stage-401/402-Tests ausgeführt; interaktiver Windows/VICE-
  End-to-End-Test ist nicht erfolgt.
- ZIP-Archiv auf Integrität geprüft.
