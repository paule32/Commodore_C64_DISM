[Deutsch](STAGE400_C64_BASIC_DIALEKT.md) | [English](STAGE400_C64_BASIC_DIALEKT.en.md)

# Stage 400 – C64: Compiler → BASIC → Dialect

**Authoritative starting point:** `d64_dism_asm_399.zip`.

## User interface

The Project Settings dock has **Compiler → BASIC** pages under the C=64 profiles `68000`, `68010`, `68020`, and `68030`. Each page contains a **Dialect** group box with two mutually exclusive radio buttons:

- `BASIC V2` (default)
- `Simon BASIC`

The existing light/dark theme styling is reused. Profile `68010` was added consistently with the other C64 project settings. This does **not** add a new compiler target or processor backend.

## Project file

Each profile stores its own dialect in the INI section `Settings.C64.<Profile>.Compiler.BASIC`:

```ini
[Settings.C64.68000.Compiler.BASIC]
Title = C=64 68000 BASIC Dialekt
Dialect = basic_v2

[Settings.C64.68010.Compiler.BASIC]
Title = C=64 68010 BASIC Dialekt
Dialect = simon_basic
```

For older projects or invalid values, `basic_v2` is the default. Switching the radio button refreshes the project configuration, marks it modified, and persists the value like other project settings.

## Scope limitation

`Simon BASIC` is only a **saved project setting** at this stage. No Simon-BASIC tokens, lexer/parser, code generator, or VICE runtime have been added.

## Verification

- `python -m py_compile d64_dism.py`.
- Five Stage-400 tests covering profiles, defaults, INI round-trip, GUI wiring, and profile-switch persistence.
- Sixteen existing Stage-394/395/399 regression tests passed.
- ZIP integrity and unchanged unrelated files verified.

Interactive Qt5 testing on Windows is still outstanding.
