#include "System.SysUtils"

CLASS EWorkerFailure OF DbException
ENDCLASS

CLASS TWorker OF TObject
    PUBLIC PROPERTY Info = "uninitialized"

    PROCEDURE __ini__()
        TRY
            self.Info = "bereit"
        FINALLY
            ? "TWorker initialisiert"
        ENDTRY
        RETURN

    PROCEDURE Fail(message)
        TRY
            THROW NEW EWorkerFailure(message)
        FINALLY
            ? "Fail: FINALLY"
        ENDTRY
        RETURN

    PROCEDURE Run()
        TRY
            self.Fail("Fehler aus einer Klassenmethode")
        CATCH (DbException e)
            ? e.ClassName
            ? e.Message
            THROW e
        FINALLY
            ? "Run: FINALLY"
        ENDTRY
        RETURN
ENDCLASS

LOCAL worker AS TWorker
TRY
    worker = NEW TWorker()
    worker.Run()
CATCH (DbException e)
    ? "Aeusserer Handler: " + e.ClassName
    ? e.Message
FINALLY
    ? "Programm: FINALLY"
ENDTRY
