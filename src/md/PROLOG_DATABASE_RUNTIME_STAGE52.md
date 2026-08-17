# PROLOG Database Runtime Stage 52

Stage 52 fixes the two GDB crashes reported after Stage 51.

## 1. `arzt_patient.exe` – crash at `0x00402E9F`

The crash is in the structure serializer used by `database_save/1`.

Stage 51 kept the next argument-link handle in `ECX`:

```asm
__rt_emit_term_struct_loop:
    ...
    push __prolog_text_comma_space
    call __rt_emit_text
    add esp, 4
    mov eax, ecx
    call __rt_node_ptr
```

`__rt_emit_text` calls helpers which use `ECX`, so the link handle was no longer
valid for the second and following structure arguments.

Stage 52 preserves it explicitly:

```asm
    push ecx
    push __prolog_text_comma_space
    call __rt_emit_text
    add esp, 4
    pop ecx
```

This applies to facts such as:

```prolog
name(4711, "Max Mustermann").
```

and therefore to the save path of `arzt_patient.pl`.

## 2. External rule parser – variable identity

The Stage 51 database parser cached `__prolog_db_parser_var_count` in `ECX` and
then called `__rt_token_eq`. `__rt_token_eq` itself uses `ECX` as its character
index, so a failed token comparison destroyed the table bound/index used when
creating or locating the next variable.

That is particularly relevant to:

```prolog
hoher_blutdruck(Patient) :-
    blutdruck(Patient, Systolisch, _),
    Systolisch > 140.
```

Stage 52 compares the scan index directly with the authoritative count in
memory and reloads the count at the NEW path:

```asm
__rt_db_parser_var_scan:
    cmp edx, dword ptr [__prolog_db_parser_var_count]
    jae __rt_db_parser_var_new
    ...

__rt_db_parser_var_new:
    mov ecx, dword ptr [__prolog_db_parser_var_count]
```

The same correction is applied to the interactive query variable table.

## 3. Loaded rule body → goal chain

The lexical cut/choice barrier was cached in caller-clobbered `EDX` across
recursive `__rt_goal_expr_to_chain` calls. Stage 52 reads the stable third
function argument (`[EBP+16]` on PE32) whenever a new goal link is built or a
recursive branch is entered.

This avoids geometry/choice corruption while expanding conjunctions from
externally loaded rules.

## 4. Stage 52 diagnostic example builds

`examples/prolog_database/generated_stage52/` contains fresh PE32 builds made
with the Stage 52 internal assembler/linker:

- `arzt_patient.exe`
- `arzt_patient.generated.pe32.asm`
- `arzt_patient.symbols.map`
- `arzt_mit_fachwissen.exe`
- `arzt_mit_fachwissen.generated.pe32.asm`
- `arzt_mit_fachwissen.symbols.map`

The maps use:

```text
VA = 0x00401000 + .text symbol offset
```

For example, both Stage 52 example images map `__rt_deref` to `0x00401240`.

## 5. GDB check

Run from the example directory:

```text
gdb arzt_patient.exe
(gdb) r
```

and:

```text
gdb arzt_mit_fachwissen.exe
(gdb) r
```

If another PC is reported, look it up in the matching `.symbols.map`.
For additional context these GDB commands are useful:

```text
(gdb) bt
(gdb) info registers eax ebx ecx edx esi edi esp ebp
(gdb) x/12wx $esp
(gdb) x/8i $pc-16
```

## 6. Regression status

Stage 52 adds tests for:

- serializer `ECX` preservation;
- external database variable table scanning;
- interactive query variable table scanning;
- stable rule-body cut barrier;
- internal PE32 and PE32+ linking of both database examples.

Full project regression: **551 tests, all passing**.

The current execution environment cannot run Windows PE files natively, so the
final runtime execution remains a Windows/GDB verification step.
