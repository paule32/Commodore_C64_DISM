"""Software-Installer-Dialoge: Stage 558 (Projektstart und sieben Wizard-Seiten).

Fuer den schwarz-weissen Titelverlauf wird bei Projektstart und Wizard ein
Qt-eigener, verschiebbarer Titelbalken eingesetzt. Eine native Windows-
Titelleiste bietet keinen frei definierbaren horizontalen Farbverlauf.
Andere Dialoge nutzen weiterhin die native DWM-Dark-Mode-Unterstuetzung.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QLinearGradient
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QRadioButton, QCheckBox, QStyle, QVBoxLayout,
    QColorDialog, QWidget, QTreeWidget, QTreeWidgetItem,
)
from software_installer_model import InstallerProject, InstallerProjectRegistry
from installer_wizard_options import (
    WINDOWS_LANGUAGES, DEFAULT_LANGUAGES, DEFAULT_LANGUAGE,
    WINDOWS_VERSION_TREE, DEFAULT_WINDOWS_VERSIONS, windows_leaf_ids,
    decode_selection, encode_selection, normalized_default_language,
)


WIZARD_SIZE = (780, 620)  # Identische Geometrie fuer alle sieben Wizard-Seiten.
GENERAL_FIELDS = (
    ("company", "Wie heißt Ihre Firma", "Ihre Firma"),
    ("product", "Produktname oder Titel", "Ihr Produkt"),
    ("version", "Produkt Version", "1.0"),
    ("website", "Firmen Internetseite", "https://www.firma.de"),
)


def _set_windows_dark_titlebar(dialog: QDialog, dark: bool) -> None:
    """Native Titelleiste fuer Dialoge *ohne* eigenen Gradientenbalken."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        value = ctypes.c_int(int(bool(dark)))
        handle = int(dialog.winId())
        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(handle), ctypes.c_uint(attribute),
                ctypes.byref(value), ctypes.sizeof(value))
            if result == 0:
                break
    except (AttributeError, OSError, ValueError):
        pass


class InstallerGradientTitleBar(QFrame):
    """Frameless-Dialogtitel mit echtem Qt-Farbverlauf und Fensterbewegung."""

    def __init__(self, dialog):
        super().__init__(dialog)
        self.setObjectName("installerGradientTitleBar")
        self.setFixedHeight(38)
        self._drag_offset = None
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 2, 6, 2)
        self.caption = QLabel(dialog.windowTitle(), self)
        self.caption.setObjectName("installerGradientTitleText")
        dialog.windowTitleChanged.connect(self.caption.setText)
        self.caption.installEventFilter(self)  # Auch Ziehen direkt am Titel erlauben.
        row.addWidget(self.caption, 1)
        self.close_button = QPushButton("×", self)
        self.close_button.setObjectName("installerGradientTitleClose")
        self.close_button.setFixedSize(30, 28)
        self.close_button.setToolTip("Dialog schließen")
        self.close_button.clicked.connect(dialog.reject)
        row.addWidget(self.close_button)

    def eventFilter(self, obj, event):
        if obj is self.caption:
            if event.type() == QEvent.MouseButtonPress:
                self.mousePressEvent(event)
                return True
            if event.type() == QEvent.MouseMove:
                self.mouseMoveEvent(event)
                return True
            if event.type() == QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self.window().frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and (event.buttons() & Qt.LeftButton):
            self.window().move(event.globalPos() - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class InstallerThemedDialog(QDialog):
    def __init__(self, parent=None, *, dark_mode=False, gradient_title=False):
        super().__init__(parent)
        self._dark_mode = bool(dark_mode)
        self._gradient_title = bool(gradient_title)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        if gradient_title:
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.apply_theme(self._dark_mode)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._gradient_title:
            _set_windows_dark_titlebar(self, self._dark_mode)

    def _content_layout(self):
        """Ein gemeinsamer Titelbalken und ein separates Inhalts-Widget."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)
        if self._gradient_title:
            self.gradient_title_bar = InstallerGradientTitleBar(self)
            outer.addWidget(self.gradient_title_bar)
        body = QWidget(self)
        body.setObjectName("installerDialogBody")
        outer.addWidget(body, 1)
        content = QVBoxLayout(body)
        content.setContentsMargins(18, 16, 18, 16)
        content.setSpacing(10)
        return content

    def apply_theme(self, dark: bool):
        self._dark_mode = bool(dark)
        bg, panel, fg, border, highlight, selection = (
            ("#202329", "#2b3039", "#f1f2f4", "#515b6c", "#3d4c62", "#465b77")
            if dark else
            ("#f5f5f5", "#ffffff", "#20242b", "#bcc5d1", "#dbe7f6", "#d7e6fb")
        )
        # Die Titelleiste bleibt im Dark Mode exakt schwarz -> weiss.
        title_gradient = ("stop:0 #000000, stop:1 #ffffff" if dark else
                          "stop:0 #343943, stop:1 #ffffff")
        self.setStyleSheet(f"""
            QDialog {{ background: {bg}; color: {fg}; border: 1px solid {border}; }}
            QWidget#installerDialogBody {{ background: {bg}; color: {fg}; }}
            QLabel, QRadioButton, QCheckBox {{ color: {fg}; background: transparent; }}
            QLineEdit, QListWidget, QComboBox {{ background: {panel}; color: {fg};
                border: 1px solid {border}; border-radius: 3px; padding: 5px;
                selection-background-color: {selection}; }}
            QComboBox QAbstractItemView {{ background: {panel}; color: {fg};
                selection-background-color: {selection}; }}
            QGroupBox {{ color: {fg}; border: 1px solid {border}; border-radius: 4px;
                margin-top: 13px; padding-top: 8px; font-weight: bold; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
            QPushButton {{ background: {panel}; color: {fg}; border: 1px solid {border};
                border-radius: 4px; min-height: 27px; padding: 4px 12px; }}
            QPushButton:hover {{ background: {highlight}; }}
            QPushButton:disabled {{ color: {border}; background: {bg}; }}
            QListWidget::item:selected {{ background: {selection}; color: {fg}; }}
            QFrame#installerDialogSeparator {{ background: {border}; max-height: 1px;
                min-height: 1px; border: none; }}
            QFrame#installerGradientTitleBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {title_gradient});
                border: none; }}
            QLabel#installerGradientTitleText {{ color: white; font-weight: bold;
                background: transparent; border: none; }}
            QPushButton#installerGradientTitleClose {{ color: black; background: transparent;
                border: none; font-size: 20px; padding: 0; min-height: 0; }}
            QPushButton#installerGradientTitleClose:hover {{ background: #e7c5c5; }}
            QLabel#installerWizardImage {{ background: qlineargradient(
                x1:0, y1:0, x2:0.85, y2:1, stop:0 {panel}, stop:1 {highlight});
                border: 1px solid {border}; border-radius: 4px; }}
            QFrame#installerThemePreview {{ background: {panel}; border: 1px solid {border};
                border-radius: 4px; }}
            QTreeWidget#installerWindowsTree {{ background: {panel}; color: {fg};
                border: 1px solid {border}; border-radius: 3px;
                alternate-background-color: {bg}; selection-background-color: {selection}; }}
        """)
        if self.isVisible() and not self._gradient_title:
            _set_windows_dark_titlebar(self, self._dark_mode)


def _line(parent):
    line = QFrame(parent)
    line.setObjectName("installerDialogSeparator")
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    return line


def _button_row(dialog, captions, actions, *, default_index=0):
    row = QHBoxLayout()
    row.addStretch(1)
    result = []
    for caption, callback in zip(captions, actions):
        button = QPushButton(caption, dialog)
        button.clicked.connect(callback)
        button.setDefault(len(result) == default_index)
        row.addWidget(button)
        result.append(button)
    return row, result


class InstallerProjectStartDialog(InstallerThemedDialog):
    """Projektliste mit Neuanlage oder Oeffnen und optionalem Wizard."""

    def __init__(self, registry: InstallerProjectRegistry, parent=None,
                 *, dark_mode=False, help_callback=None):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.registry = registry
        self.help_callback = help_callback
        self.selected_path = None
        self.setWindowTitle("Neues Projekt starten")
        self.resize(570, 480)
        layout = self._content_layout()

        self.new_radio = QRadioButton("Neues Projekt erstellen", self)
        self.new_radio.setObjectName("installerNewProjectRadio")
        self.new_radio.setChecked(True)
        layout.addWidget(self.new_radio)
        self.wizard_check = QCheckBox("start mit Wizard", self)
        self.wizard_check.setObjectName("installerWizardCheck")
        wizard_indent = QHBoxLayout()
        wizard_indent.addSpacing(24)
        wizard_indent.addWidget(self.wizard_check)
        wizard_indent.addStretch(1)
        layout.addLayout(wizard_indent)
        self.existing_radio = QRadioButton("Vorhandenes Projekt öffnen", self)
        self.existing_radio.setObjectName("installerExistingProjectRadio")
        layout.addWidget(self.existing_radio)

        self.projects_list = QListWidget(self)
        self.projects_list.setObjectName("installerProjectList")
        self.projects_list.itemDoubleClicked.connect(lambda _item: self._accept_choice())
        layout.addWidget(self.projects_list, 1)
        self.browse_button = QPushButton("Suchen", self)
        self.browse_button.setObjectName("installerProjectBrowseButton")
        self.browse_button.clicked.connect(self._browse)
        browse_row = QHBoxLayout()
        browse_row.addWidget(self.browse_button)
        browse_row.addStretch(1)  # Stage 556: Suchen links ausrichten.
        layout.addLayout(browse_row)
        layout.addWidget(_line(self))
        buttons, self.buttons = _button_row(
            self, ("OK", "Abbrechen", "Hilfe"),
            (self._accept_choice, self.reject, self._help), default_index=0)
        layout.addLayout(buttons)
        self.new_radio.toggled.connect(self._sync_mode)
        self.existing_radio.toggled.connect(self._sync_mode)
        self._load_projects()
        self._sync_mode()

    def _load_projects(self):
        try:
            entries = self.registry.available()
        except (OSError, ValueError, TypeError) as error:
            QMessageBox.warning(self, "Installer-Projekte", "Projektliste kann nicht gelesen werden:\n" + str(error))
            entries = []
        for entry in entries:
            self._add_project(entry.get("path", ""), entry.get("name", ""))

    def _add_project(self, path, name=""):
        path = str(Path(path).expanduser().resolve())
        for index in range(self.projects_list.count()):
            if str(self.projects_list.item(index).data(Qt.UserRole)).casefold() == path.casefold():
                self.projects_list.setCurrentRow(index)
                return
        item = QListWidgetItem(str(name or Path(path).stem), self.projects_list)
        item.setData(Qt.UserRole, path)
        item.setToolTip(path)

    def _sync_mode(self, _checked=None):
        is_existing = self.existing_radio.isChecked()
        self.projects_list.setEnabled(is_existing)
        self.browse_button.setEnabled(is_existing)
        self.wizard_check.setEnabled(not is_existing)

    def _browse(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Installer-Projekt suchen", str(self.registry.filename.parent),
            "Installer-Projekte (*.installer.json);;JSON-Dateien (*.json)")
        if not filename:
            return
        try:
            project = InstallerProject.load(filename)
        except (OSError, ValueError, TypeError, KeyError) as error:
            QMessageBox.warning(self, "Projektdatei", "Projektdatei ungültig:\n" + str(error))
            return
        self._add_project(filename, project.name)

    def _accept_choice(self):
        if self.existing_radio.isChecked():
            item = self.projects_list.currentItem()
            if item is None:
                QMessageBox.information(self, "Installer-Projekt", "Bitte ein Projekt aus der Liste wählen.")
                return
            self.selected_path = str(item.data(Qt.UserRole))
        self.accept()

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Neues Projekt starten")


class InstallerWizardDialog(InstallerThemedDialog):
    """Gleiche Seitengeometrie, 140px-Bildfeld und Navigation fuer alle Seiten."""

    BACK = 2

    def __init__(self, title, help_topic, parent=None, *, dark_mode=False,
                 help_callback=None, first_page=False, final_page=False):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle(title)
        self.help_callback = help_callback
        self.help_topic = help_topic
        self.setFixedSize(*WIZARD_SIZE)
        layout = self._content_layout()
        body = QHBoxLayout()
        body.setSpacing(18)
        self.image_box = QLabel(self)
        self.image_box.setObjectName("installerWizardImage")
        self.image_box.setFixedWidth(140)
        self.image_box.setAlignment(Qt.AlignCenter)
        self.image_box.setPixmap(self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(72, 72))
        body.addWidget(self.image_box, 0)
        self.fields_layout = QVBoxLayout()
        self.fields_layout.setSpacing(10)
        body.addLayout(self.fields_layout, 1)
        layout.addLayout(body, 1)
        layout.addSpacing(20)  # Bildbox endet ca. 20 px vor der Trennlinie.
        layout.addWidget(_line(self))
        row, self.buttons = _button_row(
            self, ("< Zurück", "Fertigstellen" if final_page else "Weiter >",
                   "Abbrechen", "Hilfe"),
            (lambda: self.done(self.BACK), self.accept, self.reject, self._help),
            default_index=1)
        self.back_button, self.next_button, self.cancel_button, self.help_button = self.buttons
        self.back_button.setEnabled(not first_page)
        layout.addLayout(row)

    def _help(self):
        if callable(self.help_callback):
            self.help_callback(self.help_topic)


class InstallerGeneralInfoDialog(InstallerWizardDialog):
    """Wizard-Seite 1: leere Felder ergeben die Platzhalter als Effektivwerte."""

    def __init__(self, parent=None, *, dark_mode=False, values=None, help_callback=None):
        super().__init__("Allgemeine Informationen", "Wizard Seite 1", parent,
                         dark_mode=dark_mode, help_callback=help_callback, first_page=True)
        self.setObjectName("installerGeneralInfoWizard")
        self.inputs = {}
        values = values or {}
        for key, title, placeholder in GENERAL_FIELDS:
            self.fields_layout.addWidget(QLabel(title, self))
            edit = QLineEdit(self)
            edit.setObjectName("installerWizard_" + key)
            edit.setPlaceholderText(placeholder)
            edit.setText(str(values.get(key, "")))
            self.fields_layout.addWidget(edit)
            self.inputs[key] = edit
        self.fields_layout.addStretch(1)

    def values(self):
        return {key: edit.text().strip() or edit.placeholderText()
                for key, edit in self.inputs.items()}


class InstallerPlatformDialog(InstallerWizardDialog):
    """Wizard-Seite 2: Wahl zwischen 32-Bit- und 64-Bit-Setup."""

    def __init__(self, parent=None, *, dark_mode=False, values=None, help_callback=None):
        super().__init__("Platform", "Wizard Seite 2", parent,
                         dark_mode=dark_mode, help_callback=help_callback)
        self.setObjectName("installerPlatformWizard")
        values = values or {}
        label = QLabel("Bitte wählen Sie Ihre Platform aus.", self)
        self.fields_layout.addWidget(label)
        self.fields_layout.addSpacing(20)
        info = QLabel(
            "Wählen Sie 32-Bit, wenn Sie ein 32-Bit Anwendungs-Setup erstellen möchten\n"
            "Wählen Sie 64-Bit, wenn Sie ein 64-Bit Anwendungs-Setup erstellen möchten.", self)
        info.setWordWrap(True)
        self.fields_layout.addWidget(info)
        self.fields_layout.addSpacing(20)
        self.radio_32 = QRadioButton("32 - Bit Setup", self)
        self.radio_64 = QRadioButton("64 - Bit Setup", self)
        self.radio_32.setObjectName("installerPlatform32Radio")
        self.radio_64.setObjectName("installerPlatform64Radio")
        self.fields_layout.addWidget(self.radio_32)
        self.fields_layout.addWidget(self.radio_64)
        self.radio_64.setChecked(str(values.get("platform", "32")) == "64")
        self.radio_32.setChecked(not self.radio_64.isChecked())
        self.fields_layout.addStretch(1)

    def values(self):
        return {"platform": "64" if self.radio_64.isChecked() else "32"}


class InstallerSourcesDialog(InstallerWizardDialog):
    """Wizard-Seite 3: Quellenverzeichnis und Unterverzeichnisse."""

    def __init__(self, parent=None, *, dark_mode=False, values=None, help_callback=None):
        super().__init__("Quelldateien", "Wizard Seite 3", parent,
                         dark_mode=dark_mode, help_callback=help_callback)
        self.setObjectName("installerSourcesWizard")
        values = values or {}
        description = QLabel(
            "Bitte geben sie den Ort der Quelldateien an.\n"
            "(Die Dateien die Sie installieren wollen.)", self)
        description.setWordWrap(True)
        self.fields_layout.addWidget(description)
        self.fields_layout.addSpacing(40)
        self.fields_layout.addWidget(QLabel("Pfad des Verzeichnisses", self))
        row = QHBoxLayout()
        self.directory_edit = QLineEdit(self)
        self.directory_edit.setObjectName("installerSourceDirectory")
        self.directory_edit.setText(str(values.get("source_directory", "")))
        self.directory_edit.setPlaceholderText("Quellverzeichnis auswählen")
        row.addWidget(self.directory_edit, 1)
        self.browse_button = QPushButton("Wählen", self)
        self.browse_button.setObjectName("installerSourceBrowseButton")
        self.browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.browse_button.clicked.connect(self._browse)
        row.addWidget(self.browse_button)
        self.fields_layout.addLayout(row)
        self.include_check = QCheckBox("Einbeziehung der Unterverzeichnisse", self)
        self.include_check.setObjectName("installerIncludeSubdirectories")
        self.include_check.setChecked(str(values.get("include_subdirectories", "false")).lower()
                                      in ("true", "1", "yes", "on"))
        self.fields_layout.addWidget(self.include_check)
        self.fields_layout.addStretch(1)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(
            self, "Quelldateien auswählen", self.directory_edit.text() or str(Path.home()))
        if path:
            self.directory_edit.setText(path)

    def values(self):
        return {"source_directory": self.directory_edit.text().strip(),
                "include_subdirectories": "true" if self.include_check.isChecked() else "false"}


class InstallerColorLineEdit(QLineEdit):
    """Doppelklick auf den Textbereich oeffnet die native Farbauswahl."""

    def mouseDoubleClickEvent(self, event):
        combo = self.parentWidget()
        while combo is not None and not isinstance(combo, InstallerColorComboBox):
            combo = combo.parentWidget()
        if combo is not None:
            combo.choose_custom_color()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class InstallerColorComboBox(QComboBox):
    """Farbliste mit frei waehlbaren Farben (Select Color via Doppelklick)."""

    DEFAULT_COLORS = (
        ("Schwarz", "#000000"), ("Weiß", "#ffffff"),
        ("Rot", "#ff0000"), ("Grün", "#008000"),
        ("Blau", "#0000ff"), ("Grau", "#808080"),
        ("Dunkelblau", "#20385f"), ("Hellblau", "#c0dfff"),
    )

    def __init__(self, parent=None, *, color="#20385f"):
        super().__init__(parent)
        self.setObjectName("installerColorCombo")
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setLineEdit(InstallerColorLineEdit(self))
        self.lineEdit().setToolTip("Farbe wählen oder doppelklicken für Select Color")
        self.lineEdit().editingFinished.connect(self._normalize_color)
        for title, hex_color in self.DEFAULT_COLORS:
            self.addItem(self._icon(hex_color), f"{title} ({hex_color})", hex_color)
        self.set_color(color)

    @staticmethod
    def _icon(hex_color):
        pixmap = QPixmap(18, 15)
        pixmap.fill(QColor(hex_color))
        return QIcon(pixmap)

    def set_color(self, color):
        parsed = QColor(str(color))
        normalized = parsed.name() if parsed.isValid() else "#20385f"
        for index in range(self.count()):
            if self.itemData(index) == normalized:
                self.setCurrentIndex(index)
                self.lineEdit().setText(normalized)
                return
        self.addItem(self._icon(normalized), f"Eigene Farbe ({normalized})", normalized)
        self.setCurrentIndex(self.count() - 1)
        self.lineEdit().setText(normalized)

    def color(self):
        color = QColor(self.lineEdit().text().strip())
        if color.isValid():
            return color.name()
        index_color = QColor(str(self.currentData() or ""))
        return index_color.name() if index_color.isValid() else "#20385f"

    def _normalize_color(self):
        self.set_color(self.color())

    def choose_custom_color(self):
        # Standard-QColorDialog benutzt unter Windows die native Select-Color-UI.
        selected = QColorDialog.getColor(QColor(self.color()), self, "Select Color")
        if selected.isValid():
            self.set_color(selected.name())


class InstallerThemePreview(QFrame):
    """Nicht-interaktive Vorschau der Theme-Auswahl."""

    def __init__(self, parent=None, *, theme_name="Standard 1"):
        super().__init__(parent)
        self.setObjectName("installerThemePreview")
        self.setMinimumHeight(320)
        self._theme_name = str(theme_name or "Standard 1")

    def set_theme(self, theme_name):
        self._theme_name = str(theme_name or "Standard 1")
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        outer = self.rect().adjusted(8, 8, -8, -8)
        painter.fillRect(outer, QColor("#dfe5ef"))

        dialog_w = int(outer.width() * 0.82)
        dialog_h = int(outer.height() * 0.88)
        dialog_x = outer.x() + (outer.width() - dialog_w) // 2
        dialog_y = outer.y() + 12
        dialog_rect = outer.adjusted((outer.width() - dialog_w) // 2, 12,
                                     -((outer.width() - dialog_w) // 2),
                                     -(outer.height() - dialog_h - 12))
        border = QColor("#505050")
        line_color = QColor("#707070")
        black_text = QColor("#101010")
        white_text = QColor("#ffffff")
        blue = QColor("#2f72d6")
        light_blue = QColor("#88b7ff")
        white = QColor("#ffffff")

        painter.setPen(QPen(border, 1))
        painter.setBrush(white)
        painter.drawRoundedRect(dialog_rect, 4, 4)

        top_h = max(44, dialog_rect.height() // 5)
        bottom_h = top_h
        center_h = dialog_rect.height() - top_h - bottom_h

        top_rect = dialog_rect.adjusted(0, 0, 0, -(dialog_rect.height() - top_h))
        center_rect = dialog_rect.adjusted(0, top_h, 0, -bottom_h)
        bottom_rect = dialog_rect.adjusted(0, dialog_rect.height() - bottom_h, 0, 0)

        def draw_standard1():
            grad = QLinearGradient(top_rect.topLeft(), top_rect.bottomLeft())
            grad.setColorAt(0.0, white)
            grad.setColorAt(1.0, light_blue)
            painter.fillRect(top_rect, grad)
            painter.fillRect(center_rect, white)
            painter.fillRect(bottom_rect, white)
            painter.setPen(QPen(line_color, 1))
            painter.drawLine(top_rect.bottomLeft(), top_rect.bottomRight())
            painter.drawLine(bottom_rect.topLeft(), bottom_rect.topRight())
            painter.setPen(QPen(black_text, 1))
            painter.drawText(center_rect.adjusted(0, 36, 0, 0), Qt.AlignHCenter, "Verknüpfung")
            combo = center_rect.adjusted(40, 62, -40, -(center_rect.height() - 88))
            painter.setBrush(QColor("#f3f6fb"))
            painter.setPen(QPen(border, 1))
            painter.drawRoundedRect(combo, 3, 3)
            painter.setPen(QPen(black_text, 1))
            painter.drawText(combo.adjusted(10, 0, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, "Ihr Produkt")
            rb1_y = combo.bottom() + 22
            for idx, text in enumerate((
                "Für jeden Windows-Benutzer Installieren",
                "Für den aktuellen Windows-Benutzer installieren")):
                cy = rb1_y + idx * 26
                painter.setPen(QPen(border, 1))
                painter.setBrush(QColor("#ffffff"))
                painter.drawEllipse(center_rect.left() + 40, cy, 12, 12)
                painter.setPen(QPen(black_text, 1))
                painter.drawText(center_rect.left() + 60, cy - 2, center_rect.width() - 80, 16,
                                 Qt.AlignLeft | Qt.AlignVCenter, text)
            btn_y = bottom_rect.y() + (bottom_rect.height() - 24) // 2
            x = bottom_rect.right() - 236
            for caption, width in (("< Zurück", 68), ("Weiter >", 68), ("Abbrechen", 78)):
                rect = type(bottom_rect)(x, btn_y, width, 24)
                painter.setPen(QPen(border, 1))
                painter.setBrush(QColor("#eef2f8"))
                painter.drawRoundedRect(rect, 3, 3)
                painter.setPen(QPen(black_text, 1))
                painter.drawText(rect, Qt.AlignCenter, caption)
                x += width + 10

        def draw_standard2():
            painter.fillRect(top_rect, white)
            painter.fillRect(bottom_rect, white)
            painter.fillRect(center_rect, blue)
            band_h = max(10, top_rect.height() // 3)
            top_band = top_rect.adjusted(0, 0, 0, -(top_rect.height() - band_h))
            bottom_band = bottom_rect.adjusted(0, 0, 0, -(bottom_rect.height() - band_h))
            grad1 = QLinearGradient(top_band.topLeft(), top_band.bottomLeft())
            grad1.setColorAt(0.0, blue)
            grad1.setColorAt(1.0, white)
            grad2 = QLinearGradient(bottom_band.topLeft(), bottom_band.bottomLeft())
            grad2.setColorAt(0.0, blue)
            grad2.setColorAt(1.0, white)
            painter.fillRect(top_band, grad1)
            painter.fillRect(bottom_band, grad2)
            painter.setPen(QPen(line_color, 1))
            painter.drawLine(top_rect.bottomLeft(), top_rect.bottomRight())
            painter.drawLine(bottom_rect.topLeft(), bottom_rect.topRight())
            painter.setPen(QPen(white_text, 1))
            painter.drawText(center_rect.adjusted(0, 36, 0, 0), Qt.AlignHCenter, "Verknüpfung")
            combo = center_rect.adjusted(40, 62, -40, -(center_rect.height() - 88))
            painter.setBrush(QColor("#1f5ebc"))
            painter.setPen(QPen(QColor("#d8e4ff"), 1))
            painter.drawRoundedRect(combo, 3, 3)
            painter.setPen(QPen(white_text, 1))
            painter.drawText(combo.adjusted(10, 0, -10, 0), Qt.AlignVCenter | Qt.AlignLeft, "Ihr Produkt")
            rb1_y = combo.bottom() + 22
            for idx, text in enumerate((
                "Für jeden Windows-Benutzer Installieren",
                "Für den aktuellen Windows-Benutzer installieren")):
                cy = rb1_y + idx * 26
                painter.setPen(QPen(QColor("#d8e4ff"), 1))
                painter.setBrush(QColor("#2b67c7"))
                painter.drawEllipse(center_rect.left() + 40, cy, 12, 12)
                painter.setPen(QPen(white_text, 1))
                painter.drawText(center_rect.left() + 60, cy - 2, center_rect.width() - 80, 16,
                                 Qt.AlignLeft | Qt.AlignVCenter, text)
            btn_y = bottom_rect.y() + (bottom_rect.height() - 24) // 2
            x = bottom_rect.right() - 236
            for caption, width in (("< Zurück", 68), ("Weiter >", 68), ("Abbrechen", 78)):
                rect = type(bottom_rect)(x, btn_y, width, 24)
                painter.setPen(QPen(border, 1))
                painter.setBrush(QColor("#eef2f8"))
                painter.drawRoundedRect(rect, 3, 3)
                painter.setPen(QPen(black_text, 1))
                painter.drawText(rect, Qt.AlignCenter, caption)
                x += width + 10

        if self._theme_name == "Standard 2":
            draw_standard2()
        else:
            draw_standard1()
        painter.end()


class InstallerAppearanceDialog(InstallerWizardDialog):
    """Wizard-Seite 4: Wizard-Typ, Hintergrundfarbe, Verlauf oder Bild."""

    def __init__(self, parent=None, *, dark_mode=False, values=None, help_callback=None):
        super().__init__("Fenster Einstellungen", "Wizard Seite 4", parent,
                         dark_mode=dark_mode, help_callback=help_callback)
        self.setObjectName("installerAppearanceWizard")
        values = values or {}
        self.fields_layout.addWidget(QLabel(
            "Wählen Sie das Aussehen der Setup-Anwendung aus", self))
        self.window_radio_wizard = QRadioButton("Wizard", self)
        self.window_radio_background = QRadioButton("Wizard mit Hintergrund-Fenster", self)
        self.window_radio_wizard.setObjectName("installerWindowWizardRadio")
        self.window_radio_background.setObjectName("installerWindowBackgroundRadio")
        self.fields_layout.addWidget(self.window_radio_wizard)
        self.fields_layout.addWidget(self.window_radio_background)
        background = values.get("window_mode", "wizard") == "background"
        self.window_radio_background.setChecked(background)
        self.window_radio_wizard.setChecked(not background)

        self.appearance_group = QGroupBox("Aussehen: ", self)
        self.appearance_group.setObjectName("installerAppearanceGroup")
        grid = QGridLayout(self.appearance_group)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(9)
        self.static_radio = QRadioButton("Statische Farbe", self.appearance_group)
        self.gradient_radio = QRadioButton("Verlauf", self.appearance_group)
        self.image_radio = QRadioButton("Bild", self.appearance_group)
        self.static_radio.setObjectName("installerAppearanceStaticRadio")
        self.gradient_radio.setObjectName("installerAppearanceGradientRadio")
        self.image_radio.setObjectName("installerAppearanceImageRadio")
        grid.addWidget(self.static_radio, 0, 0)
        grid.addWidget(self.gradient_radio, 0, 1)
        self.static_color = InstallerColorComboBox(
            self.appearance_group, color=values.get("static_color", "#20385f"))
        self.static_color.setObjectName("installerStaticColor")
        grid.addWidget(self.static_color, 1, 0)
        gradient_row = QHBoxLayout()
        self.gradient_start = InstallerColorComboBox(
            self.appearance_group, color=values.get("gradient_start", "#20385f"))
        self.gradient_start.setObjectName("installerGradientStartColor")
        self.gradient_end = InstallerColorComboBox(
            self.appearance_group, color=values.get("gradient_end", "#ffffff"))
        self.gradient_end.setObjectName("installerGradientEndColor")
        gradient_row.addWidget(self.gradient_start)
        gradient_row.addWidget(self.gradient_end)
        grid.addLayout(gradient_row, 1, 1)
        grid.addWidget(self.image_radio, 2, 0)
        image_row = QHBoxLayout()
        self.image_edit = QLineEdit(self.appearance_group)
        self.image_edit.setObjectName("installerBackgroundImagePath")
        self.image_edit.setPlaceholderText("Pfad zur Hintergrundgrafik")
        self.image_edit.setText(str(values.get("background_image", "")))
        image_row.addWidget(self.image_edit, 1)
        self.image_browse = QPushButton("Wählen", self.appearance_group)
        self.image_browse.setObjectName("installerBackgroundImageBrowse")
        self.image_browse.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.image_browse.clicked.connect(self._browse_image)
        image_row.addWidget(self.image_browse)
        grid.addLayout(image_row, 3, 0, 1, 2)
        choice = str(values.get("appearance_style", "static"))
        if choice == "gradient":
            self.gradient_radio.setChecked(True)
        elif choice == "image":
            self.image_radio.setChecked(True)
        else:
            self.static_radio.setChecked(True)
        for radio in (self.static_radio, self.gradient_radio, self.image_radio):
            radio.toggled.connect(self._sync_style)
        self._sync_style()
        self.fields_layout.addWidget(self.appearance_group)
        self.fields_layout.addStretch(1)

    def _sync_style(self, _checked=None):
        self.static_color.setEnabled(self.static_radio.isChecked())
        self.gradient_start.setEnabled(self.gradient_radio.isChecked())
        self.gradient_end.setEnabled(self.gradient_radio.isChecked())
        self.image_edit.setEnabled(self.image_radio.isChecked())
        self.image_browse.setEnabled(self.image_radio.isChecked())

    def _browse_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Hintergrundbild auswählen", self.image_edit.text() or str(Path.home()),
            "Bilddateien (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Alle Dateien (*)")
        if filename:
            self.image_edit.setText(filename)

    def values(self):
        return {
            "window_mode": "background" if self.window_radio_background.isChecked() else "wizard",
            "appearance_style": ("image" if self.image_radio.isChecked() else
                                 "gradient" if self.gradient_radio.isChecked() else "static"),
            "static_color": self.static_color.color(),
            "gradient_start": self.gradient_start.color(),
            "gradient_end": self.gradient_end.color(),
            "background_image": self.image_edit.text().strip(),
        }


class InstallerProjectThemeDialog(InstallerWizardDialog):
    """Wizard-Seite 5: Projekt-Theme mit nicht-interaktiver Vorschau."""

    def __init__(self, parent=None, *, dark_mode=False, values=None, help_callback=None):
        super().__init__("Projekt Theme", "Wizard Seite 5", parent,
                         dark_mode=dark_mode, help_callback=help_callback)
        self.setObjectName("installerProjectThemeWizard")
        values = values or {}
        self.fields_layout.addWidget(QLabel("Wählen Sie das Projekt-Theme aus", self))
        self.theme_combo = QComboBox(self)
        self.theme_combo.setObjectName("installerProjectThemeCombo")
        self.theme_combo.addItems(["Standard 1", "Standard 2"])
        current = str(values.get("project_theme", "Standard 1"))
        index = self.theme_combo.findText(current)
        self.theme_combo.setCurrentIndex(index if index >= 0 else 0)
        self.fields_layout.addWidget(self.theme_combo)
        self.preview = InstallerThemePreview(self, theme_name=self.theme_combo.currentText())
        self.preview.setObjectName("installerProjectThemePreview")
        self.fields_layout.addWidget(self.preview, 1)
        self.fields_layout.addStretch(1)
        self.theme_combo.currentTextChanged.connect(self.preview.set_theme)

    def values(self):
        return {"project_theme": self.theme_combo.currentText().strip() or "Standard 1"}


class InstallerLanguagesDialog(InstallerWizardDialog):
    """Wizard-Seite 6: Sprach-CheckListBox und abhaengige Standardsprache."""

    def __init__(self, parent=None, *, dark_mode=False, values=None, help_callback=None):
        super().__init__("Sprachen", "Wizard Seite 6", parent,
                         dark_mode=dark_mode, help_callback=help_callback)
        self.setObjectName("installerLanguagesWizard")
        values = values or {}
        self.fields_layout.addWidget(QLabel(
            "Welche Sprache(n) möchten Sie unterstützen ?", self))

        self.languages_list = QListWidget(self)
        self.languages_list.setObjectName("installerLanguagesCheckList")
        self.languages_list.setAlternatingRowColors(True)
        self.languages_list.setMinimumHeight(260)
        available = [language for _label, language in WINDOWS_LANGUAGES]
        saved = set(decode_selection(values.get("languages"), available, DEFAULT_LANGUAGES))
        for display, code in WINDOWS_LANGUAGES:
            item = QListWidgetItem(display, self.languages_list)
            item.setData(Qt.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if code in saved else Qt.Unchecked)
        self.fields_layout.addWidget(self.languages_list, 1)

        self.fields_layout.addWidget(QLabel(
            "Welche Standard-Sprache soll genutzt werden ?", self))
        self.default_language_combo = QComboBox(self)
        self.default_language_combo.setObjectName("installerDefaultLanguageCombo")
        self.fields_layout.addWidget(self.default_language_combo)
        self.fields_layout.addStretch(1)
        self._preferred_default = str(values.get("default_language", DEFAULT_LANGUAGE))
        self._sync_default_languages()
        self.languages_list.itemChanged.connect(self._sync_default_languages)

    def _selected_languages(self):
        return [self.languages_list.item(i).data(Qt.UserRole)
                for i in range(self.languages_list.count())
                if self.languages_list.item(i).checkState() == Qt.Checked]

    def _sync_default_languages(self, _item=None):
        selected = self._selected_languages()
        current = self.default_language_combo.currentData()
        requested = (current if current in selected else self._preferred_default)
        default = normalized_default_language(selected, requested)
        self.default_language_combo.blockSignals(True)
        self.default_language_combo.clear()
        for i in range(self.languages_list.count()):
            item = self.languages_list.item(i)
            code = item.data(Qt.UserRole)
            if code in selected:
                self.default_language_combo.addItem(item.text(), code)
        index = self.default_language_combo.findData(default)
        if index >= 0:
            self.default_language_combo.setCurrentIndex(index)
        self.default_language_combo.setEnabled(bool(selected))
        self.default_language_combo.blockSignals(False)
        self._preferred_default = default

    def accept(self):
        if not self._selected_languages():
            QMessageBox.warning(self, "Sprachen", "Bitte wählen Sie mindestens eine Sprache aus.")
            return
        super().accept()

    def values(self):
        selected = self._selected_languages()
        default = normalized_default_language(selected, self.default_language_combo.currentData())
        return {"languages": encode_selection(selected), "default_language": default}


class InstallerRequirementsDialog(InstallerWizardDialog):
    """Wizard-Seite 7: Installationsoptionen und Windows-Versions-TreeList."""

    def __init__(self, parent=None, *, dark_mode=False, values=None, help_callback=None):
        super().__init__("System Anforderungen", "Wizard Seite 7", parent,
                         dark_mode=dark_mode, help_callback=help_callback, final_page=True)
        self.setObjectName("installerRequirementsWizard")
        values = values or {}
        self.uninstall_check = QCheckBox("Un-Install unterstützen", self)
        self.install_log_check = QCheckBox("Log-Datei während der Installation führen", self)
        self.warn_admin_check = QCheckBox(
            "Benutzer warnen, wenn Administrator-Rechte erforderlich sind", self)
        for checkbox, key in (
            (self.uninstall_check, "support_uninstall"),
            (self.install_log_check, "installation_log"),
            (self.warn_admin_check, "warn_administrator"),
        ):
            checkbox.setObjectName("installer_" + key)
            checkbox.setChecked(str(values.get(key, "false")).casefold() in
                                ("true", "1", "yes", "on"))
            self.fields_layout.addWidget(checkbox)

        self.fields_layout.addSpacing(8)
        self.fields_layout.addWidget(QLabel(
            "Wählen Sie das/die gewünschte / erforderliche System", self))
        self.windows_tree = QTreeWidget(self)
        self.windows_tree.setObjectName("installerWindowsTree")
        self.windows_tree.setHeaderLabels(["Windows-Versionen"])
        self.windows_tree.setAlternatingRowColors(True)
        self.windows_tree.setMinimumHeight(300)
        self.windows_tree.setUniformRowHeights(True)
        self.fields_layout.addWidget(self.windows_tree, 1)
        self._updating_tree = False
        selected = set(decode_selection(
            values.get("windows_versions"), windows_leaf_ids(), DEFAULT_WINDOWS_VERSIONS))
        for node in WINDOWS_VERSION_TREE:
            self._append_node(None, node, selected)
        self.windows_tree.expandAll()
        self.windows_tree.itemChanged.connect(self._on_item_changed)

    def _append_node(self, parent, node, selected):
        code, caption, children = node
        item = (QTreeWidgetItem(self.windows_tree, [caption]) if parent is None
                else QTreeWidgetItem(parent, [caption]))
        item.setData(0, Qt.UserRole, code)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        if children:
            for child in children:
                self._append_node(item, child, selected)
            self._recompute_parent(item)
        else:
            item.setCheckState(0, Qt.Checked if code in selected else Qt.Unchecked)
        return item

    def _set_descendants(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._set_descendants(child, state)

    def _recompute_parent(self, parent):
        child_states = [parent.child(i).checkState(0) for i in range(parent.childCount())]
        if not child_states:
            return
        if all(state == Qt.Checked for state in child_states):
            parent.setCheckState(0, Qt.Checked)
        elif all(state == Qt.Unchecked for state in child_states):
            parent.setCheckState(0, Qt.Unchecked)
        else:
            parent.setCheckState(0, Qt.PartiallyChecked)

    def _on_item_changed(self, item, column):
        if self._updating_tree or column != 0:
            return
        self._updating_tree = True
        try:
            state = item.checkState(0)
            if state in (Qt.Checked, Qt.Unchecked):
                self._set_descendants(item, state)
            parent = item.parent()
            while parent is not None:
                self._recompute_parent(parent)
                parent = parent.parent()
        finally:
            self._updating_tree = False

    def _checked_leaves(self):
        result = []
        def visit(item):
            if item.childCount():
                for index in range(item.childCount()):
                    visit(item.child(index))
            elif item.checkState(0) == Qt.Checked:
                result.append(item.data(0, Qt.UserRole))
        for i in range(self.windows_tree.topLevelItemCount()):
            visit(self.windows_tree.topLevelItem(i))
        return result

    def accept(self):
        if not self._checked_leaves():
            QMessageBox.warning(self, "Windows-Versionen",
                                "Bitte wählen Sie mindestens eine Windows-Version aus.")
            return
        super().accept()

    def values(self):
        return {
            "support_uninstall": "true" if self.uninstall_check.isChecked() else "false",
            "installation_log": "true" if self.install_log_check.isChecked() else "false",
            "warn_administrator": "true" if self.warn_admin_check.isChecked() else "false",
            "windows_versions": encode_selection(self._checked_leaves()),
        }


class InstallerDestinationDialog(InstallerThemedDialog):
    """Legacy-Dialog fuer alte Aufrufer; Wizard-Seite 2 ist jetzt Platform."""

    BACK = 2

    def __init__(self, parent=None, *, dark_mode=False, destination="", help_callback=None):
        super().__init__(parent, dark_mode=dark_mode)
        self.setWindowTitle("Installationsverzeichnis")
        self.setObjectName("installerDestinationWizard")
        self.resize(550, 240)
        self.help_callback = help_callback
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.addWidget(QLabel("Installationsziel", self))
        self.destination_edit = QLineEdit(self)
        self.destination_edit.setPlaceholderText("C:\\Program Files\\Ihr Produkt")
        self.destination_edit.setText(destination)
        layout.addWidget(self.destination_edit)
        layout.addStretch(1)
        layout.addWidget(_line(self))
        row, self.buttons = _button_row(
            self, ("< Zurück", "Fertigstellen", "Abbrechen", "Hilfe"),
            (lambda: self.done(self.BACK), self.accept, self.reject, self._help),
            default_index=1)
        layout.addLayout(row)

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Wizard Seite 2")


class InstallerProjectNameDialog(InstallerThemedDialog):
    """Dark-Mode-faehiger Speichern-unter-Eingabedialog fuer den Projektnamen."""

    def __init__(self, parent=None, *, dark_mode=False, name="Unbenannt"):
        super().__init__(parent, dark_mode=dark_mode)
        self.setWindowTitle("Installer-Projekt speichern unter")
        self.setObjectName("installerProjectNameDialog")
        self.resize(440, 175)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.addWidget(QLabel("Projektname:", self))
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Name des Installer-Projektes")
        self.name_edit.setText(name)
        layout.addWidget(self.name_edit)
        layout.addStretch(1)
        layout.addWidget(_line(self))
        row, self.buttons = _button_row(
            self, ("Speichern", "Abbrechen"), (self.accept, self.reject))
        layout.addLayout(row)

    def name(self):
        return self.name_edit.text().strip()
