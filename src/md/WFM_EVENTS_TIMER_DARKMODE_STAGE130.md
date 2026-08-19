# Stage 130 – WFM Events, Timer, Source und Dark-Mode

Die Anwendung startet im Dark-Mode (`dark_mode_enabled=True`) und zeigt im Dark-Mode das Sonnen-/Light-Symbol.

Im WFM-Tab **Quellcode** bleibt das normale DocumentEditor-Assemblerpanel verborgen. Der WFM-Quelltext ist editierbar. Beim Speichern werden handgeschriebene Prozeduren/Funktionen und Event-Zuordnungen zurück in das Designer-Modell übernommen.

Der Designer-Tab **Ereignisse** enthält drei Spalten: Ereignis, Prozedur und Navigation. Doppelklick auf einen nichtleeren Prozedurnamen erzeugt bei Bedarf z.B. `procedure PushButton1_OnClick(Sender)`, fügt `/* Event Code */` plus `return` ein und navigiert in den Quellcode. Event-Zuordnungen werden als `OnClick = CLASS*::PushButton1_OnClick` gespeichert.

Standardevents: OnClick, OnLostFocus, OnGetFocus, OnHover, OnMouseEnter, OnMouseLeave, OnMouseMove, OnMouseLeftClick, OnMouseRightClick, OnKeyDown, OnKeyUp, OnKeyRelease, OnTextChange. Timer verwendet OnInterval.

Timer wird als `THIS.Timer1 = NEW TIMER(THIS)` gespeichert. Properties: Name, Interval (Default 1000 Mikrosekunden), Active (.T./.F.). Runtime: echtes QTimer mit Qt::PreciseTimer; Qt5 arbeitet in Millisekunden, daher wird auf mindestens 1 ms gerundet.

Die Runtime führt keine Anwendungslogik aus. `DBaseQtObjectBindEvent` verbindet Qt-Signale nur mit Callback-Adressen im kompilierten WFM-Programm. Stage 130 emittiert bereits Programmcode für `? "Text"` und `?? "Text"`; bei GUI-WFM wird dafür erst bei Bedarf eine Windows-Konsole über `AllocConsole()` angelegt.

**Aktuelle Grenze:** Andere beliebige dBase-Statements innerhalb der Event-Prozeduren werden im Stage-130-Fallback noch als ASM-Kommentar erhalten und noch nicht nativ emittiert. Eventdispatch, Timer und `?`/`??` laufen bereits als Programmcode.
