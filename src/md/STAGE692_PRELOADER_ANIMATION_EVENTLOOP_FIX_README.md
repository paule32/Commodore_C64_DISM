# Stage 692 – animierter Preloader trotz blockierender Ladeprozesse

**Verbindliche Basis:** Stage 691 (`d64_dism_stage691.zip`).

## Fehlerursache

`QMovie.start()` startet die GIF-Wiedergabe, erzeugt aber keinen eigenen
Ereignisloop. In Stage 691 blockierten sowohl `time.sleep(1.5)` und der
anschließende synchrone Import von `d64_dism` als auch die synchronen
Dock-Öffnungsmethoden den GUI-Thread. Dadurch zeigte `loader.gif` nur ein
Standbild, während der eigentliche Ladevorgang dauerte.

## Korrektur

- `splash_animation_bridge.py`: Kleiner, optionaler Subprozess-Controller.
  Er startet mit `sys.executable` einen zweiten Python-/Qt-Prozess, überträgt
  nur Show-/Hide-Kommandos und Koordinaten über `stdin` (JSON Lines). Der
  Childprozess bestätigt eine gültige Qt-/GIF-Initialisierung mit `READY`.
- `examples/splash_animation_worker.py`: Eigener `QApplication`-Ereignisloop;
  `QMovie` läuft dort, auch wenn der Hauptprozess synchron importiert oder
  einen GUI-Dock aufbaut. Der Worker zeichnet entweder den originalen
  C64-Start-Splash oder ein transparentes, mausdurchlässiges 30×30-Overlay
  über dem bestehenden Dock-Preloader in der rechten oberen Ecke. Der
  Zeichencode des originalen C64-Splashes wird wiederverwendet.
- `examples/__main__.py`: Verwendet den unabhängig animierten Startup-Splash.
  Der blockierende `time.sleep(1.5)`-Aufruf entfällt. Startet der Worker
  nicht, bleibt der bisherige lokale `QSplashScreen` als Fallback erhalten.
- `d64_dism.py`: Positioniert den unabhängigen Preloader am bisherigen
  `D64OperationPreludeDialog`-Ladeicon und blendet ihn beim Schließen wieder
  aus. Bestehende Ladeleisten, Themes und Dock-Aktionen bleiben erhalten.
- Der Worker beendet sich beim Beenden des Hauptprogramms über `stdin`-EOF,
  auch wenn der Hauptprozess ungeplant terminiert.

## Voraussetzungen und Einschränkungen

`data/loader.gif` muss weiterhin neben `d64_dism.py` liegen. Das GIF selbst
ist nicht Teil der ZIP-Datei. Es muss ein **animiertes GIF mit mindestens zwei
Frames** sein. Bei fehlender/defekter Grafik wird keine Animation angezeigt.

Der separate Renderer wird beim direkten Start über einen Python-Interpreter
aktiviert. Bei einem *frozen* Build (gepackte EXE ohne externen Python-Interpreter)
bleibt aus Sicherheitsgründen der ursprüngliche lokale QMovie-Pfad erhalten.
Dessen Animation kann während synchroner CPU-/GUI-Arbeit weiterhin einfrieren;
ein eigenes EXE-Worker-Entrypoint müsste für den jeweiligen Packager vorgesehen
werden. Diese Einschränkung gilt nur für eingefrorene Builds.

Zur Fehlerdiagnose unter Windows im Terminal vor dem Programmstart:

```powershell
$env:D64_SPLASH_DEBUG = "1"
```

Der Worker gibt dann den GIF-Pfad und die von Qt erkannten Frame-/Animations-
Eigenschaften auf `stderr` aus.

## Tests

- **75 gezielte Tests bestanden**: Stages 620, 685–692.
- Einschließlich eines echten (Qt-freien) Subprozess-Tests für das JSON-
  Kommando-Protokoll, Prozessbeendigung und fehlgeschlagenes Ready-Handshake.
- Syntax der geänderten Python-Module geprüft.
- Ein visueller nativer PyQt5-Test unter Windows bleibt erforderlich, da das
  lokale Testsystem kein PyQt5 enthält.
