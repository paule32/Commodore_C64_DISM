[Deutsch](STAGE487_LINUX_DBASE_WFM_QT5_BRIDGE.md) | [English](STAGE487_LINUX_DBASE_WFM_QT5_BRIDGE.en.md)

# Stage 487 – First Linux dBASE/WFM Integration

Builds on Stage 486 by allowing **Linux Ubuntu 22.04 32-bit** and **64-bit** for dBASE `.prg` and opened WFM forms. The Form Designer's target selector includes both. Compile creates `<name>.generated.linux32.asm` or `.linux64.asm`; Assemble/Compile+Link emits matching ELF object files (`.linux32.o`/`.linux64.o`) and limited statically linked executables. The documentation clearly distinguishes this first implementation from a fully working Linux WFM GUI port: Qt bridge/runtime behavior remains incomplete. Tests check target routing and emitted files.

## Source code and command examples (unchanged)

```bash
python -m pytest -q test_stage486_linux_elf.py test_stage487_linux_dbase_wfm.py
```

