# Stage 121 – WFM Compiler-Fallback

## Behoben

1. Designer-WFM wird direkt mit `_compile_dbase_wfm_fallback()` kompiliert.
   Der allgemeine dBase-WITH/MENU-Parser wird nicht mehr vorgeschaltet.

2. Der Fallback-Shell wird mit `?? ""` erzeugt, damit auch ältere
   d64dbase-Versionen den Qt-GUI-Runtime-Shell erzeugen.

3. Fehlende Runtime-Imports werden unabhängig von einem
   `DBaseQtShutdown`-Marker in den vorhandenen Importblock eingefügt.

Damit verschwinden sowohl die falsche MENU-Property-Meldung für `Left`
als auch der Fehler über den fehlenden `DBaseQtShutdown`-Import.
