[Deutsch](STAGE475_DBASE_MACRO_PREPROCESSOR.md) | [English](STAGE475_DBASE_MACRO_PREPROCESSOR.en.md)

# Stage 475 – dBASE Preprocessor for .prg and .wfm

The existing `d64dbase/compiler.py` preprocessor is also applied to WFM compilation. The editor's original source remains unchanged; preprocessing occurs on a temporary compile copy. Features include recursive `#include "file.h"` (include guards and cycle detection), `#define`/`#undef`, conditional `#ifdef`, `#ifndef`, `#if`, `#elif`, `#else`, and `#endif`, including nesting. Expressions support `<`, `<=`, `==`, `!=`, `>=`, `=>`, `>`, and legacy `=`/`<>`. Include files are searched relative to the including file, then the configured Windows PE32/PE64 compiler input directories. Tests check expansion, conditions, locations, and both compiler entry points.

## Source code and command examples (unchanged)

```dbase
#define MAKRO 2
#include "gemeinsam.h"

#if MAKRO => 2 && (2 + 3 * 4) == 14
    ? "aktiv"
#elif MAKRO == 1
    ? "alternativ"
#else
    #error Keine gueltige Einstellung
#endif

#if "String1" + "String2" == "String1String2"
    ? "Strings verknuepft"
#endif

#info Dies ist Infotext aus der Datei: #__FILE__
#warn Beispielwarnung in Zeile __LINE__
```

