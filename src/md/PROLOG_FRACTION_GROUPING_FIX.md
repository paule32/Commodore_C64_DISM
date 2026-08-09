# PROLOG fraction grouping fix

`d64 PROLOG` treats a numeric `number/number` pair as one fraction operand
before the ordinary `*`, `/`, and `mod` operator layer.

This is an intentional d64 extension. It differs from ISO Prolog's purely
left-associative `/` operator chain.

Example:

```prolog
?- X is 1/2 / 1/2.
```

is parsed as:

```text
X is (1/2) / (1/2)
```

and therefore evaluates to:

```text
X = 1.
```

The same grouping applies in the source parser and in the native Windows REPL
parser used by PE32 and PE32+ executables.

Only numeric literal pairs receive this special grouping. General symbolic
expressions keep the normal multiplicative operator path, and parentheses can
always be used to force an explicit grouping.
