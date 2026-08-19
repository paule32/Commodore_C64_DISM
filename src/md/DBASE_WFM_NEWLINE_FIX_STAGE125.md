# Stage 125 – WFM ASM newline fix

Der WFM-Fallback hat mehrere dynamisch erzeugte ASM-Teile mit dem
literalen Text `\\n` verbunden. Dadurch entstanden keine echten
Assemblerzeilen.

Betroffen waren:

- ergänzte `import`-Direktiven,
- der WFM-Komponenten-Body,
- der explizite Stage-124-Lifecycle,
- der angehängte Datenblock.

Diese Stellen verwenden jetzt echte `\n`-Zeilenumbrüche.

Beispiel:

Vorher logisch:
`import DBaseQtInitialize, "d64qt5.dll", "DBaseQtInitialize"\\nimport ...`

Jetzt:
`import DBaseQtInitialize, "d64qt5.dll", "DBaseQtInitialize"`
und die nächste Import-Direktive beginnt auf einer neuen physischen ASM-Zeile.
