# dBase Start: hard no-build fix

This revision removes the automatic Qt5 bridge builder from `d64_dism.py` entirely.

For dBase, pressing **Start** does exactly this:

1. Resolve `<working-directory>/<source-stem>.exe`.
2. Verify that the EXE exists.
3. Launch it with `subprocess.Popen`.

It does **not** compile, assemble, link, build/deploy `d64qt5.dll`, run an external make tool, or run a Qt project generator.

`d64qt5.dll` and the matching Qt5 runtime DLLs must already be available next to the generated EXE or through the Windows DLL search path. If Windows cannot load one of those DLLs, Windows reports the missing dependency when the EXE is launched; `d64_dism` does not attempt to build anything.

Release ZIPs contain no `__pycache__`, `.pyc`, or `.pyo` files, so stale Python bytecode cannot restore the previous automatic-build path.

Source marker:

```python
DBASE_START_HARD_NO_BUILD = True
```
