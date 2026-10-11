** Stage 309: Windows-Mauserkennung (SM_MOUSEPRESENT)
STORE ismouse() TO HatMaus

IF HatMaus
    ? "Windows meldet eine Maus."
ELSE
    ? "Windows meldet keine Maus."
ENDIF

IF ismouse() .AND. HatMaus = 1
    ? "Maus ist aktiviert."
ENDIF

? ismouse()
