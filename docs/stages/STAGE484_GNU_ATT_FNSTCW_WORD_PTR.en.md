[Deutsch](STAGE484_GNU_ATT_FNSTCW_WORD_PTR.md) | [English](STAGE484_GNU_ATT_FNSTCW_WORD_PTR.en.md)

# Stage 484 – GNU AT&T: FNSTCW and FLDCW Require WORD Memory Operands

Fixes x87 control-word instructions in GNU AT&T conversions: `FNSTCW` and `FLDCW` operate on **16-bit WORD memory**, not incorrectly inferred wider operands. `windows_asm_att.py` preserves the 16-bit width after syntax conversion for PE32 and PE64. `test_stage484_att_x87_control_word.py` contains nine regression tests, including real internal assembly, machine-code byte comparisons, and full instruction layout checks. The change is restricted to control-word memory forms.

## Source code and command examples (unchanged)

```asm
fnstcw word ptr [esp]    ; Intel
fnstcw (%esp)            # AT&T
```


```asm
fnstcw (%esp)            # AT&T         -> fnstcw word ptr [esp]
fldcw 4(%esp)            # AT&T         -> fldcw word ptr [esp+4]
fnstcw (%rsp)            # AT&T, PE64   -> fnstcw word ptr [rsp]
fldcw 4(%rsp)            # AT&T, PE64   -> fldcw word ptr [rsp+4]
```

