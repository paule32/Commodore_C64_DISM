[Deutsch](STAGE509_RESOURCE_TREE_KONTEXTMENUE_MENU.md) | [English](STAGE509_RESOURCE_TREE_KONTEXTMENUE_MENU.en.md)

# Stage 509 – Resource Tree Context Menu and MENU Template

The left Resource Tree gains a context menu with resource creation/editing actions and a new **Menu** template button. `resource_rc_templates.py` supplies a compilable MENU source template and recognizes declarations for the live source outline. The tree and preview refresh when resources are added or edited. Read-only resources are protected; uncompiled templates are visibly marked instead of misrepresented as compiled bytes. `d64_dism.py`, the template module, and `test_stage509_resource_tree_context_menu.py` were updated; Python syntax and regression tests passed.

## Source code and command examples (unchanged)

```rc
IDM_MENU_1 MENU
BEGIN
    POPUP "Datei"
    BEGIN
        MENUITEM "Öffnen", 3011
        MENUITEM SEPARATOR
        MENUITEM "Beenden", 3012
    END
    POPUP "Hilfe"
    BEGIN
        MENUITEM "Über ...", 3013
    END
END
```

