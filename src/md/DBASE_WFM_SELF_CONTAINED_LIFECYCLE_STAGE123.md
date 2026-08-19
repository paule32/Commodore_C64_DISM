# Stage 123 – WFM self-contained Qt lifecycle

Der WFM-Fallback erzeugt bei fehlendem GUI-Lebenszyklus selbst `DBaseQtInitialize -> WFM -> DBaseQtExec -> DBaseQtShutdown`. Die Runtime exportiert `DBaseQtInitialize`; `DBaseQtInit` war kein gueltiger Export.
