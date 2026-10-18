# -*- coding: utf-8 -*-
"""Stage 446: dBASE console runtime DLL for the internal PE32/PE32+ linker.

Generate the DLL using ONLY the built-in assembler and COFF/PE linkers.
No MinGW/clang/make is invoked. The original runtime body is reused from the
compiler to preserve Workstation, CONOUT$, CP1252 and scrollback semantics.
"""
from pathlib import Path

DLL_NAME = "d64_dbase_console.dll"
EXPORTS = ("DBaseConsoleEnsure", "DBaseConsoleWrite", "DBaseConsoleShutdown", "DBaseConsoleSetTitle")
IMPORTS = {
    "kernel32.dll": (
        "AllocConsole", "FreeConsole", "GetStdHandle", "CreateFileA",
        "GetConsoleScreenBufferInfo", "SetConsoleScreenBufferSize",
        "SetConsoleOutputCP", "SetConsoleTitleA", "GetConsoleWindow", "WriteFile",
    ),
    "user32.dll": ("ShowWindow", "SetWindowPos", "SetForegroundWindow"),
}


def assembly_source(target: str) -> str:
    """Standalone DLL assembly, preserving legacy console output semantics."""
    from .compiler import _DBaseCodeGenerator
    if target not in ("pe32", "pe64"):
        raise ValueError(f"Unbekannte Windows-Architektur: {target}")
    is64 = target == "pe64"
    lines = ["bits 64" if is64 else "bits 32", f'dllname "{DLL_NAME}"']
    for public, internal in zip(EXPORTS, (
        "__dbase_console_ensure", "__dbase_console_write",
        "__dbase_console_shutdown", "__dbase_console_set_title",
    )):
        lines.append(f"export {public}, {internal}")
    for dll, names in IMPORTS.items():
        for name in names:
            lines.append(f'import {name}, "{dll}", "{name}"')
    lines += ["section .text", "__dbase_console_dll_entry:", "    mov eax, 1",
              "    ret" if is64 else "    ret 12"]

    class _Emitter:
        def __init__(self):
            self.is64 = is64
            self.lines = lines

        def emit(self, line=""):
            self.lines.append(line)

    emitter = _Emitter()
    # Reuse the exact tested lazy AllocConsole/CONOUT$ implementation, but
    # compile it into the DLL instead of embedding it in every application.
    _DBaseCodeGenerator.emit_native_console_runtime(emitter, "__dbase_console_default_title")

    # Use a caller-selected title even if SetTitle was called before the first
    # output. NULL keeps the original title. The string pointer is borrowed:
    # callers must keep it valid for the lifetime of the process.
    label = "__dbase_console_title_selected"
    prefix = "    mov rcx, __dbase_console_default_title" if is64 else "    push __dbase_console_default_title"
    position = lines.index(prefix)
    if is64:
        lines[position:position + 1] = [
            f"    mov rcx, qword ptr [{label}]", "    test rcx, rcx",
            "    jne __dbase_console_title_ready", 
            "    mov rcx, __dbase_console_default_title",
            "__dbase_console_title_ready:",
        ]
    else:
        lines[position:position + 1] = [
            f"    mov eax, dword ptr [{label}]", "    test eax, eax",
            "    jne __dbase_console_title_ready",
            "    mov eax, __dbase_console_default_title",
            "__dbase_console_title_ready:", "    push eax",
        ]

    lines += ["", "__dbase_console_set_title:"]
    if is64:
        # Win64 RCX=CP1252 NUL-terminated title. ABI stack aligned for APIs.
        lines += ["    test rcx, rcx", "    je __dbase_console_set_title_done",
                  "    mov qword ptr [__dbase_console_title_selected], rcx",
                  "    cmp dword ptr [__dbase_console_ready], 0",
                  "    je __dbase_console_set_title_done",
                  "    sub rsp, 40", "    call SetConsoleTitleA", "    add rsp, 40",
                  "__dbase_console_set_title_done:", "    ret"]
    else:
        lines += ["    push ebp", "    mov ebp, esp",
                  "    mov eax, dword ptr [ebp+8]", "    test eax, eax",
                  "    je __dbase_console_set_title_done",
                  "    mov dword ptr [__dbase_console_title_selected], eax",
                  "    cmp dword ptr [__dbase_console_ready], 0",
                  "    je __dbase_console_set_title_done",
                  "    push eax", "    call SetConsoleTitleA",
                  "__dbase_console_set_title_done:",
                  "    mov esp, ebp", "    pop ebp", "    ret"]
    lines += ["", "section .data", "__dbase_console_default_title:",
              '    db "dBase Console [MODAL TEST]", 0',
              "__dbase_console_out_name:", '    db "CONOUT$", 0',
              "", "section .bss", "__dbase_console_ready:", "    resd 1",
              "__dbase_console_handle:", "    resq 1" if is64 else "    resd 1",
              "__dbase_console_window:", "    resq 1" if is64 else "    resd 1",
              "__dbase_console_written:", "    resd 1",
              "__dbase_console_info:", "    resd 8",
              "__dbase_console_title_selected:",
              "    resq 1" if is64 else "    resd 1"]
    return "\n".join(lines) + "\n"


def build_dll(target: str, destination: Path, *, assemble32, coff32, link32,
              assemble64, coff64, link64) -> Path:
    """Create a genuine Windows PE DLL using the application's own toolchain."""
    target = str(target).lower()
    source = assembly_source(target)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if target == "pe32":
        obj = coff32(assemble32(source, filename=str(destination.with_suffix('.asm'))))
        result = link32((obj,), entry_symbol="__dbase_console_dll_entry",
                        dll=True, dll_name=DLL_NAME)
    elif target == "pe64":
        obj = coff64(assemble64(source, filename=str(destination.with_suffix('.asm'))))
        result = link64((obj,), entry_symbol="__dbase_console_dll_entry",
                        dll=True, dll_name=DLL_NAME)
    else:
        raise ValueError(target)
    destination.write_bytes(result.executable)
    return destination


def deploy_runtime(output_path: Path, target: str, *, get_exports,
                   assemble32=None, coff32=None, link32=None,
                   assemble64=None, coff64=None, link64=None,
                   package_root: Path = None) -> Path:
    """Place the right-architecture DLL next to the generated executable.

    Existing DLLs are only accepted if machine and all exports match. A staged
    binary shipped with the project has priority so old runtime versions do
    not silently survive a compiler update. Without a staged binary the
    built-in assembler+linker are used (no external make/gcc invocation).

    ``get_exports(path, expected_machine)`` is the IDE's existing PE export
    parser and checks the real PE machine type, not just the file name.
    """
    import hashlib
    import shutil

    if target not in ("pe32", "pe64"):
        raise ValueError(f"Unsupported console runtime target: {target}")
    machine = 0x014C if target == "pe32" else 0x8664
    destination = Path(output_path).resolve().parent / DLL_NAME
    base = Path(package_root) if package_root is not None else Path(__file__).resolve().parent
    packaged = base / "bin" / target / DLL_NAME

    def valid(file: Path) -> bool:
        try:
            return set(EXPORTS).issubset(set(get_exports(file, machine)))
        except Exception:  # invalid/corrupt PE headers are not compatible DLLs
            return False

    if packaged.is_file() and valid(packaged):
        if packaged.resolve() == destination.resolve():
            return destination
        same = False
        if destination.is_file() and valid(destination):
            same = hashlib.sha256(packaged.read_bytes()).digest() == hashlib.sha256(destination.read_bytes()).digest()
        if not same:
            # Don't replace the destination before a fully validated binary
            # exists. A locked DLL causes an explicit error rather than an
            # unusable EXE with an incompatible runtime.
            shutil.copy2(packaged, destination)
    elif not valid(destination):
        if not all(callable(fn) for fn in (assemble32, coff32, link32,
                                            assemble64, coff64, link64)):
            raise FileNotFoundError("No valid dBASE console DLL and no internal linker available")
        build_dll(target, destination, assemble32=assemble32, coff32=coff32,
                  link32=link32, assemble64=assemble64, coff64=coff64,
                  link64=link64)

    if not valid(destination):
        raise ValueError(f"Incompatible or missing {target} console DLL: {destination}")
    return destination
