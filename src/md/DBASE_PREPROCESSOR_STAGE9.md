# dBase Stage 9 – Präprozessor, Diagnostik und Start ohne Rebuild

Diese Stufe erweitert den dBase-Präprozessor und trennt Build und Start.

## Startverhalten

- F2: Compile -> Assemble -> Link -> erzeugte EXE starten.
- Die dBase-EXE wird nach dem Linken in das aktuell eingestellte Arbeitsverzeichnis von `d64_dism` geschrieben.
- Der `Start`-Button startet ausschließlich die bereits vorhandene `<Quellname>.exe` aus diesem Arbeitsverzeichnis.
- `Start` ruft weder Compiler noch Assembler noch Linker auf. Fehlt die EXE, wird nur eine Fehlermeldung angezeigt.
- Die IDE-Tabs `Konsole` und `DEBUG` bleiben entfernt. Die Qt5-Ausgabetabs befinden sich ausschließlich in der generierten dBase-Anwendung.

## Bedingte Übersetzung

```dbase
#if 0
    // dieser gesamte Block wird nicht kompiliert
    unfertiger code @@@
#endif
```

Unterstützt werden weiterhin verschachtelte/scoped Direktiven:

```text
#if
#ifdef
#ifndef
#else
#endif
```

Es gibt nur `#else`; fehlerhafte Schreibweisen werden als unbekannte Präprozessor-Anweisung abgewiesen.

## Diagnostik

```dbase
#info Diese Meldung erscheint unter Hinweise
#warning Diese Meldung erscheint unter Warnungen
#error Dieser Text beendet den Compilervorgang
```

Direktiven in inaktiven `#if 0`-Zweigen werden nicht ausgelöst.

## Vordefinierte Symbole

```text
__FILE__   Name/Pfad der aktuellen Quelldatei als String
__LINE__   physische 1-basierte Quellzeile als Zahl
__DATE__   Compilerdatum als String, z.B. "Aug 10 2026"
__TIME__   Compilerzeit als String, z.B. "21:15:42"
```

Beispiel:

```dbase
? "File: " + __FILE__ + ", Zeile: " + __LINE__
? "Build: " + __DATE__ + " " + __TIME__
```

`__LINE__` wird am Verwendungsort expandiert, auch wenn es in einem Makro steht:

```dbase
#define HERE __LINE__
? HERE
? HERE
```

Die beiden Ausgaben enthalten unterschiedliche Zeilennummern.

## Bestehende Makrofunktionen

Stage 8 bleibt erhalten:

```dbase
#define VALUE 5
#define make(x) var ## x

#ifdef VALUE >= 5
    ? "aktiv"
#endif

#if defined(VALUE) >= 5
    ? "ebenfalls aktiv"
#endif

#pragma link obj/foo.o
#pragma link lib/libfoo.a
```

`#pragma link` bindet `.o`, `.obj`, `.a` und `.lib` weiterhin als echte Linkereingaben in PE32 bzw. PE32+ ein.
