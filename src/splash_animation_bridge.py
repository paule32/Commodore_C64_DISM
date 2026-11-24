# -*- coding: utf-8 -*-
"""Stage 692: independent Qt event loop for animated loading indicators.

A QMovie in the main GUI cannot advance while a synchronous GUI operation or
module import blocks that GUI thread.  This bridge maintains an optional,
lightweight Qt helper *process*, never a QApplication in a secondary thread.
The helper exits on stdin EOF, including unexpected parent termination.
"""
from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

_lock = threading.RLock()
_process: subprocess.Popen | None = None
_registered = False


def _worker_script() -> Path:
    return Path(__file__).resolve().parent / 'examples' / 'splash_animation_worker.py'


def _ensure_worker(gif_path: str | Path) -> bool:
    global _process, _registered
    path = Path(gif_path).expanduser().resolve()
    if not path.is_file():
        return False
    with _lock:
        if _process is not None and _process.poll() is None:
            return True
        _process = None
        # For frozen EXEs sys.executable isn't a Python interpreter.
        # Keep the original in-process QMovie as a safe fallback.
        if getattr(sys, 'frozen', False) or not _worker_script().is_file():
            return False
        try:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            _process = subprocess.Popen(
                [sys.executable, '-u', str(_worker_script()), '--gif', str(path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=(None if os.environ.get('D64_SPLASH_DEBUG') == '1'
                        else subprocess.DEVNULL),
                creationflags=flags,
                cwd=str(Path(__file__).resolve().parent),
            )
            if not _registered:
                atexit.register(close_splash_bridge)
                _registered = True
            return _process.poll() is None
        except (OSError, ValueError):
            _process = None
            return False


def _send(message: dict) -> bool:
    global _process
    with _lock:
        proc = _process
        if proc is None or proc.poll() is not None or proc.stdin is None:
            return False
        try:
            proc.stdin.write((json.dumps(message, ensure_ascii=True) + '\n').encode('ascii'))
            proc.stdin.flush()
            return True
        except (OSError, ValueError, BrokenPipeError):
            return False


def _wait_until_ready(timeout: float = 2.0) -> bool:
    """Fail over to the old splash if the helper cannot initialize Qt/GIF.

    Read from stdout on a daemon thread: select() does not work for pipes on
    Windows.  The child's only stdout line is its initialization handshake.
    """
    proc = _process
    if proc is None or proc.stdout is None:
        return False
    result = []
    def read_one_line():
        try:
            result.append(proc.stdout.readline())
        except (OSError, ValueError):
            result.append(b'')
    thread = threading.Thread(target=read_one_line, daemon=True)
    thread.start()
    thread.join(timeout)
    return bool(result and result[0] == b'READY\n' and proc.poll() is None)


def start_startup_splash(gif_path: str | Path) -> bool:
    """Show the complete startup screen in a process free to animate."""
    if not _ensure_worker(gif_path):
        return False
    if not _wait_until_ready():
        close_splash_bridge()
        return False
    return _send({'command': 'startup'})


def finish_startup_splash() -> None:
    _send({'command': 'hide_startup'})


def show_preloader_overlay(gif_path: str | Path, x: int, y: int,
                           width: int = 30, height: int = 30) -> bool:
    """Show a transparent non-activating animated overlay over a GUI splash."""
    if not _ensure_worker(gif_path):
        return False
    return _send({'command': 'overlay', 'x': int(x), 'y': int(y),
                  'width': max(1, int(width)), 'height': max(1, int(height))})


def hide_preloader_overlay() -> None:
    _send({'command': 'hide_overlay'})


def close_splash_bridge() -> None:
    """Closing stdin lets the helper shut down cleanly even on app exit."""
    global _process
    with _lock:
        proc, _process = _process, None
        if proc is None:
            return
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            proc.wait(timeout=1.5)
        except (OSError, subprocess.TimeoutExpired):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except (OSError, subprocess.TimeoutExpired):
                    proc.kill()
