"""Compile-time dBASE procedure source files with Windows sharing semantics.

SET PROCEDURE is a *source import*, not a generated runtime file handle.
EXCLUSIVE opens for GENERIC_READ with dwShareMode=0; ADDITIVE uses
FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE.  Neither changes
file attributes or grants write access to the compiler itself.

Handles stay open throughout the complete (possibly nested) preprocessing
pass, and are closed in reverse order, including when compilation fails.
"""
from __future__ import annotations

from contextlib import ExitStack
import os
from pathlib import Path

FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004


def windows_share_mode(mode: str) -> int:
    kind = str(mode).casefold()
    if kind == 'exclusive':
        return 0
    if kind == 'additive':
        return FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
    raise ValueError(f'Ungueltiger SET PROCEDURE-Modus: {mode}')


def _open_windows_procedure(path: Path, mode: str):
    """CreateFileW(GENERIC_READ, sharing, OPEN_EXISTING) as a Python stream."""
    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel32.CreateFileW
    create.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    )
    create.restype = wintypes.HANDLE
    close = kernel32.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    handle = create(str(path), 0x80000000, windows_share_mode(mode), None,
                    3, 0x00000080, None)
    if handle == ctypes.c_void_p(-1).value:
        code = ctypes.get_last_error()
        raise OSError(code, ctypes.FormatError(code), str(path))
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | getattr(os, 'O_BINARY', 0))
    except BaseException:
        close(handle)
        raise
    # fdopen takes ownership of the CRT descriptor and underlying Win32 handle.
    try:
        return os.fdopen(fd, 'rb')
    except BaseException:
        os.close(fd)
        raise


class DBaseProcedureFileManager:
    """One compilation's source snapshots and live procedure read handles."""
    def __init__(self) -> None:
        self._stack = ExitStack()
        self._cache: dict[Path, bytes] = {}
        self._opened: dict[Path, str] = {}
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._closed = True
        return self._stack.__exit__(exc_type, exc, tb)

    def has_snapshot(self, path: Path) -> bool:
        return Path(path).resolve() in self._cache

    def read(self, path: Path, *, mode: str = 'include') -> bytes:
        if self._closed:
            raise RuntimeError('Der SET PROCEDURE-Dateimanager ist bereits geschlossen')
        path = Path(path).resolve()
        kind = str(mode).casefold()
        if kind == 'include':
            if path not in self._cache:
                self._cache[path] = path.read_bytes()
            return self._cache[path]
        windows_share_mode(kind)  # Validate even on non-Windows platforms.
        previous = self._opened.get(path)
        if previous is not None:
            if previous != kind:
                raise OSError(f'{path}: SET PROCEDURE bereits als {previous.upper()} '
                              f'geoeffnet; Wechsel auf {kind.upper()} nicht moeglich')
            return self._cache[path]
        # On Windows this is an actual mandatory kernel sharing contract.
        # On other OSes read-only opening works, but Windows sharing cannot
        # be emulated using portable file descriptors.
        stream = (_open_windows_procedure(path, kind) if os.name == 'nt'
                  else path.open('rb'))
        self._stack.enter_context(stream)
        self._opened[path] = kind
        try:
            data = stream.read()
        except BaseException:
            # ExitStack will close the stream when this compilation exits.
            raise
        if path not in self._cache:
            self._cache[path] = data
        return self._cache[path]
