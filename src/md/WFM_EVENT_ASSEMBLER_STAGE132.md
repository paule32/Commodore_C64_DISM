# Stage 132 – WFM Event-Prozeduren als ASM und EXE-Inhalt

Beim Compile erhält jede gebundene WFM-Prozedur einen eigenen ASM-Callback:

```asm
__dbase_wfm_proc_PushButton1_OnClick:
    ...
    ret
```

Damit zeigt `DBaseQtObjectBindEvent()` auf Code der Anwendung, nicht auf
Anwendungslogik in der Runtime.

Aktuell nativ emittiert:
- `? <String|Zahl|Boolean>`
- `?? <String|Zahl|Boolean>`
- `RETURN`
- `EXIT`
- `Foo`, `Foo()`, `Foo(Sender)` für andere WFM-Methoden

Nicht unterstützte Event-Statements werden ab Stage 132 nicht mehr still als
Kommentar verworfen. Der Compile-Schritt meldet stattdessen einen konkreten
WFM-Compilerfehler.

Zusätzlich wird für jede WFM-Prozedur/Funktion der vollständige
`PROCEDURE/FUNCTION ... RETURN`-Block als UTF-8 in `.data` gelinkt:

```asm
__dbase_wfm_proc_source_PushButton1_OnClick:
    db ...
```

Der Block ist damit nach Compile → Assemble → Link Bestandteil der EXE.
