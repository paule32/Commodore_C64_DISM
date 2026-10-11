** Stage 310: native Windows keyboard detection (Raw Input API)
STORE iskeyboard() TO HatTastatur

IF HatTastatur = 1
    ? "Windows meldet eine Tastatur."
ELSE
    ? "Windows meldet keine Tastatur."
ENDIF

IF iskeyboard() .AND. ismouse()
    ? "Maus und Tastatur sind vorhanden."
ENDIF

IF .NOT. iskeyboard()
    ? "Keine Tastatur vom Raw-Input-System gemeldet."
ENDIF

? iskeyboard()
