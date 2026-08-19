# Stage 131 – WFM Event-Referenz korrigiert

Die kanonische WFM-Syntax für Event-Prozeduren lautet:

```dbase
<EventName> = CLASS::<EventProcedure>
```

Beispiel:

```dbase
THIS.PushButton1 = NEW PUSHBUTTON(THIS, "press me")

WITH (THIS.PushButton1)
    OnClick = CLASS::PushButton1_OnClick
ENDWITH

procedure PushButton1_OnClick(Sender)
    /* Event Code */
    return
```

Der fehlerhafte Stage-130-Präfix `CLASS*::` wird nicht mehr erzeugt.

Aus Kompatibilitätsgründen kann der WFM-Parser vorhandene Stage-130-Dateien
mit `CLASS*::` weiterhin lesen. Intern werden diese beim Einlesen sofort auf
`CLASS::` normalisiert und beim nächsten Speichern korrekt geschrieben.

Die Runtime-Eventbrücke ändert sich dadurch nicht. Sie erhält weiterhin nur
den extrahierten Prozedurnamen und die Callback-Adresse des kompilierten
WFM-Programms.
