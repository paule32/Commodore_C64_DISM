# Stage 464 – dBASE TYPE() und VARTYPE()

Basis: `d64_dism_asm_463.zip`.

## Funktionen

- `TYPE("xyz")` liest den aktuellen Laufzeittyp der Memory-Variablen mit dem angegebenen Namen. Der Parameter muss in dieser Ausbaustufe ein **direktes konstantes Stringliteral mit einem einfachen Variablennamen** sein (keine dynamisch zusammengesetzte Namensausdruckskette). Nicht vorhandene oder noch nicht initialisierte Variablen liefern `"U"`.
- `VARTYPE(xyz)` liest den aktuellen Laufzeittyp des Variablenausdrucks direkt. Im Konsolen-Compiler werden auch andere typisierte Ausdrücke und Literale unterstützt. Der WFM-Eventcompiler unterstützt direkte WFM-Variablen und Literale.
- Unterstützte Typbuchstaben in dieser Ausbaustufe: `N` (numerisch), `C` (String/Char), `U` (undefiniert/NULL). WFM-Objektslots liefern zusätzlich `O`. Die vorhandene dBASE-Runtime unterscheidet derzeit keine gesonderten logischen oder Datums-Slottypen; dafür ist keine separate `L`-/`D`-Erkennung implementiert.
- Alle Funktionsnamen sind case-insensitive; die Rückgaben sind Strings der Länge 1.

## Beispiel

```dbase
STORE 123.45 TO xyz
? TYPE("xyz")       && N
? VARTYPE(xyz)      && N
IF TYPE("xyz") == "N"
    ? "numerisch"
ENDIF
STORE "Hallo" TO xyz
? TYPE("xyz")       && C
? VARTYPE(xyz)      && C
? TYPE("unbekannt") && U
```

## Technische Umsetzung

- `d64dbase/compiler.py`: Analyse, Interpreter, native PE32-/PE32+-Codegenerierung. TYPE/VARTYPE werden nicht als externe Qt5-Funktionen importiert. Bei einer bestehenden Variablen liest der generierte Code deren `*_type`-Feld; besonders wichtig bei Typwechseln nach IF-Verzweigungen. Werte ohne Variablenquelle nutzen die feststellbaren Typcodes.
- `d64_dism.py`: WFM-Compiler erzeugt nativen Code für STORE/Print/IF- und ELSEIF-Anweisungen mit TYPE-/VARTYPE-Ergebnissen. Er liest die bestehenden WFM-Type-Felder (`0=NULL`, `1=integer`, `2=float`, `3=string`, `4=object`). Die ABI bleibt unverändert.
- Keine neuen Qt5-Bridge-Exporte und keine Änderung der Qt5-Ordinal-ABI.

## Tests

`test_stage464_dbase_type_vartype.py`: Vorschau, Parameterprüfung, Typwechsel, unbekannte Variablen, Konsolen- und WFM-Builds inklusive vollständiger PE32-/PE32+-Assemblierung und Verlinkung.

Zudem 76 bestehende/neuere Compiler- und WFM-Tests sowie 90 bestehende Runtime-/PE-Tests; diese zwei Regressionstest-Sammlungen und die neue Testdatei umfassen insgesamt **166 bestandene Tests** und **einen übersprungenen**. Kein nativer Windows-GUI-Laufzeittest im Linux-Container möglich.
