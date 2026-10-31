[Deutsch](STAGE465_DBASE_LOGICAL_DATE_EVENT_TYPE_COMMENTS.md) | [English](STAGE465_DBASE_LOGICAL_DATE_EVENT_TYPE_COMMENTS.en.md)

# Stage 465 – Logical and Date Types in TYPE()/VARTYPE(); WFM Event Comments

Extends dBASE typing with true logical and date values: `STORE .T. TO xyz` and `.F.` store Boolean values; `STORE {^2026-10-19} TO xyz` stores a date using an ISO representation. `TYPE("xyz")` and `VARTYPE(xyz)` return `L` or `D` accordingly, including after dynamic type changes. WFM event parsing also accepts inline `&&` comments without treating their text as executable statements. Compiler and runtime tests cover literals, values, and comment boundaries.

## Source code and command examples (unchanged)

```dbase
B = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE 123.45 TO xyz
        ? TYPE("xyz")       && N
        ? VARTYPE(xyz)      && N
        IF TYPE("xyz") == "N"
            ? "xyz ist numerisch"
        ENDIF
        STORE "Hallo" TO xyz
        ? TYPE("xyz")       && C
        ? VARTYPE(xyz)      && C
        STORE .T. TO xyz
        ? TYPE("xyz")       && L
        STORE {^2026-10-19} TO xyz
        ? VARTYPE(xyz)      && D
        RETURN
ENDCLASS
```

