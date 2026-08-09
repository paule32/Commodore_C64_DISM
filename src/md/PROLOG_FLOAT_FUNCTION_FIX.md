# PROLOG arithmetic float/1 fix

`float/1` now has the two required, context-dependent meanings:

- As an ordinary goal, `float(X)` is a type test and succeeds only if `X` is already a float term.
- Inside an arithmetic expression evaluated by `is/2` or a numeric comparison, `float(Expression)` recursively evaluates `Expression` and returns a float term.

Verified cases:

```prolog
?- X is float(1/2).                 % X = 0.5
?- X is float(1).                   % X = 1.0
?- X is float(1/2 / 1/2 / 2).      % X = 0.5 with the project fraction-grouping rule
?- float(0.5).                      % true
?- float(1).                        % false
```

The native PE32 and PE32+ runtime implements the same behavior through `__rt_eval_float`.
