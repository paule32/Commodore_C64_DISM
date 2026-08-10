# dBase Stage 8 – C-artiger Makro-Praeprozessor und F2-Start

## IDE-Verhalten

Die frueheren d64_dism-Dokumenttabs `Konsole` und `DEBUG` werden fuer dBase nicht mehr angelegt.
Die Ausgabeoberflaeche gehoert ausschliesslich zur generierten Qt5-Anwendung (`d64qt5.dll`).
Der F2-Ablauf bleibt:

1. dBase -> ASM kompilieren
2. ASM -> COFF32/COFF64 assemblieren
3. Objekte/Archive linken
4. Qt5-Runtime deployen
5. erzeugte EXE unmittelbar starten

## Objektmakros

```dbase
#define foo 5
X = foo + 3 * 4
? X
```

liefert `17`.

## Funktionsmakros und Token-Pasting

```dbase
#define foo(x) bar ## x
bar5 = 14
? foo(5)
```

`foo(5)` wird vor dem dBase-Parser zu `bar5`.

Mehrere Parameter sind erlaubt:

```dbase
#define join(a,b) a ## b
foobar = 9
? join(foo,bar)
```

## Bedingungen

Unterstuetzt:

```text
#if
#ifdef
#ifndef
#else
#endif
```

Beispiele:

```dbase
#define foo 5

#ifdef foo >= 5
? "foo >= 5"
#endif

#if defined(foo) >= 5
? "ebenfalls aktiv"
#endif
```

`defined(foo)` ist in diesem dBase-Praeprozessor erweitert: Bei einem numerischen
Objektmakro liefert es dessen Wert, bei einem sonstigen definierten Makro `1`, bei
einem undefinierten Makro `0`. Dadurch ist die vom Projekt gewuenschte Schreibweise
`#if defined(foo) >= 5` fuer `#define foo 5` wahr.

Bedingungsbereiche sind scoped. Ein `#define`, das innerhalb eines `#if/#ifdef/#ifndef`
erzeugt wird, wird bei `#endif` verworfen. Beim Wechsel nach `#else` wird der
Makrostand vom Eintritt in den Scope wiederhergestellt.

## #pragma link

```dbase
#pragma link obj/foo.o
#pragma link lib/libfoo.a
```

Unterstuetzte Formate:

```text
.o
.obj
.a
.lib
```

Relative Pfade werden relativ zur dBase-Quelldatei aufgeloest. Die Dateien werden
nicht als Assemblertext gelesen, sondern dem finalen `link_coff32_inputs` bzw.
`link_coff64_inputs` als echte Linkereingaben hinzugefuegt.

## Strings und Kommentare

Makros werden nicht innerhalb von Stringliteralen oder Kommentaren expandiert.
Die bisherigen Kommentarformen `//`, `**`, `&&` und `/* ... */` bleiben erhalten.
