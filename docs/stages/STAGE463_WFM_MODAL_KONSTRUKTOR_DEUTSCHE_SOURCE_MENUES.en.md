[Deutsch](STAGE463_WFM_MODAL_KONSTRUKTOR_DEUTSCHE_SOURCE_MENUES.md) | [English](STAGE463_WFM_MODAL_KONSTRUKTOR_DEUTSCHE_SOURCE_MENUES.en.md)

# Stage 463 – WFM Headers, Modal Forms, Constructors, and German Editor Menus

Updates generated WFM form headers and constructor handling, including modal versus nonmodal display. Named bridge functions include `DBaseQtWfmModalParameter` (ordinal **1013**) to read an optional modal argument and `DBaseQtFormRun` (ordinal **1014**) to distinguish modal event-loop execution from nonmodal form display. Source editor context menus are translated into German while keeping familiar keyboard shortcuts. Reported tests include 80 automated cases, with one Windows/Qt-runtime-dependent case not executed; this is not a claim of complete native validation.

## Source code and command examples (unchanged)

```dbase
// Generated on <Datum>
//
PARAMETER bmodal
LOCAL B
B = NEW Form1(51,4)
if bmodal = .T.
   B.ReadModal()
else
   B.Open()
endif

CLASS Form1 OF FORM
    ...
ENDCLASS
```

