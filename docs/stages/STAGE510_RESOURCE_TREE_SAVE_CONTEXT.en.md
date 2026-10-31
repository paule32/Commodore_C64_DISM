[Deutsch](STAGE510_RESOURCE_TREE_SAVE_CONTEXT.md) | [English](STAGE510_RESOURCE_TREE_SAVE_CONTEXT.en.md)

# Stage 510 – Save and Save As in the Resource Tree Context Menu

Adds **Save** and **Save As…** to the Resource Tree's context menu, calling `WindowsResourceEditorWidget.save()` and `.save_as()` respectively. Saving an unnamed file follows the existing Save As flow and Qt file dialog. **Ctrl+S** is displayed with `QKeySequence.Save`; the main window's existing shortcut still routes to the active resource workspace. The seven New actions and Select/Copy/Paste/Delete remain after a separator, with no removal of earlier functionality. Tests verify wiring and unchanged menu commands.

## Source code and command examples (unchanged)

```
Speichern                  Strg+S
Speichern unter ...
-------------------------------
Neu:  Dialog
Neu:  Menü
Neu:  Text
Neu:  Icon
Neu:  Bitmap
Neu:  Cursor
Neu:  RCDATA
-------------------------------
Alles auswählen
Kopieren
Einfügen
Löschen
```

