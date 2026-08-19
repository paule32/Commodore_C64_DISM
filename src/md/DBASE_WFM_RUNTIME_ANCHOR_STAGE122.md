# Stage 122 – WFM Runtime Anchor Fix

Der WFM-Fallback verlangt nicht mehr `DBaseQtShowWindow` als feste
Einfügemarke.

Der erzeugte WFM-Aufbaucode wird jetzt eingefügt:

1. direkt nach `call DBaseQtInit`,
2. alternativ vor `call DBaseQtExec`,
3. alternativ vor `call DBaseQtShutdown`.

`DBaseQtFormOpen()` zeigt das erzeugte Formular selbst mit `show()`,
`raise()` und `activateWindow()` an. Ein zusätzlicher
`DBaseQtShowWindow`-Aufruf ist deshalb für WFM nicht erforderlich.
