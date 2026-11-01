"""Standalone C64 Disassembler Win32 crash watchdog, modeled on PythonBDE.

No Qt import. Start before Qt loads to catch C extension and Qt crashes.
The existing start.exe launcher remains independent: its guard prevents duplicate
external crash dialogs if both start mechanisms are used.
"""
from __future__ import annotations

import faulthandler
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import threading
import uuid

try:
    from .gui_errors import append_error_log, log_path
except ImportError:
    from gui_errors import append_error_log, log_path

_LOCK = threading.Lock()
_STARTED = False
_PROCESS = None
_FATAL_HANDLE = None


def watchdog_arch() -> str:
    return "x64" if struct.calcsize("P") == 8 else "x86"


def project_directory() -> Path:
    return Path(__file__).resolve().parent.parent


def bundled_executable(architecture=None, root=None) -> Path:
    base = Path(root) if root is not None else project_directory()
    return base / "watchdog" / "win32" / f"watchdog.exe"


def cached_executable(architecture=None, env=None) -> Path:
    env = os.environ if env is None else env
    base = env.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Commodore_C64_DISM" / "watchdog" / f"watchdog.exe"


def hidden_process_kwargs(*, gui_executable=False) -> dict:
    if os.name != "nt":
        return {}
    # CREATE_NO_WINDOW is important for compiler subprocesses; GUI exe displays
    # its native crash window later, so never hide the GUI via SW_HIDE.
    kwargs = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    if not gui_executable:
        start = subprocess.STARTUPINFO()
        start.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        start.wShowWindow = 0
        kwargs["startupinfo"] = start
    return kwargs


def _find_compiler(arch: str) -> str | None:
    options = ("x86_64-w64-mingw32-g++", "g++") if arch == "x64" else ("i686-w64-mingw32-g++", "g++")
    for candidate in options:
        compiler = shutil.which(candidate)
        if not compiler:
            continue
        try:
            result = subprocess.run([compiler, "-dumpmachine"], capture_output=True,
                                    text=True, check=True, timeout=8,
                                    **hidden_process_kwargs()).stdout.casefold()
            matches = "x86_64" in result if arch == "x64" else any(x in result for x in ("i386", "i586", "i686"))
            if matches and any(x in result for x in ("mingw", "w64", "windows")):
                return compiler
        except (OSError, subprocess.SubprocessError):
            pass
    return None


def build_if_available(*, architecture=None, root=None, target=None) -> Path | None:
    arch = architecture or watchdog_arch()
    base = Path(root) if root is not None else project_directory()
    source = base / "watchdog" / "watchdog.cpp"
    binary = Path(target) if target is not None else cached_executable(arch)
    if binary.is_file():
        return binary
    if not source.is_file():
        return None
    compiler = _find_compiler(arch)
    if not compiler:
        append_error_log(f"Watchdog: MinGW-g++ ({arch}) fehlt; watchdog/build_mingw{32 if arch == 'x86' else 64}.bat verwenden.")
        return None
    temporary = binary.with_name(f".{binary.stem}.{uuid.uuid4().hex}.exe")
    try:
        binary.parent.mkdir(parents=True, exist_ok=True)
        command = [compiler, "-std=c++17", "-O2", "-municode", "-mwindows",
                   "-D_WIN32_WINNT=0x0601", "-static", "-static-libgcc", "-static-libstdc++",
                   "-o", str(temporary), str(source), "-lshell32", "-luser32"]
        result = subprocess.run(command, capture_output=True, text=True,
                                check=False, timeout=90, **hidden_process_kwargs())
        if result.returncode or not temporary.is_file():
            append_error_log(f"Watchdog: MinGW-Build fehlgeschlagen ({result.returncode}):\n{(result.stderr or result.stdout)[:6000]}")
            return None
        if not binary.is_file():
            os.replace(temporary, binary)
        return binary
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        append_error_log(f"Watchdog: Build-Fehler: {exc}")
        return None
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def fatal_log_path(pid=None) -> Path:
    return log_path().parent / f"d64_dism_fatal_{pid or os.getpid()}.log"


def install_faulthandler(path=None) -> bool:
    global _FATAL_HANDLE
    if _FATAL_HANDLE is not None:
        return True
    try:
        target = Path(path) if path is not None else fatal_log_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = target.open("w", encoding="utf-8", buffering=1)
        try:
            faulthandler.enable(file=handle, all_threads=True, c_stack=True)
        except TypeError:
            faulthandler.enable(file=handle, all_threads=True)
        _FATAL_HANDLE = handle  # MUST remain open until process exit
        return True
    except (OSError, RuntimeError, ValueError) as exc:
        append_error_log(f"Watchdog: faulthandler fehlgeschlagen: {exc}")
        return False


def _ready_event():
    import ctypes
    from ctypes import wintypes as wt
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateEventW
    create.argtypes = (ctypes.c_void_p, wt.BOOL, wt.BOOL, wt.LPCWSTR)
    create.restype = wt.HANDLE
    wait = kernel.WaitForSingleObject
    wait.argtypes = (wt.HANDLE, wt.DWORD)
    wait.restype = wt.DWORD
    close = kernel.CloseHandle
    close.argtypes = (wt.HANDLE,)
    close.restype = wt.BOOL
    name = f"Local\\D64_Watchdog_Ready_{os.getpid()}_{uuid.uuid4().hex}"
    handle = create(None, False, False, name)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateEventW")
    return name, handle, wait, close


def start_watchdog(*, app_name="Commodore C64 DISM", executable=None) -> bool:
    """Arm the native process monitor once; never block GUI startup on failure."""
    global _STARTED, _PROCESS
    if os.name != "nt" or os.getenv("D64_DISABLE_WATCHDOG") == "1":
        return False
    # The pre-existing Win32 start.exe already supervises this child and can
    # show its own crash dialog. Avoid two dialogs for one crash.
    if os.getenv("D64_LAUNCHED_BY_WATCHDOG") == "1":
        install_faulthandler()
        return False
    with _LOCK:
        if _STARTED:
            return True
        install_faulthandler()
        binary = Path(executable) if executable is not None else bundled_executable()
        if not binary.is_file() and executable is None:
            binary = cached_executable()
        if not binary.is_file() and executable is None:
            binary = build_if_available()
        if binary is None or not Path(binary).is_file():
            append_error_log("Watchdog: keine native EXE vorhanden; GUI startet ohne externen Watchdog.")
            return False
        event, close = None, None
        try:
            name, event, wait, close = _ready_event()
            command = [str(binary), "--pid", str(os.getpid()), "--role", app_name,
                       "--fatal-log", str(fatal_log_path()), "--error-log", str(log_path()),
                       "--ready-event", name]
            _PROCESS = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        close_fds=True, **hidden_process_kwargs(gui_executable=True))
            status = wait(event, 3000)
            if status != 0:
                append_error_log(f"Watchdog: native Bereitschaft nicht gemeldet (Wait={status})")
                return False
            _STARTED = True
            return True
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            append_error_log(f"Watchdog: Startfehler: {exc}")
            return False
        finally:
            if event is not None and close is not None:
                close(event)
