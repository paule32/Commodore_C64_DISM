[Deutsch](STAGE468_WFM_LOCAL_DEKLARATION.md) | [English](STAGE468_WFM_LOCAL_DEKLARATION.en.md)

# Stage 468 – LOCAL at Top Level and inside dBASE Procedures

Expands dBASE/WFM scope handling for `LOCAL name`, `LOCAL name = expression`, and multiple local declarators. Names are bound per procedure, including correct resolution when globals and nested scopes coexist. The compiler allocates distinct typed local slots so assignments in one routine cannot accidentally affect another. Top-level executable code and event methods both use the corrected local-variable path. Compilation and scope tests check generated layout; native runtime behavior is documented separately.

## Source code and command examples (unchanged)

```
WFM-Prozedur __dbase_top_level__: Statement noch nicht als Event-Assembler implementiert: local A = 9
```

