# C64 Pascal

Die Pipeline besteht aus zwei getrennten Stufen:

1. `C64PascalLexer.g4` und `C64PascalParser.g4` parsen Pascal mit ANTLR 4.13.2.
2. `compiler.py` erzeugt lesbaren MOS-6510-Assembler. Der in
   `d64_dism(5).py` integrierte Assembler erzeugt daraus das C64-PRG.

## Installation

```powershell
py -m pip install antlr4-python3-runtime==4.13.2
```

Der Ordner `c64pascal` muss neben `d64_dism(5).py` liegen.

## Aktueller Sprachumfang

- `program`, `const`, `var`, `begin` und `end`
- `Integer` (16 Bit), `Byte`, `Char`, `Boolean`
- Zuweisungen und Konstantenausdrücke
- `+`, `-`, `*`, `div`, `mod`, `and`, `or`, `xor`, `not`
- `=`, `<>`, `<`, `<=`, `>`, `>=`
- `if/then/else`, `while/do`, `repeat/until`, `for/to/downto`
- `break`, `continue`
- `Write`, `WriteLn`, `ClrScr`, `Poke`, `Inc`, `Dec`, `Halt`
- `Peek`, `Chr`, `Ord`, `Lo`, `Hi`
- Dezimalzahlen sowie C64-typische Hex- (`$`) und Binärliterale (`%`)

`DIV` und `MOD` arbeiten in dieser ersten Stufe vorzeichenlos. Stringvariablen,
Arrays, Records, benutzerdefinierte Prozeduren/Funktionen und Units sind für
die nächsten Ausbaustufen vorgesehen.

## Parser neu erzeugen

```powershell
py c64pascal\generate_parser.py T:\Tools\antlr-4.13.2-complete.jar
```

