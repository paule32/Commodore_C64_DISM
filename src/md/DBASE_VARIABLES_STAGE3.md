# dBase compiler – stage 3: variables and debug screen

Targets: Windows PE32 (IA-32) and Windows PE32+ (AMD64).

## Variables

Assignments are case-insensitive by name and create real runtime storage slots:

```dbase
X = 1
Y = 2 + 3 * 4
C = 'A'
S = "text 1" + "text 2"
H = 0x10 + $10 + 10h
```

Supported current value classes:

- numeric values, including decimal/floating expressions
- hexadecimal numeric literals: `0xFF`, `$FF`, `0FFh`
- char literal: a one-character single-quoted literal, e.g. `'A'`
- strings in single or double quotes

A variable may be assigned another type later. Every variable has generated internal fields for type, numeric value, string pointer and string length.

## Output

```dbase
? X
? "Wert von X = " + X
?? "ohne NewLine: " + X
```

`?` appends CR/LF. `??` does not.

`+` is numeric when both operands are numeric. If either operand is String/Char, it is concatenation and numeric values are formatted as text automatically.

## Functions in expressions

No-argument function calls are emitted as external symbols:

```dbase
foo = 5
X = foo + foobar() + 11
```

The assembly contains `extern foobar` and `call foobar`. The defining object/module must be supplied when linking the final executable. Current numeric return ABI:

- PE32: `double` in x87 `ST0`
- PE32+: `double` in `XMM0`

Function parameters are deliberately rejected until their dBase calling convention is implemented.

## Debug output console

```dbase
? "normal console"
SET FORMAT TO SCREEN
? "debug console"
?? "same debug line"
SET FORMAT TO CONSOLE
? "back on normal console"
```

`SET FORMAT TO SCREEN` starts a second `cmd.exe` with `CREATE_NEW_CONSOLE`. The generated program creates a Windows named pipe and the child console reads it through `more.com`. `?` and `??` are routed to this debug console until `SET FORMAT TO CONSOLE` is used.
