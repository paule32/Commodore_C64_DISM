[Deutsch](STAGE420_C64_CALL_REDUCER.md) | [English](STAGE420_C64_CALL_REDUCER.en.md)

# Stage 420 – CALL Reducer: MOS6510 Runtime Dead-Code Elimination

**Basis:** `d64_dism_asm_419.zip` (see the German release notes for the exact baseline).

The **CALL reducer** option is added under C=64 → 68000/68010/68020/68030 → Compiler → Optimizer, immediately below STA reducer. Each profile saves `CALLReducer=true/false`; the default is off. The GUI passes the current value as `call_reducer` to the BASIC compiler. Both reducers are independent.

`c64basic/call_reducer.py` implements `reduce_runtime_calls`. After BASIC code generation, it identifies reachable runtime routines and removes unreferenced machine-code blocks while retaining externally referenced symbols, conservatively treating address references and preserving data, resources, and `.cbss`. This shrinks PRG output without changing the source. The documented demonstration reduces a 2,359-byte PRG to 1,117 bytes with CALL and STA reductions combined. Analysis is conservative but does not prove safety for every indirect or externally referenced assembly pattern; regression and assembled-PRG comparisons are included.
