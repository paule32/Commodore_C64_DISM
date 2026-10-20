# Stage 465 – dBASE Logisch/Datum in TYPE()/VARTYPE() und WFM-Eventkommentare

**Verbindliche Grundlage:** Stage 464 (`d64_dism_asm_464.zip`).

## Neue dBASE-Typen

- `STORE .T. TO xyz` bzw. `.F.` speichert einen echten logischen Laufzeitwert.
- `STORE {^2026-10-19} TO xyz` speichert einen Datumswert mit ISO-Datumsrepräsentation.
- `TYPE("xyz")` und `VARTYPE(xyz)` liefern `L` oder `D`, wenn die aktuelle Variable den entsprechenden Typ besitzt; nach einem Typwechsel liefern sie wieder `N`, `C` usw.
- Für noch nicht vorhandene Variablen bleibt `U` erhalten.
- Konsoleninterpreter, dBASE-Konsolencompiler und WFM-Codegenerierung berücksichtigen diese Werte. Datumsangaben werden auf gültige Kalendertage geprüft.

## WFM-Events: Inline-Kommentar `&&`

Ein zusätzlicher Fehler aus Stage 464 trat **innerhalb von Event-Prozeduren** auf. Der WFM-Generator übergab bislang `? TYPE("xyz") && N` unverändert an den dBASE-Ausdrucksparser. Dieser meldete ein unerwartetes `&`.

Der WFM-Event-Compiler verwendet nun für die gesamte Prozedur den bereits vorhandenen `strip_dbase_comments`-Scanner, bevor die einzelnen Statements compiliert werden. Er berücksichtigt `&&`, `//`, `**`, `/* ... */` und beachtet String-Literale, Escape- und Doppelquotes. Zeilenumbrüche bleiben erhalten.

Beispiel:

```dbase
B = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE 123.45 TO xyz
        ? TYPE("xyz")       && N
        ? VARTYPE(xyz)      && N
        IF TYPE("xyz") == "N"
            ? "xyz ist numerisch"
        ENDIF
        STORE "Hallo" TO xyz
        ? TYPE("xyz")       && C
        ? VARTYPE(xyz)      && C
        STORE .T. TO xyz
        ? TYPE("xyz")       && L
        STORE {^2026-10-19} TO xyz
        ? VARTYPE(xyz)      && D
        RETURN
ENDCLASS
```

Die WFM-Prozedur wird weiterhin durch das zugeordnete Event (im Beispiel `PushButton1_onClick`) ausgelöst. Allgemeine dBASE-Statements außerhalb der `CLASS ... ENDCLASS`-Definition werden nicht automatisch zu einer Event-Prozedur; die bestehende Bootstrapping-Semantik bleibt unverändert.

## Runtime

Die Qt-unabhängige `c64_dbase_runtime.dll` enthält jetzt die Formatter-Varianten für die WFM-Typcodes `5` (Logisch) und `6` (Datum); `DBaseWfmClassifyType` ist entsprechend angepasst. Die mitgelieferten PE32- und PE32+-DLL-Dateien sind aus demselben Quellstand neu gebaut. Die elf DLL-Exportnamen bleiben bestehen.

- Logisch wird bei Textausgaben als `.T.` bzw. `.F.` formatiert.
- Datum wird mit dem gespeicherten UTF-8-Zeiger und der expliziten Bytelänge formatiert, etwa `2026-10-19`.

## Tests

- Tests für `TYPE()`/`VARTYPE()` mit numerischen, Zeichenketten-, logischen, Datums- und undefinierten Variablen sowie Typwechseln.
- Der genaue `&&`-Beispielcode **innerhalb** von `PushButton1_onClick()` für PE32 und PE32+ bis zum gelinkten PE-Image.
- String-Literale mit `&&` und mehrzeilige Blockkommentare innerhalb von WFM-Events.
- Runtime-DLL-Neuerzeugung, Exporttabellen, vorhandene WFM-, JSON-/Binär-, ABI- und Linkerregressionen.

**Ergebnis:** 182 Tests bestanden, 1 übersprungen. Native Windows-/Qt5-Ausführung der erzeugten Events hier noch nicht durchgeführt.
