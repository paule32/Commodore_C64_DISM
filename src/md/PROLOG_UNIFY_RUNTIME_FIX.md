# PROLOG Runtime: Unification Fix for `is/2`

## Symptom

The interactive query

```prolog
?- X is 1 + 2.
```

returned `false.` although parsing and arithmetic evaluation were correct.

## Root cause

`__rt_unify` kept the dereferenced right-hand term handle in `ECX`.
Immediately afterwards it called `__rt_node_ptr`, whose documented scratch
register is also `ECX/RCX`:

```asm
mov eax, esi
call __rt_node_ptr
```

`__rt_node_ptr` internally calculates the node address through ECX/RCX.  The
right term handle was therefore destroyed before the variable binding path.
For `X is 1+2`, `X` was effectively presented to `__rt_bind_var` as both the
variable and its own value.  The occurs-check correctly rejected that and the
solver reported failure.

The same register lifetime error also affected recursive LIST and STRUCT
unification, because their right-side link handles were kept in ECX across
`__rt_node_ptr` calls.

## Fix

The dereferenced right-hand term is now kept in `EBX` across node pointer
lookups.  In recursive STRUCT unification, right argument links are explicitly
saved/restored around calls to `__rt_node_ptr`.

This fixes:

- variable <-> value unification
- `is/2` result binding
- ordinary `=/2` variable binding
- LIST unification
- STRUCT/compound unification
- dynamic database matching paths that depend on the same runtime unifier

## Native verification

The generated PE32+ machine code was mapped and its native runtime functions
were called directly.  The Windows output imports were stubbed only for the
verification harness; parsing, arithmetic, heap, trail, unification and solver
code were executed natively.

Verified queries:

```prolog
?- X is 1 + 2.          % X = 3
?- X = 42.              % X = 42
?- [X,b] = [a,b].       % X = a
?- f(X,2) = f(1,2).     % X = 1
```

For `X is 1+2`, the native solver reports one solution and the query variable
dereferences to a `NODE_INT` whose value is 3.

## Targets

The runtime emitter is shared by both backends, so the same fix is emitted for:

- Windows PE32 / IA-32 / COFF32
- Windows PE32+ / AMD64 / COFF64

Both targets assemble and link through the internal d64_dism toolchain.
