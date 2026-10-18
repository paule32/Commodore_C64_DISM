# -*- coding: utf-8 -*-
"""Stage 437 – gerahmte und themenfaehige Dialoge fuer Hilfe -> Ueber.

Die Qt5-Informationen stammen aus den zur Laufzeit geladenen PyQt5/Qt5-Bibliotheken.
Die native QMessageBox.aboutQt kann weder die gewuenschte eigene Titelleiste
noch einen gleichmaessigen 3-Pixel-Rahmen garantieren. Deshalb werden beide
Menueeintraege ueber denselben frameless QDialog dargestellt.
"""
from __future__ import annotations

from PyQt5.QtCore import QPoint, Qt, QSize, PYQT_VERSION_STR, qVersion
from PyQt5.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QVBoxLayout, QWidget,
)


APP_ABOUT_LINES = (
    'C= 64  Disassembler',
    'Version 0.0.1',
    '(c) 2026 bei Jens Kallup - paule32',
    'Alle Rechte vorbehalten.',
    'Lizenziert durch die MIT Lizenz',
)


class D64AboutTitleBar(QWidget):
    """Eigene verschiebbare Schwarz-Grau-Titelleiste mit Schliessen-X."""

    def __init__(self, dialog, dark_mode: bool):
        super().__init__(dialog)
        self._dialog = dialog
        self._dark_mode = bool(dark_mode)
        self._drag_offset = None
        self.setObjectName('d64_about_titlebar')
        self.setFixedHeight(40)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 4, 2)
        row.setSpacing(3)
        self.title_label = QLabel(dialog.windowTitle(), self)
        self.title_label.setObjectName('d64_about_title')
        row.addWidget(self.title_label, 1)
        self.close_button = QToolButton(self)
        self.close_button.setObjectName('d64_about_close')
        self.close_button.setToolTip('Schließen')
        self.close_button.setFixedSize(36, 32)
        self.close_button.setIconSize(QSize(20, 20))
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.clicked.connect(dialog.reject)
        row.addWidget(self.close_button)
        dialog.windowTitleChanged.connect(self.title_label.setText)
        self.set_dark_mode(dark_mode)

    def _close_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor('#ffffff' if self._dark_mode else '#202530'),
                            2.3, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(6, 6, 18, 18)
        painter.drawLine(18, 6, 6, 18)
        painter.end()
        return QIcon(pixmap)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = bool(enabled)
        # Ein transparentes Widget-Stylesheet darf den QPainter-Verlauf
        # nicht durch eine gezeichnete Qt-Hintergrundflaeche verdecken.
        color = '#ffffff' if enabled else '#202530'
        self.title_label.setStyleSheet(
            f'color:{color};background:transparent;border:0;font-weight:600;'
        )
        self.close_button.setStyleSheet(
            'QToolButton#d64_about_close{background:transparent;border:0;}'
            'QToolButton#d64_about_close:hover{background:#ad3935;}'
        )
        self.close_button.setIcon(self._close_icon())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        if self._dark_mode:
            gradient.setColorAt(0.0, QColor('#000000'))
            gradient.setColorAt(1.0, QColor('#707070'))
        else:
            gradient.setColorAt(0.0, QColor('#cad0d8'))
            gradient.setColorAt(1.0, QColor('#eef0f4'))
        painter.fillRect(self.rect(), gradient)
        painter.end()
        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self._dialog.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self._dialog.move(event.globalPos() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class D64AboutDialog(QDialog):
    """Gemeinsames Erscheinungsbild fuer Anwendung und Qt5-Informationen."""

    def __init__(self, parent=None, *, about_qt: bool = False, dark_mode: bool = True):
        super().__init__(parent)
        self._dark_mode = bool(dark_mode)
        self._about_qt = bool(about_qt)
        self.setObjectName('d64_about_dialog')
        self.setWindowTitle('Über Qt5 ...' if about_qt else 'Über ...')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.resize(600 if about_qt else 530, 340 if about_qt else 316)
        self.setMinimumSize(470, 280)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.border_frame = QFrame(self)
        self.border_frame.setObjectName('d64_about_frame')
        outer.addWidget(self.border_frame)
        framed = QVBoxLayout(self.border_frame)
        framed.setContentsMargins(3, 3, 3, 3)
        framed.setSpacing(0)
        self.title_bar = D64AboutTitleBar(self, self._dark_mode)
        framed.addWidget(self.title_bar)

        content = QWidget(self.border_frame)
        content.setObjectName('d64_about_content')
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(22, 20, 22, 14)
        content_layout.setSpacing(7)
        self.labels = []
        if self._about_qt:
            self._create_qt_content(content, content_layout)
        else:
            self._create_application_content(content, content_layout)
        content_layout.addStretch(1)
        self.ok_button = QPushButton('OK', content)
        self.ok_button.setObjectName('d64_about_ok')
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)
        action_row = QHBoxLayout()
        action_row.addStretch(1)
        action_row.addWidget(self.ok_button)
        content_layout.addLayout(action_row)
        framed.addWidget(content, 1)
        self.set_dark_mode(self._dark_mode)

    def _add_text(self, parent, layout, value, role, font_size, bold=False):
        label = QLabel(value, parent)
        label.setObjectName('d64_about_' + role)
        label.setTextFormat(Qt.PlainText)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        font = QFont('Arial')
        font.setPixelSize(font_size)
        font.setBold(bold)
        label.setFont(font)
        layout.addWidget(label)
        self.labels.append((label, role))
        return label

    def _create_application_content(self, parent, layout):
        # Exakter Wortlaut; die Farben sind Eigenschaften, keine Text-Plaetzehalter.
        self._add_text(parent, layout, APP_ABOUT_LINES[0], 'app_title', 26, True)
        self._add_text(parent, layout, APP_ABOUT_LINES[1], 'version', 17, True)
        self._add_text(parent, layout, APP_ABOUT_LINES[2], 'copyright', 15)
        self._add_text(parent, layout, APP_ABOUT_LINES[3], 'rights', 15)
        layout.addSpacing(12)
        self._add_text(parent, layout, APP_ABOUT_LINES[4], 'license', 16)

    def _create_qt_content(self, parent, layout):
        self._add_text(parent, layout, 'Über Qt5', 'qt_title', 25, True)
        self._add_text(parent, layout, f'Diese Anwendung verwendet Qt {qVersion()}.',
                       'qt_version', 17)
        self._add_text(parent, layout, f'PyQt-Version: {PYQT_VERSION_STR}',
                       'pyqt_version', 16)
        self._add_text(parent, layout,
                       'Qt ist ein plattformübergreifendes Framework für grafische Benutzeroberflächen.',
                       'qt_description', 15)
        self._add_text(parent, layout,
                       'Qt und die zugehörigen Marken gehören ihren jeweiligen Rechteinhabern.',
                       'qt_copyright', 14)
        self._add_text(parent, layout, 'Weitere Informationen: www.qt.io',
                       'qt_website', 14)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = bool(enabled)
        background = '#202630' if enabled else '#f3f5f8'
        border = '#778391' if enabled else '#8996a5'
        foreground = '#ffffff' if enabled else '#202630'
        yellow = '#ffe15c' if enabled else '#806000'
        button_bg = '#343e4d' if enabled else '#e5eaf0'
        self.setStyleSheet(
            f'QFrame#d64_about_frame{{background:{background};border:3px solid {border};}}'
            f'QWidget#d64_about_content{{background:{background};border:0;}}'
            f'QPushButton#d64_about_ok{{background:{button_bg};color:{foreground};'
            f'border:1px solid {border};border-radius:3px;padding:5px 24px;min-width:74px;}}'
        )
        for label, role in self.labels:
            color = yellow if not self._about_qt and role != 'license' else foreground
            label.setStyleSheet(f'color:{color};background:transparent;border:0;')
        self.title_bar.set_dark_mode(enabled)
        self.update()
