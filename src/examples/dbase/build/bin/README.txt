Stage 448 – einheitliche c64_dbase_runtime.dll

pe32/c64_dbase_runtime.dll = Windows i386 (32 Bit)
pe64/c64_dbase_runtime.dll = Windows AMD64 (64 Bit)

Exports:
  DBaseConsoleEnsure / Write / Shutdown / SetTitle
  DBaseCharIsLowerCP1252 / DBaseCharIsUpperCP1252
  DBaseCharIsLowerUtf8 / DBaseCharIsUpperUtf8

Neu erzeugen: bereits vorhandene Menüeinträge unter Werkzeuge sowie
Projekt-Einstellungen -> PE32/PE32+ -> Umgebung -> dBASE Runtime DLL erstellen.
Python-Buildpfad: d64dbase.runtime_builder.create_runtime_dll ->
d64dbase.console_runtime.build_dll (interner COFF-Assembler/PE-Linker).
Keine zusätzliche zweite Runtime-DLL und keine weiteren Menüeinträge nötig.
