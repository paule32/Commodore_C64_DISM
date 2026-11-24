# -*- coding: utf-8 -*-
"""Stage 692: private Qt5 splash renderer with its own event loop.

Launched only by splash_animation_bridge.py, never as an application window.
No other Qt widgets are created outside this process's GUI thread.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import queue
import sys
import threading

from PyQt5.QtCore import QCoreApplication, Qt, QSize, QTimer
from PyQt5.QtGui import QImageReader, QMovie
from PyQt5.QtWidgets import QApplication, QLabel, QSplashScreen


def _startup_pixmap():
    # Reuse the original C64 startup appearance without executing main().
    path = Path(__file__).with_name('__main__.py')
    spec = importlib.util.spec_from_file_location('_d64_splash_appearance', str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError('C64 splash style could not be loaded')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._make_c64_splash(module._load_splash_font())


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--gif', required=True)
    opts = parser.parse_args(argv)

    # Match the parent application's device-independent coordinates on HiDPI.
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)
    movie = QMovie(str(Path(opts.gif)))
    if os.environ.get('D64_SPLASH_DEBUG') == '1':
        reader = QImageReader(str(Path(opts.gif)))
        print(f'[Stage 692 preloader] {opts.gif}: '
              f'valid={movie.isValid()}, animated={reader.supportsAnimation()}, '
              f'frames={reader.imageCount()}', file=sys.stderr, flush=True)
    if not movie.isValid():
        return 2
    movie.setCacheMode(QMovie.CacheAll)
    movie.setScaledSize(QSize(32, 32))

    splash = None
    splash_loader = None
    overlay = QLabel()
    overlay.setObjectName('d64_independent_loader')
    overlay.setFixedSize(32, 32)
    overlay.setAlignment(Qt.AlignCenter)
    overlay.setAttribute(Qt.WA_ShowWithoutActivating, True)
    overlay.setAttribute(Qt.WA_TranslucentBackground, True)
    overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    if hasattr(Qt, 'WindowDoesNotAcceptFocus'):
        flags |= Qt.WindowDoesNotAcceptFocus
    if hasattr(Qt, 'WindowTransparentForInput'):
        flags |= Qt.WindowTransparentForInput
    overlay.setWindowFlags(flags)
    overlay.setMovie(movie)
    overlay.hide()

    messages = queue.Queue()

    def read_commands():
        try:
            for line in sys.stdin:
                try:
                    messages.put(json.loads(line))
                except (ValueError, TypeError):
                    continue
        finally:
            messages.put({'command': 'quit'})

    threading.Thread(target=read_commands, daemon=True).start()

    def ensure_startup():
        nonlocal splash, splash_loader
        if splash is None:
            splash = QSplashScreen(
                _startup_pixmap(), Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            splash.setObjectName('c64_startup_splash')
            splash_loader = QLabel(splash)
            splash_loader.setObjectName('c64_startup_loader')
            splash_loader.setFixedSize(34, 34)
            splash_loader.move(splash.width() - 54, 20)
            splash_loader.setAlignment(Qt.AlignCenter)
            splash_loader.setMovie(movie)
        overlay.hide()
        splash.show()
        splash_loader.show()
        splash.raise_()
        movie.start()

    def show_overlay(command):
        if splash is not None:
            splash.hide()
        overlay.resize(max(1, int(command['width'])), max(1, int(command['height'])))
        movie.setScaledSize(QSize(max(1, overlay.width()-2), max(1, overlay.height()-2)))
        overlay.move(int(command['x']), int(command['y']))
        overlay.show()
        movie.start()

    def poll():
        nonlocal splash
        for _ in range(50):
            try:
                command = messages.get_nowait()
            except queue.Empty:
                break
            action = command.get('command')
            if action == 'quit':
                app.quit()
                return
            if action == 'startup':
                ensure_startup()
            elif action == 'hide_startup':
                if splash is not None:
                    splash.hide()
                if not overlay.isVisible():
                    movie.stop()
            elif action == 'overlay':
                show_overlay(command)
            elif action == 'hide_overlay':
                overlay.hide()
                if splash is None or not splash.isVisible():
                    movie.stop()

    timer = QTimer()
    timer.timeout.connect(poll)
    timer.start(25)
    # Parent does not hide its fallback until Qt and the GIF are ready.
    sys.stdout.write('READY\n')
    sys.stdout.flush()
    return app.exec_()


if __name__ == '__main__':
    raise SystemExit(main())
