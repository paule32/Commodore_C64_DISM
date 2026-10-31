[Deutsch](STAGE501_DBASE_SESSION_DESIGNER.md) | [English](STAGE501_DBASE_SESSION_DESIGNER.en.md)

# Stage 501 – dBASE Form Designer: SESSION Component

Adds a nonvisual **SESSION** component to the dBASE Form Designer. Its transparent 36×36 database/user icon (`assets/dbase_session_36.png`) is embedded through `d64dbase.session_designer.session_icon_png_bytes()` and centered in the existing 42×42 nonvisual component frame. A Session Inspector exposes relevant properties, events, and methods for user/database session management. WFM source generation and editing keep the component's stable identity and references. Tests validate icon representation, inspector categories, and component serialization; actual Windows UI behavior requires confirmation.

## Source code and command examples (unchanged)

```dbase
    function SESSION1_addAlias(param)
        return SESSION::addAlias(param)
```

