[Deutsch](STAGE502_SESSION_METHOD_BINDINGS.md) | [English](STAGE502_SESSION_METHOD_BINDINGS.en.md)

# Stage 502 – SESSION Method Bindings

Extends the SESSION component from Stage 501 with explicit method definitions and event/procedure bindings. The Form Designer's inspector can assign supported SESSION actions to WFM methods, and generated source maps those bindings through the runtime/compiler path. Session configuration remains project-scoped; invalid method identifiers are rejected instead of producing undefined native calls. Tests cover inspector state, generated declarations, and bindings.

## Source code and command examples (unchanged)

```dbase
THIS.SESSION1 = NEW SESSION(THIS)
WITH (THIS.SESSION1)
    deleteAlias = CLASS::SESSION1_DELETEALIAS
    Name = "SESSION1"
    Left = 80
    Top = 80
    Width = 42
    Height = 42
    lockRetryCount = 3
    lockRetryInterval = 1000
    Active = .F.
ENDWITH

function SESSION1_deleteAlias(param)
    return SESSION::deleteAlias(param)
```

