TRY
    TRY
        SET DEBUG ON
        SET FORMAT TO SCREEN

        SET BACKGROUND TO 1, 14, 176

        ? "hihi"
        ? "halöo"

        THROW NEW Exception("Ein Fehler")

    CATCH (Exception e)

        ? e.Message

    ENDTRY

FINALLY
    ? "Das Ende"
    //ExitProcess(0)
ENDTRY