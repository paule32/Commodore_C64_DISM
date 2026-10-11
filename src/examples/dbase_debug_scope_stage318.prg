// Normale .prg-Datei: SET DEBUG gilt vor und nach Routinen.
SET DEBUG OFF
#include "dbase_debug_scope_stage318.h"
PROCEDURE MakeVisible()
    SET DEBUG ON
    ? "In PROCEDURE: Debug an"
    RETURN
FUNCTION MakeHidden()
    SET DEBUG OFF
    RETURN 42
MakeVisible()
? "Rueckkehr aus PROCEDURE: immer noch Debug an"
X = MakeHidden()
? X
SET DEBUG ON
? "Ausgabe wieder sichtbar"
