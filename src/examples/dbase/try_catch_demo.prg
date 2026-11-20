// Stage 639: typisierte dBL-Exceptions mit ENDTRY.
#include "System.SysUtils"

CLASS EExample OF DbException
ENDCLASS

PROCEDURE DemoThrow()
    TRY
        THROW NEW EExample("Demofehler")
    FINALLY
        ? "FINALLY in DemoThrow"
    ENDTRY
    RETURN

TRY
    DemoThrow()
CATCH (DbException e)
    ? "Klasse: " + e.ClassName
    ? "Meldung: " + e.Message
CATCH (Exception e)
    ? "Andere Exception: " + e.error
FINALLY
    ? "Das Ende"
ENDTRY
