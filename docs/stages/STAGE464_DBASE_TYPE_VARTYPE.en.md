[Deutsch](STAGE464_DBASE_TYPE_VARTYPE.md) | [English](STAGE464_DBASE_TYPE_VARTYPE.en.md)

# Stage 464 – dBASE TYPE() and VARTYPE()

Implements runtime type inspection: `TYPE("xyz")` queries the current type of a memory variable named by a direct string argument, while `VARTYPE(xyz)` queries the type of a variable expression and supports other typed expressions/literals in the console compiler. In this stage, reported type letters include `N` (numeric), `C` (character/string), and `U` (undefined/NULL), with WFM object handling following its slot model. The compiler/runtime distinguish dynamic changes in value type instead of relying on static source assumptions. Tests cover supported expressions and the generated PE targets.

## Source code and command examples (unchanged)

```dbase
STORE 123.45 TO xyz
? TYPE("xyz")       && N
? VARTYPE(xyz)      && N
IF TYPE("xyz") == "N"
    ? "numerisch"
ENDIF
STORE "Hallo" TO xyz
? TYPE("xyz")       && C
? VARTYPE(xyz)      && C
? TYPE("unbekannt") && U
```

