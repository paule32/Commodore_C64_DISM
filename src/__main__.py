# ---------------------------------------------------------------------------
# File:   __main__.py
# Author: (c) 2026 Jens Kallup - paule32
# Stage:  258
# Purpose: C64-Splash-Launcher fuer d64_dism.py
# ---------------------------------------------------------------------------
from __future__ import annotations

import ctypes
import sys
import time
try:
    from PyQt5.QtCore import QCoreApplication, Qt
    from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPixmap
    from PyQt5.QtWidgets import QApplication, QSplashScreen
except ImportError as exc:
    print(
        "PyQt5 ist nicht installiert.\n"
        "Installiere das Qt5-Paket mit:\n\n"
        "    py -m pip install PyQt5 PyQtWebEngine\n\n"
        f"Technischer Fehler: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(2)


def _load_splash_font() -> str:
    """
    Stage 258: Der Splash benutzt bewusst NICHT C64Pro.ttf.

    C64Pro.ttf wird von d64_dism.py genau einmal als Application-Font für
    PETSCII/Hex-Ansichten geladen. Ein zweites addApplicationFont() während
    des Splash-Starts kann unter dem Windows-Qt5-Fontengine zu
    "GetTextMetrics failed" führen. Für den Splash genügt eine stabile
    Monospace-Systemschrift; die eigentliche C64-Darstellung bleibt im
    Hauptprogramm unverändert.
    """
    return "Consolas" if sys.platform.startswith("win") else "Courier New"


def _make_c64_splash(font_family: str) -> QPixmap:
    """Zeichnet den Splash vollständig mit Qt; es wird kein Bildfile benötigt."""
    width, height = 720, 420
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(52, 73, 173))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.TextAntialiasing, True)

    border = QColor(120, 140, 235)
    screen = QColor(64, 81, 181)
    text = QColor(190, 198, 255)
    dark = QColor(25, 34, 92)

    painter.setPen(QPen(border, 10))
    painter.setBrush(screen)
    painter.drawRect(18, 18, width - 36, height - 36)

    painter.setPen(text)
    title_font = QFont(font_family, 24)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.drawText(
        42,
        66,
        width - 84,
        40,
        Qt.AlignHCenter | Qt.AlignVCenter,
        "**** COMMODORE C= 64 ****",
    )

    info_font = QFont(font_family, 16)
    info_font.setFixedPitch(True)
    painter.setFont(info_font)
    painter.drawText(62, 132, "64K RAM SYSTEM  38911 BASIC BYTES FREE")

    app_font = QFont(font_family, 34)
    app_font.setBold(True)
    app_font.setFixedPitch(True)
    painter.setFont(app_font)
    painter.drawText(
        40,
        172,
        width - 80,
        70,
        Qt.AlignHCenter | Qt.AlignVCenter,
        "C=64 Disassembler",
    )

    painter.setFont(info_font)
    painter.drawText(62, 284, "READY.")
    painter.drawText(62, 320, 'LOAD"D64_DISM.PY",8,1')

    painter.setPen(dark)
    painter.drawLine(62, 348, width - 62, 348)
    painter.setPen(text)
    small_font = QFont(font_family, 12)
    small_font.setFixedPitch(True)
    painter.setFont(small_font)
    painter.drawText(
        62,
        370,
        width - 124,
        28,
        Qt.AlignLeft | Qt.AlignVCenter,
        "LOADING WORKBENCH ...",
    )

    painter.end()
    return pixmap


def _focus_main_window(window) -> None:
    """Qt-Fokus plus Windows-SetForegroundWindow nach dem ersten show()."""
    try:
        window.show()
        window.raise_()
        window.activateWindow()
        window.setFocus(Qt.ActiveWindowFocusReason)
    except Exception:
        pass

    if sys.platform.startswith("win"):
        try:
            hwnd = int(window.winId())
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.SetFocus(hwnd)
        except Exception:
            pass

def weiter():
    pass

def main() -> int:
    # Stage 258: QtWebEngine verlangt AA_ShareOpenGLContexts, bevor die
    # QGuiApplication/QApplication konstruiert wird. Das Attribut hier im
    # Launcher zu setzen ist entscheidend, weil __main__.py die QApplication
    # bereits vor dem späteren Import von d64_dism.py erzeugt.
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("d64_dism Launcher")

    font_family = _load_splash_font()
    splash = QSplashScreen(
        _make_c64_splash(font_family),
        Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint,
    )
    splash.setObjectName("c64_startup_splash")
    splash.show()
    splash.raise_()
    time.sleep(1.5)
    app.processEvents()

    # d64_dism wird erst jetzt importiert. Sein ExplorerWindow wird beim
    # Konstruieren noch nicht gezeigt; der C64-Splash bleibt deshalb sichtbar.
    try:
        import d64_dism
    except BaseException:
        splash.close()
        raise

    def main_window_shown(window) -> None:
        # run_gui() hat zu diesem Zeitpunkt bereits winId() erzeugt und show()
        # ausgeführt. Erst jetzt verschwindet der Splash und der Fokus wechselt.
        try:
            splash.finish(window)
        finally:
            splash.close()
        app.processEvents()
        _focus_main_window(window)

    try:
        result = d64_dism.main(
            sys.argv[1:],
            application=app,
            window_shown_callback=main_window_shown,
        )
    finally:
        if splash.isVisible():
            splash.close()
    return int(result)


if __name__ == "__main__":
    raise SystemExit(main())
