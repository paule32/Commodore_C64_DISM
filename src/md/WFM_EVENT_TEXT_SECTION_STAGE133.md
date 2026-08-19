# Stage 133 – WFM Events nur als ausführbarer Code

Der in Stage 132 zusätzlich eingebettete UTF-8-Quellblock wurde vollständig
aus der EXE-Erzeugung entfernt.

Die Aufteilung lautet jetzt:

```text
.text
    __dbase_wfm_entry
    __dbase_wfm_proc_PushButton1_OnClick
    __dbase_wfm_proc_Helper
    ...
    -> ausführbarer Maschinen-Code

.data
    Widget-/Timer-Handles
    Captions/Property-Strings
    Strings für ? / ??
    ...
    -> reine Laufzeitdaten
```

Es werden keine `__dbase_wfm_proc_source_*`-Labels mehr erzeugt und kein
`PROCEDURE/FUNCTION ... RETURN`-Quelltext wird als `db ...` in die PE-Datei
geschrieben.

Alle im WFM definierten Methoden erhalten ein ausführbares
`__dbase_wfm_proc_<Name>`-Label in `.text`. Damit sind auch von Eventhandlern
aufgerufene Hilfsprozeduren Bestandteil des ausführbaren Codes.

`RETURN <Integer|Boolean>` erzeugt jetzt ebenfalls echten Code (`mov eax,...`).
Nicht unterstützte RETURN-Ausdrücke oder andere noch unbekannte Statements
brechen den Compile-Schritt ab, statt Logik still zu verlieren.
