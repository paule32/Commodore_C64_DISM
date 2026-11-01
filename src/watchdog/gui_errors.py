"""Early Python/Qt/Win32 exception diagnostics for Commodore_C64_DISM.

Imported by __main__.py before PyQt5. Works with pythonw.exe and does not
create a second console. Adapted to the same behavior as PythonBDE's guard.
"""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import sys
import tempfile
import threading
import traceback

_APP_NAME = "Commodore_C64_DISM"
_LOCK = threading.RLock()
_DIALOG_LOCK = threading.Lock()
_INSTALLED = False
_ORIGINAL_STDERR = None


def log_path() -> Path:
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.getenv("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return base / "Commodore_C64_DISM" / "d64_dism_errors.log"


def append_error_log(text: str) -> Path | None:
    with _LOCK:
        for path in (log_path(), Path(tempfile.gettempdir()) / "d64_dism_errors.log"):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.exists() and path.stat().st_size >= 5 * 1024 * 1024:
                    path.replace(path.with_suffix(".log.old"))
                with path.open("a", encoding="utf-8", errors="replace") as f:
                    f.write(str(text).rstrip("\n") + "\n")
                return path
            except (OSError, ValueError):
                pass
    return None


class _TeeStderr:
    def __init__(self, stream):
        self.original = stream
        self.encoding = "utf-8"
        self.errors = "replace"
        self._partial = ""
        self._lock = threading.RLock()

    def write(self, data):
        text = str(data)
        with self._lock:
            parts = (self._partial + text.replace("\r\n", "\n")).split("\n")
            self._partial = parts.pop()
            for part in parts:
                append_error_log(part)
            if len(self._partial) >= 8192:
                append_error_log(self._partial)
                self._partial = ""
            if self.original is not None:
                try:
                    self.original.write(text)
                except (OSError, ValueError):
                    pass
        return len(text)

    def flush(self):
        with self._lock:
            if self._partial:
                append_error_log(self._partial)
                self._partial = ""
            if self.original is not None:
                try:
                    self.original.flush()
                except (OSError, ValueError):
                    pass

    def isatty(self):
        return bool(self.original and getattr(self.original, "isatty", lambda: False)())

    def writable(self):
        return True


def _qt_dialog(title: str, details: str) -> bool:
    try:
        from PyQt5.QtCore import QThread
        from PyQt5.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout
        app = QApplication.instance()
        if app is None or app.thread() != QThread.currentThread():
            return False
        dlg = QDialog(app.activeWindow())
        dlg.resize(880, 560)
        dlg.setWindowTitle(f"{_APP_NAME}: {title}")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(title, dlg))
        edit = QPlainTextEdit(dlg)
        edit.setReadOnly(True)
        edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        edit.setPlainText(details)
        layout.addWidget(edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=dlg)
        copy = QPushButton("Copy Traceback", dlg)
        copy.clicked.connect(lambda: app.clipboard().setText(details))
        buttons.addButton(copy, QDialogButtonBox.ActionRole)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        dlg.exec_()
        return True
    except Exception:
        return False


def _native_editor(title: str, details: str) -> bool:
    """Create a native multiline read-only Win32 EDIT with Copy/Close."""
    if os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes as wt
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

        class WNDCLASS(ctypes.Structure):
            _fields_ = [("style", wt.UINT), ("lpfnWndProc", CALLBACK),
                        ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                        ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON),
                        ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH),
                        ("lpszMenuName", wt.LPCWSTR), ("lpszClassName", wt.LPCWSTR)]

        class MSG(ctypes.Structure):
            _fields_ = [("hwnd", wt.HWND), ("message", wt.UINT),
                        ("wParam", wt.WPARAM), ("lParam", wt.LPARAM),
                        ("time", wt.DWORD), ("pt", wt.POINT)]

        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
        user32.RegisterClassW.restype = wt.ATOM
        user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
                                          ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                          wt.HWND, wt.HMENU, wt.HINSTANCE, ctypes.c_void_p]
        user32.CreateWindowExW.restype = wt.HWND
        user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        user32.SendMessageW.restype = ctypes.c_ssize_t
        user32.MoveWindow.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_int,
                                      ctypes.c_int, ctypes.c_int, wt.BOOL]
        user32.DestroyWindow.argtypes = [wt.HWND]
        user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
        user32.UpdateWindow.argtypes = [wt.HWND]
        user32.SetWindowTextW.argtypes = [wt.HWND, wt.LPCWSTR]
        user32.UnregisterClassW.argtypes = [wt.LPCWSTR, wt.HINSTANCE]
        user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
        user32.PostQuitMessage.argtypes = [ctypes.c_int]
        user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wt.HWND, wt.UINT, wt.UINT]
        user32.GetMessageW.restype = ctypes.c_int
        kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wt.HMODULE
        hwnds = {"edit": None, "copy": None, "close": None}
        WM_SIZE, WM_COMMAND, WM_DESTROY = 5, 0x111, 2
        done = {"value": False}

        def wndproc(hwnd, message, wp, lp):
            if message == WM_SIZE:
                width, height = lp & 0xFFFF, (lp >> 16) & 0xFFFF
                if hwnds["edit"]:
                    user32.MoveWindow(hwnds["edit"], 12, 12, max(100, width-24), max(50, height-70), True)
                    user32.MoveWindow(hwnds["copy"], max(12, width-262), height-46, 140, 30, True)
                    user32.MoveWindow(hwnds["close"], max(155, width-112), height-46, 100, 30, True)
                return 0
            if message == WM_COMMAND:
                command = wp & 0xFFFF
                if command == 1001:
                    user32.SendMessageW(hwnds["edit"], 0xB1, 0, -1)  # EM_SETSEL all
                    user32.SendMessageW(hwnds["edit"], 0x301, 0, 0)  # WM_COPY
                    return 0
                if command == 1002:
                    user32.DestroyWindow(hwnd)
                    return 0
            if message == 0x10:  # WM_CLOSE
                user32.DestroyWindow(hwnd)
                return 0
            if message == WM_DESTROY:
                done["value"] = True
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, message, wp, lp)

        callback = CALLBACK(wndproc)
        instance = kernel32.GetModuleHandleW(None)
        class_name = f"D64Trace_{os.getpid()}_{threading.get_ident()}"
        wc = WNDCLASS()
        wc.lpfnWndProc = callback
        wc.hInstance = instance
        wc.lpszClassName = class_name
        wc.hbrBackground = wt.HBRUSH(6)
        if not user32.RegisterClassW(ctypes.byref(wc)):
            raise OSError("RegisterClassW failed")
        try:
            hwnd = user32.CreateWindowExW(0, class_name, f"{_APP_NAME} – {title}",
                                         0x10CF0000, 100, 100, 900, 590, None, None, instance, None)
            if not hwnd:
                raise OSError("CreateWindowExW failed")
            hwnds["edit"] = user32.CreateWindowExW(0x200, "EDIT", "",
                0x50000000 | 0x00300000 | 0x0004 | 0x0800 | 0x00C0,
                10, 10, 870, 500, hwnd, None, instance, None)
            hwnds["copy"] = user32.CreateWindowExW(0, "BUTTON", "Copy Traceback",
                0x50010000, 620, 515, 135, 30, hwnd, wt.HMENU(1001), instance, None)
            hwnds["close"] = user32.CreateWindowExW(0, "BUTTON", "Close",
                0x50010000, 765, 515, 100, 30, hwnd, wt.HMENU(1002), instance, None)
            if not all(hwnds.values()):
                user32.DestroyWindow(hwnd)
                raise OSError("Window controls could not be created")
            user32.SendMessageW(hwnds["edit"], 0xC5, 600000, 0)
            user32.SetWindowTextW(hwnds["edit"], details[-500000:].replace("\n", "\r\n"))
            user32.ShowWindow(hwnd, 5)
            user32.UpdateWindow(hwnd)
            msg = MSG()
            while not done["value"]:
                status = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if status <= 0:
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            return True
        finally:
            user32.UnregisterClassW(class_name, instance)
    except Exception:
        try:
            ctypes.windll.user32.MessageBoxW(None, details[-3500:], title, 0x10)
            return True
        except Exception:
            return False


def show_traceback(title: str, details: str) -> None:
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    text = f"{stamp} | {title}\n{details}"
    append_error_log(text)
    if not _DIALOG_LOCK.acquire(blocking=False):
        return
    try:
        if _qt_dialog(title, text) or _native_editor(title, text):
            return
        if _ORIGINAL_STDERR:
            _ORIGINAL_STDERR.write(text + "\n")
    finally:
        _DIALOG_LOCK.release()


def _exception_hook(kind, value, tb):
    if kind in (SystemExit, KeyboardInterrupt):
        return
    show_traceback("Unbehandelte Ausnahme", "".join(traceback.format_exception(kind, value, tb)))


def _thread_hook(args):
    _exception_hook(args.exc_type, args.exc_value, args.exc_traceback)


def _unraisable_hook(args):
    _exception_hook(args.exc_type or RuntimeError, args.exc_value or RuntimeError("unraisable"), args.exc_traceback)


def install_exception_handler(*, app_name="Commodore_C64_DISM", redirect_stderr=True) -> None:
    global _INSTALLED, _ORIGINAL_STDERR, _APP_NAME
    _APP_NAME = app_name
    if _INSTALLED:
        return
    _INSTALLED = True
    _ORIGINAL_STDERR = sys.stderr
    sys.excepthook = _exception_hook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_hook
    if hasattr(sys, "unraisablehook"):
        sys.unraisablehook = _unraisable_hook
    if redirect_stderr:
        sys.stderr = _TeeStderr(sys.stderr)
