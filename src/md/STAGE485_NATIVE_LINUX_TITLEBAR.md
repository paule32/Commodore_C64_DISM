# Stage 485 – Native Titelleiste unter Linux, bisherige Titelleiste unter Windows

Verbindliche Basis: `d64_dism_asm_484.zip`.

## Verhalten

- **Windows (`sys.platform == "win32"`)**: unveränderte selbst gezeichnete `GreenBeigeTitleBar`, `Qt.FramelessWindowHint`, 3-Pixel-Fensterrahmen, die vorhandenen Resize-Catcher und die Fenster-Schaltflächen im eigenen Titelbalken.
- **Linux**: Qt-Hauptfenster mit nativer Titelleiste des Fenstermanagers; explizites Entfernen von `Qt.FramelessWindowHint` und von den manuellen Rahmenabständen. Die oberste Qt-Client-Zeile enthält **nur die bisherige Menüleiste**, keinen zweiten selbst gezeichneten Titelbalken und keinen unsichtbaren Platzhalter. Die nativen Schaltflächen zum Minimieren, Maximieren und Schließen stammen vom Desktop/Fenstermanager.
- **Sonstige Plattformen**: native Fensterdekoration wie unter Linux.

Die eigene Docking-Titelleiste (`DockTitleBar`) wird **nicht** verändert: Die Änderung betrifft ausschließlich die Titelleiste des Hauptfensters. Auch die Themenfarben der Menüleiste, die Dock- und Speicherlogik und sämtliche Compiler bleiben unverändert.

## Technische Umsetzung

In `d64_dism.py` wird beim Erzeugen des Hauptfensters einmal die plattformabhängige Entscheidung getroffen:

```python
self._use_custom_main_title_bar = sys.platform == "win32"
```

Die Entscheidung steuert die Window-Flags und Abstände, die Erzeugung von `GreenBeigeTitleBar` und die vorhandenen Resize-Catcher. Die Menüleiste (`main_menu_bar`) bleibt auf beiden Plattformen Bestandteil des `main_top_chrome`; unter Linux besteht dieses Qt-Widget nur aus der Menüleiste.

Bestehende Zugriffe auf `main_title_bar` sichern den Zugriff mit `hasattr(...)` ab, damit das unter Linux nicht erzeugte Widget dort nicht angesprochen wird.

**Hinweis:** Die exakte Darstellung der nativen Linux-Titelleiste hängt vom Fenstermanager und (bei Wayland) der Dekorations-Unterstützung des Compositors ab. Es wird keine eigene Titelleiste mehr gezeichnet.

## Überprüfung

`test_stage485_native_linux_titlebar.py` isoliert die Original-Methode zur Erzeugung der Fenster-Chrome und prüft mit Qt-Stubs beide Zweige: native Linux-Titelleiste ohne separates Client-Widget, Windows-Zweig mit bestehender Titelleiste, korrekter Menüposition, Win32-only Frame-Flags/Resize und abgesicherte Titelleisten-Zugriffe.

Die reguläre Python-Syntaxprüfung wurde durchgeführt; die gezielten Stage-481/474/485-Tests bestanden (14 Tests). Eine interaktive Qt5-/Linux-/Windows-GUI-Abnahme war in der aktuellen Testumgebung ohne installiertes PyQt5 nicht möglich.
