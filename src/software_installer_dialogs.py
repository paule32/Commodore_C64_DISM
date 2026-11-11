"""Software-Installer-Dialoge: Stage 558 (Projektstart und sieben Wizard-Seiten).

Fuer den schwarz-weissen Titelverlauf wird bei Projektstart und Wizard ein
Qt-eigener, verschiebbarer Titelbalken eingesetzt. Eine native Windows-
Titelleiste bietet keinen frei definierbaren horizontalen Farbverlauf.
Andere Dialoge nutzen weiterhin die native DWM-Dark-Mode-Unterstuetzung.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QEvent, QDate
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap, QLinearGradient, QKeySequence
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QRadioButton, QCheckBox, QStyle, QVBoxLayout,
    QColorDialog, QWidget, QTreeWidget, QTreeWidgetItem, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QToolButton, QFontDialog, QSpinBox, QButtonGroup, QTabWidget, QMenu, QAction,
    QInputDialog, QApplication, QDateEdit,
)
from software_installer_model import InstallerProject, InstallerProjectRegistry
from installer_security_settings import (
    SECURITY_SECTION, parse_security_settings, encode_security_settings, validate_serial_list,
    default_validity_settings, MAX_REG_COUNT,
)
from installer_log_settings import (
    LOG_FILE_SECTION, LOG_FILE_DEFAULTS, parse_log_settings, encode_log_settings,
)
from installer_system_requirements import (
    SYSTEM_REQUIREMENTS_SECTION, parse_system_requirements, encode_system_requirements,
)
from installer_background_settings import (
    BACKGROUND_SECTION, BACKGROUND_DEFAULTS, parse_background_settings,
    encode_background_settings,
)
from installer_session_variables import (
    SESSION_SECTION, default_session_groups, effective_session_groups,
    encode_session_variables, check_variable_name,
)
from installer_wizard_options import (
    WINDOWS_LANGUAGES, DEFAULT_LANGUAGES, DEFAULT_LANGUAGE,
    WINDOWS_VERSION_TREE, DEFAULT_WINDOWS_VERSIONS, windows_leaf_ids,
    decode_selection, encode_selection, normalized_default_language,
)


WIZARD_SIZE = (760, 590)  # Stage 559: -20 px Breite und -30 px Hoehe, alle sieben Seiten.
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
            QLineEdit, QListWidget, QComboBox, QSpinBox, QDateEdit {{ background: {panel}; color: {fg};
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
            QTreeWidget#installerWindowsTree, QTreeWidget#installerSystemWindowsTree,
            QTreeWidget#installerSerialConfigurationsTree {{ background: {panel}; color: {fg};
                border: 1px solid {border}; border-radius: 3px;
                alternate-background-color: {bg}; selection-background-color: {selection}; }}
            QScrollArea#installerBackgroundScroll,
            QScrollArea#installerValidityScroll {{ background: {bg}; border: none; }}
            QWidget#installerValidityBody {{ background: {bg}; color: {fg}; }}
            QWidget#installerBackgroundBody {{ background: {bg}; color: {fg}; }}
            QGroupBox#installerBackgroundMode, QGroupBox#installerBackgroundAppearance,
            QGroupBox#installerBackgroundText {{ font-weight: bold; }}
            QTabWidget#installerSecurityTabs::pane {{ background: {bg}; border: 1px solid {border}; }}
            QTabWidget#installerSecurityTabs QTabBar::tab {{ background: {panel}; color: {fg};
                border: 1px solid {border}; padding: 6px 15px; margin-right: 2px; }}
            QTabWidget#installerSecurityTabs QTabBar::tab:selected {{ background: {highlight}; }}
            QTabWidget#installerSecurityTabs QTabBar::tab:hover {{ background: {highlight}; }}
            QToolButton#installerSerialCommandsButton {{ background: {panel}; color: {fg};
                border: 1px solid {border}; border-radius: 3px; padding: 5px 9px; }}
            QToolButton#installerSerialCommandsButton:hover {{ background: {highlight}; }}
            QMenu#installerSerialCommandsMenu {{ background: {panel}; color: {fg};
                border: 1px solid {border}; }}
            QMenu#installerSerialCommandsMenu::item:selected {{ background: {highlight}; }}
            QMenu#installerSerialCommandsMenu::separator {{ height: 1px; background: {border};
                margin: 3px 8px; }}
            QTableWidget#installerSerialListsTable QHeaderView::section,
            QTableWidget#installerSerialNumbersTable QHeaderView::section {{
                background: {panel}; color: {fg}; border: 1px solid {border}; padding: 5px; }}
            QScrollArea#installerSessionScroll {{ background: {bg}; border: none; }}
            QWidget#installerSessionScrollBody {{ background: {bg}; }}
            QFrame#installerSessionPanel {{ border: 1px solid {border}; border-radius: 4px;
                background: {panel}; }}
            QFrame#installerSessionPanelHeader {{ background: {highlight}; border: none;
                border-bottom: 1px solid {border}; }}
            QLabel#installerSessionPanelCaption {{ font-weight: bold; color: {fg}; }}
            QToolButton#installerSessionPanelToggle {{ background: transparent; color: {fg};
                border: none; padding: 4px; }}
            QTableWidget#installerSerialListsTable, QTableWidget#installerSerialNumbersTable,
            QTableWidget#installerSessionTable {{ color: {fg}; background: {panel};
                border: none; selection-background-color: {selection};
                gridline-color: {border}; }}
        """)
        for table_name in ("installerSerialListsTable", "installerSerialNumbersTable"):
            table = self.findChild(QTableWidget, table_name)
            if table is not None:
                _style_installer_serial_header(table, self._dark_mode)
        if self.isVisible() and not self._gradient_title:
            _set_windows_dark_titlebar(self, self._dark_mode)


def _installer_serial_font():
    """Monospaced-Serials mit geordneter Font-Fallback-Liste (Qt >= 5.13)."""
    font = QFont("Consolas")
    if hasattr(font, "setFamilies"):
        font.setFamilies(["Consolas", "Courier New", "Courier"])
    font.setStyleHint(QFont.TypeWriter)
    return font


def _style_installer_serial_header(table: QTableWidget, dark: bool) -> None:
    """Header explizit stylen: auch mit nativem Windows-QStyle im Dark-Mode."""
    if dark:
        background, hover, foreground, border = (
            "#343b48", "#46566d", "#f1f2f4", "#515b6c")
    else:
        background, hover, foreground, border = (
            "#e4e9ef", "#d4e2f2", "#20242b", "#b7c1cf")
    header = table.horizontalHeader()
    header.setHighlightSections(False)
    header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header.setMinimumHeight(30)
    # Direkte Header-QSS hat Vorrang vor dem plattformspezifischen QHeaderView-Style.
    header.setStyleSheet(f"""
        QHeaderView {{ background-color: {background}; color: {foreground};
            border: none; }}
        QHeaderView::section {{ background-color: {background}; color: {foreground};
            border: none; border-right: 1px solid {border};
            border-bottom: 1px solid {border}; padding: 5px 8px;
            font-weight: bold; }}
        QHeaderView::section:hover, QHeaderView::section:pressed {{
            background-color: {hover}; color: {foreground}; }}
    """)


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



class InstallerSessionVariableEntryDialog(InstallerThemedDialog):
    """Eingabe fuer eine neue oder umzubenennende benutzerdefinierte Variable."""

    def __init__(self, parent=None, *, dark_mode=False, name="", value="", rename=False):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle("Session-Variable umbenennen" if rename else "Session-Variable hinzufügen")
        self.setObjectName("installerSessionEntryDialog")
        self.setFixedSize(420, 240)
        layout = self._content_layout()
        self.name_edit = QLineEdit(self)
        self.name_edit.setObjectName("installerSessionVariableName")
        self.name_edit.setPlaceholderText("%VariableName%")
        self.name_edit.setText(name)
        self.value_edit = QLineEdit(self)
        self.value_edit.setObjectName("installerSessionVariableValue")
        self.value_edit.setPlaceholderText("Wert")
        self.value_edit.setText(value)
        layout.addWidget(self.name_edit)
        layout.addWidget(self.value_edit)
        layout.addStretch(1)
        layout.addWidget(_line(self))
        row, self.buttons = _button_row(
            self, ("OK", "Abbrechen"), (self.accept, self.reject))
        layout.addLayout(row)

    def result_values(self):
        return self.name_edit.text().strip(), self.value_edit.text()


class InstallerResizableSessionTable(QTableWidget):
    """Verstellbare Spaltengrenze direkt in den Zellen, ganz ohne Header.

    Ein Drag innerhalb von RESIZE_GRAB_WIDTH Pixeln um die Trennlinie
    veraendert die erste Spaltenbreite. Sonstige Klicks und Doppelklicks
    bleiben der normalen Tabellen-Selektion bzw. Zellbearbeitung vorbehalten.
    """

    RESIZE_GRAB_WIDTH = 6

    def __init__(self, rows=0, columns=2, parent=None):
        super().__init__(rows, columns, parent)
        self._resize_dragging = False
        self._resize_start_x = 0
        self._resize_start_width = 0
        self._resize_cursor_active = False
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def _near_session_divider(self, x):
        """Spaltengrenze in Viewport-Koordinaten; auch ohne Header sichtbar."""
        boundary = self.columnViewportPosition(1)
        return boundary >= 0 and abs(int(x) - boundary) <= self.RESIZE_GRAB_WIDTH

    def _update_divider_cursor(self, x):
        near = self._near_session_divider(x)
        if near != self._resize_cursor_active:
            self._resize_cursor_active = near
            if near:
                self.viewport().setCursor(Qt.SplitHCursor)
            else:
                self.viewport().unsetCursor()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._near_session_divider(event.x()):
            self._resize_dragging = True
            self._resize_start_x = event.x()
            self._resize_start_width = self.columnWidth(0)
            self.viewport().setCursor(Qt.SplitHCursor)
            self._resize_cursor_active = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_dragging:
            requested = self._resize_start_width + event.x() - self._resize_start_x
            self.setColumnWidth(0, max(96, int(requested)))
            event.accept()
            return
        self._update_divider_cursor(event.x())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resize_dragging and event.button() == Qt.LeftButton:
            self._resize_dragging = False
            self._update_divider_cursor(event.x())
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        if not self._resize_dragging:
            self._resize_cursor_active = False
            self.viewport().unsetCursor()
        super().leaveEvent(event)


class InstallerSessionCollapsiblePanel(QFrame):
    """Ausklappbarer Panelkopf mit fixer, nicht vertikal scrollbarerer Tabelle."""

    def __init__(self, caption, parent=None):
        super().__init__(parent)
        self.setObjectName("installerSessionPanel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)
        self.header = QFrame(self)
        self.header.setObjectName("installerSessionPanelHeader")
        head = QHBoxLayout(self.header)
        head.setContentsMargins(4, 2, 8, 2)
        head.setSpacing(4)
        self.toggle_button = QToolButton(self.header)
        self.toggle_button.setObjectName("installerSessionPanelToggle")
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.setToolTip(caption + " einklappen")
        self.toggle_button.clicked.connect(self.toggle)
        head.addWidget(self.toggle_button)
        label = QLabel(caption, self.header)
        label.setObjectName("installerSessionPanelCaption")
        head.addWidget(label, 1)
        outer.addWidget(self.header)
        self.table = InstallerResizableSessionTable(0, 2, self)
        self.table.setObjectName("installerSessionTable")
        # Kein Kopf-/Ziehstreifen: direkt an der senkrechten Zellengrenze ziehen.
        header = self.table.horizontalHeader()
        header.hide()
        header.setSectionsMovable(False)
        self.table.setToolTip("Spaltengrenze zwischen Variable und Wert ziehen")
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked |
                                   QAbstractItemView.EditKeyPressed |
                                   QAbstractItemView.SelectedClicked)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header.setMinimumSectionSize(96)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 195)
        self.table.setFixedHeight(
            self.table.verticalHeader().defaultSectionSize() + 4)
        outer.addWidget(self.table)
        self._expanded = True

    def populate(self, variables):
        self.table.setRowCount(len(variables))
        for row, (name, value) in enumerate(variables.items()):
            name_item = QTableWidgetItem(str(name))
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, value_item)
        # Auch die leere Tabelle braucht eine greifbare Spaltengrenze.
        self.table.setFixedHeight(
            max(1, len(variables)) * self.table.verticalHeader().defaultSectionSize() + 4)

    def values(self):
        return {self.table.item(row, 0).text(): self.table.item(row, 1).text()
                for row in range(self.table.rowCount())}

    def selected_name(self):
        row = self.table.currentRow()
        return self.table.item(row, 0).text() if row >= 0 else None

    def toggle(self, _checked=False):
        self._expanded = not self._expanded
        self.table.setVisible(self._expanded)
        self.toggle_button.setArrowType(Qt.DownArrow if self._expanded else Qt.RightArrow)
        self.toggle_button.setToolTip(
            "Einklappen" if self._expanded else "Aufklappen")


class InstallerSessionVariablesDialog(InstallerThemedDialog):
    """Session-Variablen: drei Panels, Wizard-Vorgaben und editierbare Werte."""

    def __init__(self, project: InstallerProject, parent=None, *, dark_mode=False,
                 help_callback=None):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle("Session Variablen")
        self.setObjectName("installerSessionVariablesDialog")
        self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)
        self.project = project
        self.help_callback = help_callback
        self.groups = effective_session_groups(
            project.general, project.sections.get(SESSION_SECTION, ""))
        self.serialized = None
        layout = self._content_layout()
        self.scroll = QScrollArea(self)
        self.scroll.setObjectName("installerSessionScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget(self.scroll)
        container.setObjectName("installerSessionScrollBody")
        vertical = QVBoxLayout(container)
        vertical.setContentsMargins(6, 6, 6, 6)
        vertical.setSpacing(8)
        self.panels = {}
        for key, title in (("product", "Produkt Informationen"),
                           ("directories", "Standard-Verzeichnisse"),
                           ("custom", "Benutzerdefiniert")):
            panel = InstallerSessionCollapsiblePanel(title, container)
            panel.populate(self.groups[key])
            vertical.addWidget(panel)
            self.panels[key] = panel
        # Ein gemeinsamer Spaltenwert fuer alle drei Tabellen. Erst nach der
        # kompletten Initialisierung verbinden, damit Signale beim Aufbau
        # keine nur teilweise angelegten Panels aktualisieren.
        self._syncing_session_columns = False
        self._session_name_column_width = 195
        for panel in self.panels.values():
            panel.table.setColumnWidth(0, self._session_name_column_width)
            panel.table.horizontalHeader().sectionResized.connect(
                self._sync_session_name_column)
        vertical.addStretch(1)
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll, 1)
        layout.addWidget(_line(self))

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Hinzufügen", self)
        self.remove_button = QPushButton("Entfernen", self)
        self.rename_button = QPushButton("Umbenennen", self)
        self.add_button.clicked.connect(self._add_custom)
        self.remove_button.clicked.connect(self._remove_custom)
        self.rename_button.clicked.connect(self._rename_custom)
        for button in (self.add_button, self.remove_button, self.rename_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Abbrechen", self)
        self.help_button = QPushButton("Hilfe", self)
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self._accept_changes)
        self.cancel_button.clicked.connect(self.reject)
        self.help_button.clicked.connect(self._help)
        for button in (self.ok_button, self.cancel_button, self.help_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def _sync_session_name_column(self, logical_index, _old_width, new_width):
        """Ziehen von Spalte 1 synchronisiert alle Panels, auch eingeklappte.

        Spalte 2 fuellt den verbliebenen Tabellenbereich automatisch aus.
        Die Guard-Variable verhindert Signalrekursion durch setColumnWidth.
        """
        if logical_index != 0 or self._syncing_session_columns:
            return
        self._syncing_session_columns = True
        try:
            # Bei schmalen Fenstern soll die Wert-Spalte mindestens 96 px
            # behalten. Die drei Tabellen haben denselben Layout-Bereich.
            available = [panel.table.viewport().width()
                         for panel in self.panels.values()
                         if panel.table.isVisible() and panel.table.viewport().width() > 192]
            limit = min(available) - 96 if available else max(195, int(new_width))
            width = max(96, min(int(new_width), limit))
            self._session_name_column_width = width
            for panel in self.panels.values():
                if panel.table.columnWidth(0) != width:
                    panel.table.setColumnWidth(0, width)
        finally:
            self._syncing_session_columns = False

    def _current_groups(self):
        return {key: panel.values() for key, panel in self.panels.items()}

    def _all_names(self):
        groups = self._current_groups()
        return tuple(name for group in groups.values() for name in group)

    def _add_custom(self):
        editor = InstallerSessionVariableEntryDialog(self, dark_mode=self._dark_mode)
        if editor.exec_() != QDialog.Accepted:
            return
        name, value = editor.result_values()
        try:
            name = check_variable_name(name, self._all_names())
        except ValueError as error:
            QMessageBox.warning(self, "Session Variablen", str(error))
            return
        self.panels["custom"].populate({**self.panels["custom"].values(), name: value})
        self.panels["custom"].table.setCurrentCell(
            self.panels["custom"].table.rowCount() - 1, 1)

    def _remove_custom(self):
        custom = self.panels["custom"]
        name = custom.selected_name()
        if name is None:
            QMessageBox.information(self, "Session Variablen",
                                    "Bitte im Bereich Benutzerdefiniert eine Variable auswählen.")
            return
        values = custom.values()
        del values[name]
        custom.populate(values)

    def _rename_custom(self):
        custom = self.panels["custom"]
        old_name = custom.selected_name()
        if old_name is None:
            QMessageBox.information(self, "Session Variablen",
                                    "Nur benutzerdefinierte Variablen können umbenannt werden.")
            return
        previous = custom.values()
        editor = InstallerSessionVariableEntryDialog(
            self, dark_mode=self._dark_mode, name=old_name,
            value=previous[old_name], rename=True)
        if editor.exec_() != QDialog.Accepted:
            return
        new_name, value = editor.result_values()
        try:
            new_name = check_variable_name(new_name, self._all_names(), previous=old_name)
        except ValueError as error:
            QMessageBox.warning(self, "Session Variablen", str(error))
            return
        reordered = {}
        for name, current in previous.items():
            if name == old_name:
                reordered[new_name] = value
            else:
                reordered[name] = current
        custom.populate(reordered)

    def _accept_changes(self):
        try:
            self.serialized = encode_session_variables(
                self.project.general, self._current_groups())
        except ValueError as error:
            QMessageBox.warning(self, "Session Variablen", str(error))
            return
        self.accept()

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Session Variablen")

class InstallerBackgroundWindowDialog(InstallerThemedDialog):
    """Konfiguration von Fenster-Modus, Hintergrundbild/-farbe und Textzeilen.

    620 x 550 wie 'Session Variablen'. Änderungen werden erst bei OK in
    self.serialized bereitgestellt; das Projektobjekt bleibt unberührt.
    """

    def __init__(self, project: InstallerProject, parent=None, *, dark_mode=False,
                 help_callback=None):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle("Hintergrund Fenster")
        self.setObjectName("installerBackgroundWindowDialog")
        self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)
        self.project = project
        self.help_callback = help_callback
        self.serialized = None
        settings = parse_background_settings(project.sections.get(BACKGROUND_SECTION, ""))
        self._fonts = {}
        layout = self._content_layout()

        self.show_background_check = QCheckBox("Hintergrund Fenster anzeigen", self)
        self.show_background_check.setObjectName("installerBackgroundEnabled")
        self.show_background_check.setChecked(settings["enabled"])
        layout.addWidget(self.show_background_check)

        self.scroll = QScrollArea(self)
        self.scroll.setObjectName("installerBackgroundScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget(self.scroll)
        body.setObjectName("installerBackgroundBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(4, 4, 4, 4)
        body_layout.setSpacing(10)

        left_column = QVBoxLayout()
        # Keine zusaetzlichen Einrueckungen: die linke Fenster-GroupBox und
        # die rechte Text-GroupBox beginnen exakt auf derselben Hoehe.
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(10)
        # Etwas weniger als die halbe Dialogbreite (620 px).
        self.mode_group = QGroupBox("Fenster", body)
        self.mode_group.setObjectName("installerBackgroundMode")
        mode_layout = QVBoxLayout(self.mode_group)
        self.mode_radios = {}
        for code, caption in (("standard", "Standard"),
                              ("framed", "Eingerahmt"),
                              ("kiosk", "Kiosk")):
            radio = QRadioButton(caption, self.mode_group)
            radio.setObjectName("installerBackgroundMode_" + code)
            radio.setChecked(settings["mode"] == code)
            self.mode_radios[code] = radio
            mode_layout.addWidget(radio)
        left_column.addWidget(self.mode_group)

        self.appearance_group = QGroupBox("Aussehen", body)
        self.appearance_group.setObjectName("installerBackgroundAppearance")
        appearance_layout = QVBoxLayout(self.appearance_group)
        appearance_layout.setSpacing(5)
        self.appearance_radios = {}
        self.static_radio = QRadioButton("Statische Farbe", self.appearance_group)
        self.static_radio.setObjectName("installerBackgroundStaticRadio")
        appearance_layout.addWidget(self.static_radio)
        self.static_color = InstallerColorComboBox(
            self.appearance_group, color=settings["static_color"])
        self.static_color.setObjectName("installerBackgroundStaticColor")
        appearance_layout.addWidget(self.static_color)
        self.gradient_radio = QRadioButton("Verlauf", self.appearance_group)
        self.gradient_radio.setObjectName("installerBackgroundGradientRadio")
        appearance_layout.addWidget(self.gradient_radio)
        gradient_row = QHBoxLayout()
        gradient_row.setSpacing(5)
        self.gradient_start = InstallerColorComboBox(
            self.appearance_group, color=settings["gradient_start"])
        self.gradient_start.setObjectName("installerBackgroundGradientStart")
        self.gradient_end = InstallerColorComboBox(
            self.appearance_group, color=settings["gradient_end"])
        self.gradient_end.setObjectName("installerBackgroundGradientEnd")
        gradient_row.addWidget(self.gradient_start, 1)
        gradient_row.addWidget(self.gradient_end, 1)
        appearance_layout.addLayout(gradient_row)
        self.image_radio = QRadioButton("Bild", self.appearance_group)
        self.image_radio.setObjectName("installerBackgroundImageRadio")
        appearance_layout.addWidget(self.image_radio)
        self.image_edit = QLineEdit(settings["image_path"], self.appearance_group)
        self.image_edit.setObjectName("installerBackgroundImagePath")
        self.image_edit.setPlaceholderText("Bildpfad")
        appearance_layout.addWidget(self.image_edit)
        self.image_browse = QPushButton("Durchsuchen", self.appearance_group)
        self.image_browse.setObjectName("installerBackgroundImageBrowse")
        self.image_browse.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.image_browse.clicked.connect(self._browse_image)
        appearance_layout.addWidget(self.image_browse, 0, Qt.AlignLeft)
        # "Aussehen" nimmt die uebrige Spaltenhoehe ein: die linke
        # GroupBox-Kombination schliesst unten mit "Text" rechts ab.
        left_column.addWidget(self.appearance_group, 1)
        left_widget = QWidget(body)
        left_widget.setObjectName("installerBackgroundLeftColumn")
        left_widget.setLayout(left_column)
        left_widget.setFixedWidth(242)
        # Kein AlignTop: beide Spalten werden von QHBoxLayout gleich hoch
        # aufgezogen, statt die linke Spalte auf ihre SizeHint zu kuerzen.
        body_layout.addWidget(left_widget, 0)

        # Rechts auf gleicher Ober- und Unterkante wie links.
        self.text_group = QGroupBox("Text", body)
        self.text_group.setObjectName("installerBackgroundText")
        text_layout = QVBoxLayout(self.text_group)
        text_layout.setSpacing(5)
        self.text_edits = {}
        self.text_colors = {}
        self.text_font_buttons = {}
        self.text_align_radios = {}
        for key, title, fallback in (
            ("title", "Titel-Zeile", "%ProductName%"),
            ("version", "Version-Zeile", "%ProductVersion%"),
            ("footer", "Fuß-Zeile", "%Copyright% Alle Rechte vorbehalten."),
        ):
            text_layout.addWidget(QLabel(title, self.text_group))
            edit = QLineEdit(settings.get(key + "_text", fallback), self.text_group)
            edit.setObjectName("installerBackgroundText_" + key)
            # Die Eingabezeile belegt die komplette nutzbare GroupBox-Breite.
            text_layout.addWidget(edit)

            # Schriftauswahl und Farbe stehen in einer eigenen Zeile unter
            # dem Textfeld. So bleibt Raum fuer einen lesbaren Font-Button.
            options_row = QHBoxLayout()
            options_row.setSpacing(8)
            font_button = QPushButton("Aa  Schriftart", self.text_group)
            font_button.setObjectName("installerBackgroundFont_" + key)
            font_button.setToolTip("Schriftart für " + title + " auswählen")
            font_button.setMinimumWidth(116)
            font_button.clicked.connect(
                lambda _checked=False, which=key: self._choose_font(which))
            options_row.addWidget(font_button)
            color = InstallerColorComboBox(
                self.text_group, color=settings.get(key + "_color", "#ffffff"))
            color.setObjectName("installerBackgroundColor_" + key)
            color.setMinimumWidth(103)
            options_row.addWidget(color, 1)
            text_layout.addLayout(options_row)
            self.text_edits[key] = edit
            self.text_colors[key] = color
            self.text_font_buttons[key] = font_button
            font = QFont(self.font())
            stored_font = str(settings.get(key + "_font", ""))
            if stored_font:
                font.fromString(stored_font)
            self._fonts[key] = font
            font_button.setToolTip("Schriftart: " + font.family() + " (ändern)")
            if key != "footer":
                alignment_holder = QWidget(self.text_group)
                alignment_row = QHBoxLayout(alignment_holder)
                alignment_row.setContentsMargins(0, 0, 0, 0)
                alignment_row.setSpacing(7)
                radios = {}
                for code, caption in (("left", "Links"), ("center", "Mitte"),
                                      ("right", "Rechts")):
                    radio = QRadioButton(caption, alignment_holder)
                    radio.setObjectName("installerBackgroundAlign_" + key + "_" + code)
                    radio.setChecked(settings[key + "_align"] == code)
                    radios[code] = radio
                    alignment_row.addWidget(radio)
                self.text_align_radios[key] = radios
                text_layout.addWidget(alignment_holder)
        text_layout.addStretch(1)
        body_layout.addWidget(self.text_group, 1)
        self.scroll.setWidget(body)
        layout.addWidget(self.scroll, 1)
        layout.addWidget(_line(self))
        buttons, self.buttons = _button_row(
            self, ("OK", "Abbrechen", "Hilfe"),
            (self._accept_changes, self.reject, self._help), default_index=0)
        layout.addLayout(buttons)
        self.ok_button, self.cancel_button, self.help_button = self.buttons

        self.static_radio.setChecked(settings["appearance"] == "static")
        self.gradient_radio.setChecked(settings["appearance"] == "gradient")
        self.image_radio.setChecked(settings["appearance"] == "image")
        for radio in (self.static_radio, self.gradient_radio, self.image_radio):
            radio.toggled.connect(self._sync_appearance)
        self._sync_appearance()

    def _sync_appearance(self, _checked=None):
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

    def _choose_font(self, which):
        selected, accepted = QFontDialog.getFont(
            self._fonts[which], self, "Schriftart auswählen")
        if accepted:
            self._fonts[which] = QFont(selected)
            self.text_font_buttons[which].setToolTip(
                "Schriftart: " + selected.family() + " (ändern)")

    def settings(self):
        mode = next((name for name, radio in self.mode_radios.items()
                     if radio.isChecked()), "standard")
        appearance = ("image" if self.image_radio.isChecked() else
                      "gradient" if self.gradient_radio.isChecked() else "static")
        settings = {
            "enabled": self.show_background_check.isChecked(),
            "mode": mode,
            "appearance": appearance,
            "static_color": self.static_color.color(),
            "gradient_start": self.gradient_start.color(),
            "gradient_end": self.gradient_end.color(),
            "image_path": self.image_edit.text().strip(),
        }
        for key in ("title", "version", "footer"):
            settings[key + "_text"] = self.text_edits[key].text()
            settings[key + "_font"] = self._fonts[key].toString()
            settings[key + "_color"] = self.text_colors[key].color()
        for key in ("title", "version"):
            settings[key + "_align"] = next((name for name, radio
                                             in self.text_align_radios[key].items()
                                             if radio.isChecked()), "center")
        return settings

    def _accept_changes(self):
        try:
            self.serialized = encode_background_settings(self.settings())
        except (ValueError, TypeError) as error:
            QMessageBox.warning(self, "Hintergrund Fenster", str(error))
            return
        self.accept()

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Hintergrund Fenster")



class InstallerSystemRequirementsDialog(InstallerThemedDialog):
    """Stage 564: Systemanforderungen, gleiche Geometrie wie Hintergrund Fenster.

    Keine Projektdatenmutation bis zum akzeptierten Dialog und Speichern.
    """

    # Identische Checkbox-Hierarchie wie im bestehenden Windows-Wizard.
    _append_node = InstallerRequirementsDialog._append_node
    _set_descendants = InstallerRequirementsDialog._set_descendants
    _recompute_parent = InstallerRequirementsDialog._recompute_parent
    _on_item_changed = InstallerRequirementsDialog._on_item_changed
    _checked_leaves = InstallerRequirementsDialog._checked_leaves

    def __init__(self, project: InstallerProject, parent=None, *, dark_mode=False,
                 help_callback=None):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle("Systemanforderungen")
        self.setObjectName("installerSystemRequirementsDialog")
        self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)
        self.help_callback = help_callback
        self.serialized = None
        settings = parse_system_requirements(
            project.sections.get(SYSTEM_REQUIREMENTS_SECTION, ""))
        layout = self._content_layout()
        columns = QHBoxLayout()
        columns.setSpacing(10)
        layout.addLayout(columns, 1)

        self.windows_group = QGroupBox("Betriebs-System", self)
        self.windows_group.setObjectName("installerSystemWindowsGroup")
        left = QVBoxLayout(self.windows_group)
        self.windows_tree = QTreeWidget(self.windows_group)
        self.windows_tree.setObjectName("installerSystemWindowsTree")
        self.windows_tree.setHeaderHidden(True)
        self.windows_tree.setAlternatingRowColors(True)
        self.windows_tree.setUniformRowHeights(True)
        self.windows_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._updating_tree = False
        selected = set(settings["windows_versions"])
        for node in WINDOWS_VERSION_TREE:
            self._append_node(None, node, selected)
        self.windows_tree.expandAll()
        self.windows_tree.itemChanged.connect(self._on_item_changed)
        left.addWidget(self.windows_tree)
        columns.addWidget(self.windows_group, 1)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(10)
        columns.addLayout(right, 1)
        self.checks_group = QGroupBox("System-Prüfungen", self)
        self.checks_group.setObjectName("installerSystemChecksGroup")
        grid = QGridLayout(self.checks_group)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(12)
        self.spinboxes = {}
        for row, (key, caption, unit) in enumerate((
            ("ram_mb", "RAM", "MB"),
            ("screen_width_px", "Bildschirm Weite", "Pixel"),
            ("screen_height_px", "Bildschirm Höhe", "Pixel"),
            ("color_depth_bpp", "Farbtiefe", "BPP"),
        )):
            grid.addWidget(QLabel(caption, self.checks_group), row, 0)
            spin = QSpinBox(self.checks_group)
            spin.setObjectName("installerSystem_" + key)
            spin.setRange(0, 2147483647)
            spin.setValue(settings[key])
            spin.setMinimumWidth(65)
            grid.addWidget(spin, row, 1)
            grid.addWidget(QLabel(unit, self.checks_group), row, 2)
            self.spinboxes[key] = spin
        grid.setColumnStretch(1, 1)
        self.admin_check = QCheckBox("Benutzer muss Adminrechte haben", self.checks_group)
        self.admin_check.setObjectName("installerSystemRequireAdmin")
        self.admin_check.setChecked(settings["require_admin"])
        grid.addWidget(self.admin_check, 4, 0, 1, 3)
        grid.setRowStretch(5, 1)
        right.addWidget(self.checks_group, 1)

        self.notify_group = QGroupBox("Benutzer benachrichtigen", self)
        self.notify_group.setObjectName("installerSystemNotifyGroup")
        notify_layout = QVBoxLayout(self.notify_group)
        notify_layout.setSpacing(12)
        self.warn_check = QCheckBox("Benutzer warnen und fortfahren", self.notify_group)
        self.warn_check.setObjectName("installerSystemWarnContinue")
        self.abort_check = QCheckBox("Benachrichten und Setup abbrechen", self.notify_group)
        self.abort_check.setObjectName("installerSystemAbortSetup")
        self.warn_check.setChecked(settings["notification"] == "warn_continue")
        self.abort_check.setChecked(settings["notification"] == "abort_setup")
        # Gegenseitig ausschliessend, aber optisch wie angefordert Checkboxen.
        self.warn_check.toggled.connect(self._warn_toggled)
        self.abort_check.toggled.connect(self._abort_toggled)
        notify_layout.addWidget(self.warn_check)
        notify_layout.addWidget(self.abort_check)
        notify_layout.addStretch(1)
        right.addWidget(self.notify_group, 1)

        layout.addWidget(_line(self))
        buttons, self.buttons = _button_row(
            self, ("OK", "Abbrechen", "Hilfe"),
            (self._accept_changes, self.reject, self._help), default_index=0)
        layout.addLayout(buttons)
        self.ok_button, self.cancel_button, self.help_button = self.buttons

    def _warn_toggled(self, checked):
        if checked:
            self.abort_check.setChecked(False)
        elif not self.abort_check.isChecked():
            self.warn_check.setChecked(True)

    def _abort_toggled(self, checked):
        if checked:
            self.warn_check.setChecked(False)
        elif not self.warn_check.isChecked():
            self.abort_check.setChecked(True)

    def settings(self):
        return {
            "windows_versions": self._checked_leaves(),
            **{key: spin.value() for key, spin in self.spinboxes.items()},
            "require_admin": self.admin_check.isChecked(),
            "notification": "abort_setup" if self.abort_check.isChecked() else "warn_continue",
        }

    def _accept_changes(self):
        try:
            self.serialized = encode_system_requirements(self.settings())
        except (ValueError, TypeError) as error:
            QMessageBox.warning(self, "Systemanforderungen", str(error))
            return
        self.accept()

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Systemanforderungen")


class InstallerLogFileDialog(InstallerThemedDialog):
    """Stage 565: Log-Datei, 620x550 px wie der Systemanforderungen-Dialog.

    Keine Veränderung der Projektdaten bis zur OK-Bestätigung.
    """

    def __init__(self, project: InstallerProject, parent=None, *, dark_mode=False,
                 help_callback=None):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle("Log-Datei")
        self.setObjectName("installerLogFileDialog")
        self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)
        self.help_callback = help_callback
        self.serialized = None
        settings = parse_log_settings(project.sections.get(LOG_FILE_SECTION, ""))

        layout = self._content_layout()
        self.enable_check = QCheckBox("Log-Datei anlegen", self)
        self.enable_check.setObjectName("installerLogFileEnabled")
        self.enable_check.setChecked(settings["enabled"])
        layout.addWidget(self.enable_check)

        # Dateiname und Schreibmodus liegen als gemeinsamer Block 26 px eingerückt.
        indent_row = QHBoxLayout()
        indent_row.setContentsMargins(0, 0, 0, 0)
        indent_row.addSpacing(26)
        self.details = QWidget(self)
        self.details.setObjectName("installerLogFileDetails")
        details_layout = QVBoxLayout(self.details)
        details_layout.setContentsMargins(0, 4, 0, 0)
        details_layout.setSpacing(10)

        self.filename_label = QLabel("Dateiname:", self.details)
        details_layout.addWidget(self.filename_label)
        self.filename_edit = QLineEdit(self.details)
        self.filename_edit.setObjectName("installerLogFileName")
        self.filename_edit.setMaxLength(4096)
        self.filename_edit.setText(settings["filename"])
        details_layout.addWidget(self.filename_edit)

        self.mode_label = QLabel("Schreibmodus:", self.details)
        details_layout.addWidget(self.mode_label)
        self.mode_buttons = QButtonGroup(self)
        self.mode_buttons.setExclusive(True)
        self.append_radio = QRadioButton("Anhängen", self.details)
        self.append_radio.setObjectName("installerLogFileAppend")
        self.overwrite_radio = QRadioButton("Überschreiben", self.details)
        self.overwrite_radio.setObjectName("installerLogFileOverwrite")
        self.mode_buttons.addButton(self.append_radio)
        self.mode_buttons.addButton(self.overwrite_radio)
        self.append_radio.setChecked(settings["write_mode"] == "append")
        self.overwrite_radio.setChecked(settings["write_mode"] == "overwrite")
        details_layout.addWidget(self.append_radio)
        details_layout.addWidget(self.overwrite_radio)
        indent_row.addWidget(self.details, 1)
        layout.addLayout(indent_row)
        layout.addStretch(1)

        self.enable_check.toggled.connect(self.details.setEnabled)
        self.details.setEnabled(self.enable_check.isChecked())

        layout.addWidget(_line(self))
        buttons, self.buttons = _button_row(
            self, ("OK", "Abbrechen", "Hilfe"),
            (self._accept_changes, self.reject, self._help), default_index=0)
        layout.addLayout(buttons)
        self.ok_button, self.cancel_button, self.help_button = self.buttons

    def settings(self):
        return {
            "enabled": self.enable_check.isChecked(),
            "filename": self.filename_edit.text(),
            "write_mode": "append" if self.append_radio.isChecked() else "overwrite",
        }

    def _accept_changes(self):
        try:
            self.serialized = encode_log_settings(self.settings())
        except (ValueError, TypeError) as error:
            installer_themed_warning(self, "Log-Datei", str(error),
                                     dark_mode=self._dark_mode)
            return
        self.accept()

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Log-Datei")



class InstallerSerialListPropertiesDialog(InstallerThemedDialog):
    """Kinddialog für eine Serial-Nummern-Liste; Änderungen erst nach OK."""

    def __init__(self, entry=None, parent=None, *, dark_mode=False,
                 help_callback=None, existing_names=()):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle("Serial Nummer - Listen Eigenschaften")
        self.setObjectName("installerSerialListPropertiesDialog")
        self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)
        self.help_callback = help_callback
        self.result_entry = None
        self.existing_names = {name.casefold() for name in existing_names}
        self._history = []
        self._future = []
        self._loading_serials = False
        entry = entry or {"name": "Neue Liste", "configurations": ["Standard"],
                          "serial_numbers": []}

        layout = self._content_layout()
        columns = QHBoxLayout()
        columns.setSpacing(12)
        layout.addLayout(columns, 1)

        left = QVBoxLayout()
        left.setSpacing(8)
        columns.addLayout(left, 2)
        left.addWidget(QLabel("Listen Name", self))
        self.name_edit = QLineEdit(self)
        self.name_edit.setObjectName("installerSerialListName")
        self.name_edit.setMaxLength(120)
        self.name_edit.setText(entry["name"])
        left.addWidget(self.name_edit)
        left.addWidget(QLabel("Konfigurationen", self))
        self.configuration_tree = QTreeWidget(self)
        self.configuration_tree.setObjectName("installerSerialConfigurationsTree")
        self.configuration_tree.setHeaderHidden(True)
        self.configuration_tree.setUniformRowHeights(True)
        self.configuration_tree.setAlternatingRowColors(True)
        self.configuration_tree.setRootIsDecorated(True)
        self._changing_configuration = False
        root = QTreeWidgetItem(self.configuration_tree, ["Alle Konfigurationen"])
        root.setFlags(root.flags() | Qt.ItemIsUserCheckable)
        standard = QTreeWidgetItem(root, ["Standard"])
        standard.setFlags(standard.flags() | Qt.ItemIsUserCheckable)
        checked = "Standard" in entry["configurations"]
        standard.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        root.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        self.configuration_tree.expandAll()
        self.configuration_tree.itemChanged.connect(self._configuration_changed)
        left.addWidget(self.configuration_tree, 1)

        right = QVBoxLayout()
        right.setSpacing(8)
        columns.addLayout(right, 4)
        header = QHBoxLayout()
        header.addWidget(QLabel("Serial Nummern", self), 1)
        self.commands_button = QToolButton(self)
        self.commands_button.setObjectName("installerSerialCommandsButton")
        self.commands_button.setText("Kommandos")
        self.commands_button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.commands_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.commands_menu = QMenu(self.commands_button)
        self.commands_menu.setObjectName("installerSerialCommandsMenu")
        self._create_commands()
        self.commands_button.setMenu(self.commands_menu)
        self.commands_button.clicked.connect(self.commands_button.showMenu)
        header.addWidget(self.commands_button, 0, Qt.AlignRight)
        right.addLayout(header)
        self.serial_table = QTableWidget(0, 3, self)
        self.serial_table.setObjectName("installerSerialNumbersTable")
        self.serial_table.setHorizontalHeaderLabels(
            ["Serial Nummer", "Belegt", "Reg. Count"])
        self.serial_font = _installer_serial_font()
        self.serial_table.setFont(self.serial_font)
        self.serial_table.verticalHeader().setVisible(False)
        _style_installer_serial_header(self.serial_table, self._dark_mode)
        self.serial_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive)
        self.serial_table.horizontalHeader().setStretchLastSection(False)
        for index, width in enumerate((190, 65, 88)):
            self.serial_table.setColumnWidth(index, width)
        self.serial_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.serial_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.serial_table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.SelectedClicked)
        self.serial_table.setAlternatingRowColors(True)
        self.serial_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.serial_table.customContextMenuRequested.connect(
            lambda point: self.commands_menu.exec_(
                self.serial_table.viewport().mapToGlobal(point)))
        right.addWidget(self.serial_table, 1)
        self.serial_table.itemChanged.connect(self._serial_item_changed)
        for action in self._shortcut_actions:
            self.serial_table.addAction(action)
        self._known_rows = []
        details = entry.get("serial_details", {})
        self._set_rows([
            {"serial": number,
             "occupied": details.get(number, {}).get("occupied", False),
             "reg_count": str(details.get(number, {}).get("reg_count", 0))}
            for number in entry["serial_numbers"]
        ])

        layout.addWidget(_line(self))
        row, self.buttons = _button_row(
            self, ("OK", "Abbrechen", "Hilfe"),
            (self._accept_changes, self.reject, self._help), default_index=0)
        layout.addLayout(row)
        self.ok_button, self.cancel_button, self.help_button = self.buttons

    def _configuration_changed(self, item, column):
        if column != 0 or self._changing_configuration:
            return
        self._changing_configuration = True
        try:
            root = self.configuration_tree.topLevelItem(0)
            child = root.child(0)
            if item is root:
                child.setCheckState(0, root.checkState(0))
            else:
                root.setCheckState(0, child.checkState(0))
        finally:
            self._changing_configuration = False

    def _create_commands(self):
        """Menüpunkte und Tastenkürzel, jeweils auf diesen Dialog begrenzt."""
        entries = (
            ("Wiederherstellen", "Ctrl+Z", self._undo),
            ("Rückgängig", "Ctrl+Y", self._redo),
            None,
            ("Erstellen ...", "Ctrl+G", self._generate),
            ("Finden", None, self._find),
            ("Sortieren", None, self._sort),
            None,
            ("Ausschneiden", "Ctrl+X", self._cut),
            ("Kopieren", "Ctrl+C", self._copy),
            ("Einfügen", "Ctrl+V", self._paste),
            ("Alle auswählen", "Ctrl+A", self._select_all),
            None,
            ("Alle Nummern löschen", "Ctrl+L", self._delete_all),
            ("Selektierte Reihen Löschen", "Ctrl+Delete", self._delete_selected),
            ("Reihe Einfügen", "Insert", self._insert_row),
            ("Reihen Einfügen", "Ctrl+Insert", self._insert_rows),
            None,
            ("Drucken", None, self._print),
            ("Importieren", None, self._import),
            ("Exportieren", None, self._export),
        )
        self.command_actions = {}
        for item in entries:
            if item is None:
                self.commands_menu.addSeparator()
                continue
            caption, shortcut, callback = item
            action = QAction(caption, self)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
                action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            action.triggered.connect(callback)
            self.commands_menu.addAction(action)
            self.command_actions[caption] = action
        # Die Tabelle wird erst nach dem Menü erzeugt: Shortcuts nachträglich anbinden.
        self._shortcut_actions = [action for action in self.command_actions.values()
                                  if not action.shortcut().isEmpty()]

    def _row_records(self):
        """UI-Snapshot einschließlich Belegt und Reg. Count (auch für Undo/Redo)."""
        records = []
        for row in range(self.serial_table.rowCount()):
            serial = self.serial_table.item(row, 0)
            occupied = self.serial_table.item(row, 1)
            count = self.serial_table.item(row, 2)
            records.append({
                "serial": serial.text() if serial else "",
                "occupied": bool(occupied and occupied.checkState() == Qt.Checked),
                "reg_count": count.text() if count else "0",
            })
        return records

    def _set_rows(self, rows):
        """Stellt UI wieder her; Metadaten folgen beim Sortieren ihrer Serial."""
        from collections import defaultdict, deque

        previous = self._loading_serials
        self._loading_serials = True
        try:
            old_by_serial = defaultdict(deque)
            for record in self._row_records():
                old_by_serial[record["serial"].casefold()].append(record)
            normalized = []
            for value in rows:
                if isinstance(value, dict):
                    record = dict(value)
                else:
                    serial = str(value)
                    options = old_by_serial[serial.casefold()]
                    record = dict(options.popleft()) if options else {
                        "serial": serial, "occupied": False, "reg_count": "0"}
                normalized.append(record)
            self.serial_table.blockSignals(True)
            try:
                self.serial_table.setRowCount(len(normalized))
                for index, record in enumerate(normalized):
                    serial_item = QTableWidgetItem(str(record["serial"]))
                    serial_item.setFont(self.serial_font)
                    self.serial_table.setItem(index, 0, serial_item)

                    occupied_item = QTableWidgetItem()
                    occupied_item.setFlags(
                        (occupied_item.flags() | Qt.ItemIsUserCheckable)
                        & ~Qt.ItemIsEditable)
                    occupied_item.setCheckState(
                        Qt.Checked if record.get("occupied", False) else Qt.Unchecked)
                    occupied_item.setTextAlignment(Qt.AlignCenter)
                    self.serial_table.setItem(index, 1, occupied_item)

                    count_item = QTableWidgetItem(str(record.get("reg_count", "0")))
                    count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.serial_table.setItem(index, 2, count_item)
            finally:
                self.serial_table.blockSignals(False)
        finally:
            self._loading_serials = previous
        self._known_rows = self._row_records()

    def _rows(self):
        # Bestehende Kommandos (Textimport, Copy/Paste, Finden, Drucken) bleiben
        # zeichenkettenbasiert; ihre Metadaten werden über _row_records bewahrt.
        return [record["serial"] for record in self._row_records()]

    def _push_history(self, records):
        self._history.append([dict(record) for record in records])
        if len(self._history) > 100:
            self._history.pop(0)
        self._future.clear()

    def _change_rows(self, rows, *, select_row=None):
        before = self._row_records()
        comparable = ([record["serial"] for record in before]
                      if all(isinstance(value, str) for value in rows) else before)
        if comparable == rows:
            return
        self._push_history(before)
        self._set_rows(rows)
        if select_row is not None and rows:
            self.serial_table.selectRow(min(max(0, select_row), len(rows) - 1))

    def _serial_item_changed(self, _item):
        if self._loading_serials:
            return
        updated = self._row_records()
        if updated != self._known_rows:
            self._push_history(self._known_rows)
            self._known_rows = updated

    def _undo(self):
        if self._history:
            self._future.append(self._row_records())
            self._set_rows(self._history.pop())

    def _redo(self):
        if self._future:
            self._history.append(self._row_records())
            self._set_rows(self._future.pop())

    def _selected_rows(self):
        return sorted(index.row() for index in self.serial_table.selectionModel().selectedRows())

    def _insert(self, count):
        pos = self.serial_table.currentRow()
        pos = pos if pos >= 0 else self.serial_table.rowCount()
        rows = self._rows()
        rows[pos:pos] = [""] * count
        self._change_rows(rows, select_row=pos)
        self.serial_table.editItem(self.serial_table.item(pos, 0))

    def _insert_row(self):
        self._insert(1)

    def _insert_rows(self):
        count, ok = QInputDialog.getInt(self, "Reihen Einfügen", "Anzahl Reihen:",
                                        2, 1, 10000)
        if ok:
            self._insert(count)

    def _delete_selected(self):
        selected = set(self._selected_rows())
        if selected:
            self._change_rows([value for i, value in enumerate(self._rows())
                               if i not in selected])

    def _delete_all(self):
        self._change_rows([])

    def _select_all(self):
        self.serial_table.selectAll()

    def _copy(self):
        selected = self._selected_rows()
        if selected:
            values = self._rows()
            QApplication.clipboard().setText("\n".join(values[i] for i in selected))

    def _cut(self):
        selected = self._selected_rows()
        if selected:
            self._copy()
            self._delete_selected()

    def _paste(self):
        text = QApplication.clipboard().text()
        values = [line.strip() for line in text.splitlines() if line.strip()]
        if values:
            rows = self._rows()
            pos = self.serial_table.currentRow()
            if pos < 0:
                pos = len(rows)
            rows[pos:pos] = values
            self._change_rows(rows, select_row=pos)

    def _generate(self):
        count, ok = QInputDialog.getInt(self, "Serial Nummern erstellen",
                                        "Anzahl neuer Serial Nummern:", 10, 1, 10000)
        if not ok:
            return
        import secrets
        rows = self._rows()
        seen = {value.casefold() for value in rows}
        generated = []
        while len(generated) < count:
            token = secrets.token_hex(8).upper()
            number = "-".join(token[pos:pos+4] for pos in range(0, 16, 4))
            if number.casefold() not in seen:
                seen.add(number.casefold())
                generated.append(number)
        self._change_rows(rows + generated, select_row=len(rows))

    def _find(self):
        phrase, ok = QInputDialog.getText(self, "Finden", "Serial Nummer suchen:")
        if not ok or not phrase:
            return
        rows = self._rows()
        start = max(self.serial_table.currentRow(), -1) + 1
        for i in list(range(start, len(rows))) + list(range(start)):
            if phrase.casefold() in rows[i].casefold():
                self.serial_table.setCurrentCell(i, 0)
                self.serial_table.selectRow(i)
                return
        installer_themed_warning(self, "Finden", "Keine passende Serial Nummer gefunden.",
                                 dark_mode=self._dark_mode)

    def _sort(self):
        rows = self._rows()
        filled = sorted((value for value in rows if value.strip()),
                        key=str.casefold)
        empty = [value for value in rows if not value.strip()]
        self._change_rows(filled + empty)

    def _import(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Serial Nummern importieren", "", "Textdateien (*.txt *.csv);;Alle Dateien (*)")
        if filename:
            try:
                lines = Path(filename).read_text(encoding="utf-8-sig").splitlines()
                values = [line.strip() for line in lines if line.strip()]
                self._change_rows(self._rows() + values)
            except (OSError, UnicodeError) as error:
                installer_themed_warning(self, "Importieren", str(error),
                                         dark_mode=self._dark_mode)

    def _export(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Serial Nummern exportieren", "serialnummern.txt", "Textdateien (*.txt)")
        if filename:
            try:
                Path(filename).write_text(
                    "\n".join(value.strip() for value in self._rows() if value.strip()) + "\n",
                    encoding="utf-8")
            except (OSError, UnicodeError) as error:
                installer_themed_warning(self, "Exportieren", str(error),
                                         dark_mode=self._dark_mode)

    def _serial_print_document(self):
        """Ein gemeinsames QTextDocument für Vorschau UND physisches Drucken."""
        from html import escape
        from PyQt5.QtGui import QTextDocument

        document = QTextDocument(self)
        document.setDefaultFont(self.serial_font)
        content = "<h2>Serial Nummern</h2><ol>" + "".join(
            "<li>" + escape(value) + "</li>"
            for value in self._rows() if value.strip()) + "</ol>"
        document.setHtml(content)
        return document

    def _print(self):
        """Zunächst Qt-Druckvorschau; deren Drucken-Schaltfläche öffnet QPrintDialog."""
        try:
            from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrinter

            printer = QPrinter(QPrinter.HighResolution)
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("Druckvorschau - Serial Nummern")
            preview.resize(900, 700)
            # Beide Wege verwenden exakt dasselbe Dokument; es wird erst beim
            # Drucken-Klick in der Vorschau physisch an den Drucker übergeben.
            document = self._serial_print_document()
            preview.paintRequested.connect(document.print_)
            preview.exec_()
        except (ImportError, RuntimeError, OSError) as error:
            installer_themed_warning(self, "Drucken", str(error),
                                     dark_mode=self._dark_mode)

    def _accept_changes(self):
        try:
            serials = []
            details = {}
            for record in self._row_records():
                number = record["serial"].strip()
                if not number:
                    continue
                if (not record["reg_count"].strip().isdigit()
                        or int(record["reg_count"]) > MAX_REG_COUNT):
                    raise ValueError("Reg. Count muss eine nichtnegative ganze Zahl sein")
                serials.append(number)
                count = int(record["reg_count"])
                if record["occupied"] or count:
                    details[number] = {"occupied": record["occupied"],
                                       "reg_count": count}
            entry = validate_serial_list({
                "name": self.name_edit.text(),
                "configurations": ["Standard"] if
                    self.configuration_tree.topLevelItem(0).child(0).checkState(0)
                    == Qt.Checked else [],
                "serial_numbers": serials,
                "serial_details": details,
            })
            if entry["name"].casefold() in self.existing_names:
                raise ValueError("Der Listenname ist bereits vorhanden")
        except (ValueError, TypeError) as error:
            installer_themed_warning(self, "Serial Nummer - Listen Eigenschaften",
                                     str(error), dark_mode=self._dark_mode)
            return
        self.result_entry = entry
        self.accept()

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Sicherheit")


class InstallerSecurityDialog(InstallerThemedDialog):
    """Serial-Nummern und Gültigkeits-Bereich (Stage 568)."""

    def __init__(self, project: InstallerProject, parent=None, *, dark_mode=False,
                 help_callback=None):
        super().__init__(parent, dark_mode=dark_mode, gradient_title=True)
        self.setWindowTitle("Sicherheit")
        self.setObjectName("installerSecurityDialog")
        self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)
        self.help_callback = help_callback
        self.serialized = None
        stored_security = parse_security_settings(project.sections.get(SECURITY_SECTION, ""))
        self.serial_lists = stored_security["serial_lists"]
        self.validity_settings = stored_security.get("validity", default_validity_settings())
        layout = self._content_layout()
        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("installerSecurityTabs")
        layout.addWidget(self.tabs, 1)
        serial_page = QWidget(self.tabs)
        self.tabs.addTab(serial_page, "Serial Nummer")
        serial_layout = QVBoxLayout(serial_page)
        serial_layout.setContentsMargins(10, 12, 10, 9)
        serial_layout.setSpacing(9)
        serial_layout.addWidget(QLabel("Serial Nummer Liste", serial_page))
        self.lists_table = QTableWidget(0, 3, serial_page)
        self.lists_table.setObjectName("installerSerialListsTable")
        self.lists_table.setHorizontalHeaderLabels(
            ["Listen Name", "Anzahl", "Konfiguration"])
        self.lists_table.verticalHeader().setVisible(False)
        _style_installer_serial_header(self.lists_table, self._dark_mode)
        self.lists_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.lists_table.horizontalHeader().setStretchLastSection(False)
        for index, width in enumerate((210, 80, 190)):
            self.lists_table.setColumnWidth(index, width)
        self.lists_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lists_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lists_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lists_table.setAlternatingRowColors(True)
        self.lists_table.doubleClicked.connect(self._edit_list)
        serial_layout.addWidget(self.lists_table, 1)
        self.duration_page = QWidget(self.tabs)
        self.duration_page.setObjectName("installerSecurityDurationPage")
        self.tabs.addTab(self.duration_page, "Gültigkeits-Bereich")
        self._build_validity_tab()

        layout.addWidget(_line(self))
        # Linke Listenaktionen und rechte Dialogaktionen teilen sich eine Zeile.
        actions, self.buttons = _button_row(
            self, ("OK", "Abbrechen", "Hilfe"),
            (self._accept_changes, self.reject, self._help), default_index=0)
        self.list_buttons = []
        for idx, (title, callback) in enumerate((("Hinzufügen", self._add_list),
                                                 ("Entfernen", self._remove_list),
                                                 ("Bearbeiten", self._edit_list))):
            button = QPushButton(title, self)
            button.clicked.connect(callback)
            actions.insertWidget(idx, button)
            self.list_buttons.append(button)
            setattr(self, ("add_button", "remove_button", "edit_button")[idx], button)
        layout.addLayout(actions)
        self.ok_button, self.cancel_button, self.help_button = self.buttons
        self.tabs.currentChanged.connect(self._tab_changed)
        self._update_list_table()

    def _build_validity_tab(self):
        """Drei GroupBoxen: links Datum und Zähler, rechts Kontakt/UUID.

        Wegen der unveränderten Dialoggröße 620×550 bleibt der Tab scrollbar.
        Die abschließenden OK-/Abbrechen-/Hilfe-Buttons liegen stets darunter.
        """
        values = self.validity_settings
        page_layout = QVBoxLayout(self.duration_page)
        page_layout.setContentsMargins(4, 4, 4, 4)
        scroller = QScrollArea(self.duration_page)
        scroller.setObjectName("installerValidityScroll")
        scroller.setWidgetResizable(True)
        scroller.setFrameShape(QFrame.NoFrame)
        page_layout.addWidget(scroller)
        body = QWidget(scroller)
        body.setObjectName("installerValidityBody")
        scroller.setWidget(body)
        columns = QHBoxLayout(body)
        columns.setContentsMargins(5, 5, 5, 5)
        columns.setSpacing(10)
        left = QVBoxLayout()
        left.setSpacing(10)
        columns.addLayout(left, 6)
        right = QVBoxLayout()
        columns.addLayout(right, 5)

        # Linke GroupBox 1: Datum der Gültigkeit.
        expiry_group = QGroupBox("Gültigkeit Datum", body)
        expiry_group.setObjectName("installerValidityDateGroup")
        expiry_layout = QVBoxLayout(expiry_group)
        expiry_layout.setContentsMargins(9, 17, 8, 9)
        expiry_layout.setSpacing(7)
        self.expiry_enabled = QCheckBox("Datum des Auslaufen", expiry_group)
        self.expiry_enabled.setChecked(values["expiry_enabled"])
        expiry_layout.addWidget(self.expiry_enabled)
        self.expiry_mode_group = QButtonGroup(self)
        self.expiry_radios = {}
        for key, title, widget, suffix in (
            ("absolute", "Absolutes Datum", "date", None),
            ("after_creation", "Zerfällt", "days_after_creation", "Tage nach Erstellung"),
            ("after_first_start", "Zerfällt", "days_after_first_start",
             "Tage nach ersten Start"),
        ):
            line = QHBoxLayout()
            line.setContentsMargins(12, 0, 0, 0)
            line.setSpacing(5)
            radio = QRadioButton(title, expiry_group)
            self.expiry_radios[key] = radio
            self.expiry_mode_group.addButton(radio)
            line.addWidget(radio)
            if widget == "date":
                self.absolute_date_edit = QDateEdit(expiry_group)
                self.absolute_date_edit.setObjectName("installerValidityAbsoluteDate")
                self.absolute_date_edit.setCalendarPopup(True)
                self.absolute_date_edit.setDisplayFormat("dd.MM.yyyy")
                previous_date = QDate.fromString(values["absolute_date"], Qt.ISODate)
                self.absolute_date_edit.setDate(
                    previous_date if previous_date.isValid() else QDate.currentDate())
                line.addWidget(self.absolute_date_edit, 1)
            else:
                spin = QSpinBox(expiry_group)
                spin.setObjectName("installerValidity" + widget.title().replace("_", ""))
                spin.setRange(1, 100000)
                spin.setValue(values[widget])
                if widget == "days_after_creation":
                    self.days_after_creation_spin = spin
                else:
                    self.days_after_start_spin = spin
                line.addWidget(spin)
                line.addWidget(QLabel(suffix, expiry_group), 1)
            expiry_layout.addLayout(line)
        self.expiry_radios[values["expiry_mode"]].setChecked(True)
        self.expiry_registry_checkbox = QCheckBox(
            "Abbrechen wenn Registry nicht schreibar", expiry_group)
        self.expiry_registry_checkbox.setChecked(values["expiry_abort_on_registry_error"])
        expiry_layout.addWidget(self.expiry_registry_checkbox)
        self.show_remaining_days_checkbox = QCheckBox("Zeige Rest-Tage an", expiry_group)
        self.show_remaining_days_checkbox.setChecked(values["show_remaining_days"])
        expiry_layout.addWidget(self.show_remaining_days_checkbox)
        left.addWidget(expiry_group)

        # Linke GroupBox 2: Installations-Zähler.
        counter_group = QGroupBox("Zerfall - Zähler", body)
        counter_group.setObjectName("installerValidityCounterGroup")
        counter_layout = QVBoxLayout(counter_group)
        counter_layout.setContentsMargins(9, 17, 8, 9)
        counter_layout.setSpacing(7)
        self.counter_enabled = QCheckBox("Aktivieren", counter_group)
        self.counter_enabled.setChecked(values["counter_enabled"])
        counter_layout.addWidget(self.counter_enabled)
        self.counter_mode_group = QButtonGroup(self)
        self.counter_radios = {}
        for key, field, suffix in (
            ("system", "max_system_installations", "Installationen auf System"),
            ("user", "max_user_installations", "Benutzer-Installationen"),
        ):
            line = QHBoxLayout()
            line.setContentsMargins(12, 0, 0, 0)
            line.setSpacing(5)
            radio = QRadioButton("Limit bis", counter_group)
            self.counter_radios[key] = radio
            self.counter_mode_group.addButton(radio)
            line.addWidget(radio)
            spin = QSpinBox(counter_group)
            spin.setRange(1, 100000)
            spin.setValue(values[field])
            if key == "system":
                self.max_system_installations_spin = spin
            else:
                self.max_user_installations_spin = spin
            line.addWidget(spin)
            line.addWidget(QLabel(suffix, counter_group), 1)
            counter_layout.addLayout(line)
        self.counter_radios[values["counter_mode"]].setChecked(True)
        self.counter_registry_checkbox = QCheckBox(
            "Abbrechen, wenn Registry nicht schreibbar.", counter_group)
        self.counter_registry_checkbox.setChecked(values["counter_abort_on_registry_error"])
        counter_layout.addWidget(self.counter_registry_checkbox)
        self.show_remaining_count_checkbox = QCheckBox(
            "Nummer bis Limit anzeigen", counter_group)
        self.show_remaining_count_checkbox.setChecked(values["show_remaining_count"])
        counter_layout.addWidget(self.show_remaining_count_checkbox)
        left.addWidget(counter_group)
        left.addStretch(1)

        # Rechte GroupBox: Produktidentifikation und Kontakte.
        settings_group = QGroupBox("Einstellungen", body)
        settings_group.setObjectName("installerValiditySettingsGroup")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(9, 17, 9, 9)
        settings_layout.setSpacing(7)
        settings_layout.addWidget(QLabel("Produkt Identifikation", settings_group))
        self.product_id_edit = QLineEdit(settings_group)
        self.product_id_edit.setObjectName("installerValidityProductUuid")
        self.product_id_edit.setText(values["product_id"])
        settings_layout.addWidget(self.product_id_edit)
        self.generate_product_id_button = QPushButton("Erstellen", settings_group)
        self.generate_product_id_button.setObjectName("installerGenerateProductUuid")
        self.generate_product_id_button.clicked.connect(self._generate_product_id)
        settings_layout.addWidget(self.generate_product_id_button, 0, Qt.AlignLeft)
        self.contact_info_checkbox = QCheckBox("Kontaktinfos anzeigen", settings_group)
        self.contact_info_checkbox.setChecked(values["show_contact_info"])
        settings_layout.addWidget(self.contact_info_checkbox)
        self.contact_edits = {}
        for field, caption in (
            ("contact_name", "Kontakt-Name:"),
            ("contact_website", "Webseite"),
            ("contact_email", "Kontakt E-Mail"),
            ("contact_phone", "Kontakt Telefon"),
        ):
            settings_layout.addWidget(QLabel(caption, settings_group))
            field_edit = QLineEdit(settings_group)
            field_edit.setObjectName("installerValidity" + field.title().replace("_", ""))
            field_edit.setText(values[field])
            self.contact_edits[field] = field_edit
            settings_layout.addWidget(field_edit)
        right.addWidget(settings_group)
        right.addStretch(1)

        self.expiry_enabled.toggled.connect(self._update_validity_controls)
        self.counter_enabled.toggled.connect(self._update_validity_controls)
        self.contact_info_checkbox.toggled.connect(self._update_validity_controls)
        for radio in list(self.expiry_radios.values()) + list(self.counter_radios.values()):
            radio.toggled.connect(self._update_validity_controls)
        self._update_validity_controls()

    def _update_validity_controls(self, *_args):
        expiration = self.expiry_enabled.isChecked()
        for radio in self.expiry_radios.values():
            radio.setEnabled(expiration)
        self.absolute_date_edit.setEnabled(expiration and self.expiry_radios["absolute"].isChecked())
        self.days_after_creation_spin.setEnabled(
            expiration and self.expiry_radios["after_creation"].isChecked())
        self.days_after_start_spin.setEnabled(
            expiration and self.expiry_radios["after_first_start"].isChecked())
        self.expiry_registry_checkbox.setEnabled(expiration)
        self.show_remaining_days_checkbox.setEnabled(expiration)
        counting = self.counter_enabled.isChecked()
        for radio in self.counter_radios.values():
            radio.setEnabled(counting)
        self.max_system_installations_spin.setEnabled(
            counting and self.counter_radios["system"].isChecked())
        self.max_user_installations_spin.setEnabled(
            counting and self.counter_radios["user"].isChecked())
        self.counter_registry_checkbox.setEnabled(counting)
        self.show_remaining_count_checkbox.setEnabled(counting)
        for edit in self.contact_edits.values():
            edit.setEnabled(self.contact_info_checkbox.isChecked())

    def _generate_product_id(self):
        # Keine Registry-Schreiboperation im Editor: UUID nur projektseitig erzeugen.
        import uuid
        self.product_id_edit.setText(str(uuid.uuid4()))

    def _collect_validity_settings(self):
        return {
            "expiry_enabled": self.expiry_enabled.isChecked(),
            "expiry_mode": next(key for key, radio in self.expiry_radios.items()
                                if radio.isChecked()),
            "absolute_date": self.absolute_date_edit.date().toString(Qt.ISODate),
            "days_after_creation": self.days_after_creation_spin.value(),
            "days_after_first_start": self.days_after_start_spin.value(),
            "expiry_abort_on_registry_error": self.expiry_registry_checkbox.isChecked(),
            "show_remaining_days": self.show_remaining_days_checkbox.isChecked(),
            "counter_enabled": self.counter_enabled.isChecked(),
            "counter_mode": next(key for key, radio in self.counter_radios.items()
                                 if radio.isChecked()),
            "max_system_installations": self.max_system_installations_spin.value(),
            "max_user_installations": self.max_user_installations_spin.value(),
            "counter_abort_on_registry_error": self.counter_registry_checkbox.isChecked(),
            "show_remaining_count": self.show_remaining_count_checkbox.isChecked(),
            "product_id": self.product_id_edit.text().strip(),
            "show_contact_info": self.contact_info_checkbox.isChecked(),
            **{name: edit.text() for name, edit in self.contact_edits.items()},
        }

    def _tab_changed(self, index):
        for button in self.list_buttons:
            button.setVisible(index == 0)

    def _current_row(self):
        selected = self.lists_table.selectionModel().selectedRows()
        return selected[0].row() if selected else -1

    def _update_list_table(self, row=None):
        self.lists_table.setRowCount(len(self.serial_lists))
        for i, entry in enumerate(self.serial_lists):
            for j, value in enumerate((entry["name"], str(len(entry["serial_numbers"])),
                                       ", ".join(entry["configurations"]))):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.lists_table.setItem(i, j, item)
        if row is not None and 0 <= row < len(self.serial_lists):
            self.lists_table.selectRow(row)

    def _open_properties(self, entry=None, *, excluding_row=None):
        names = [item["name"] for index, item in enumerate(self.serial_lists)
                 if index != excluding_row]
        child = InstallerSerialListPropertiesDialog(
            entry, self, dark_mode=self._dark_mode,
            help_callback=self.help_callback, existing_names=names)
        if child.exec_() != QDialog.Accepted:
            return None
        return child.result_entry

    def _add_list(self):
        entry = self._open_properties()
        if entry is not None:
            self.serial_lists.append(entry)
            self._update_list_table(len(self.serial_lists) - 1)

    def _edit_list(self, *_args):
        index = self._current_row()
        if index < 0:
            return
        entry = self._open_properties(self.serial_lists[index], excluding_row=index)
        if entry is not None:
            self.serial_lists[index] = entry
            self._update_list_table(index)

    def _remove_list(self):
        index = self._current_row()
        if index >= 0:
            del self.serial_lists[index]
            self._update_list_table(min(index, len(self.serial_lists) - 1))

    def _accept_changes(self):
        try:
            self.serialized = encode_security_settings(
                {"serial_lists": self.serial_lists,
                 "validity": self._collect_validity_settings()})
        except (ValueError, TypeError) as error:
            installer_themed_warning(self, "Sicherheit", str(error),
                                     dark_mode=self._dark_mode)
            return
        self.accept()

    def _help(self):
        if callable(self.help_callback):
            self.help_callback("Sicherheit")

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


def installer_themed_warning(parent, title, text, *, dark_mode=False):
    """QMessageBox im Installer-Theme statt ungestylter nativer Meldung."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.Ok)
    # Nutzt die identischen Theme-Regeln des InstallerThemedDialog.
    theme = InstallerThemedDialog(parent, dark_mode=dark_mode)
    box.setStyleSheet(theme.styleSheet() + "\nQMessageBox { background: " +
        ("#202329" if dark_mode else "#f5f5f5") + "; }" )
    box.setObjectName("installerThemedWarning")
    box.setWindowFlags(box.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(0, lambda: _set_windows_dark_titlebar(box, dark_mode))
    return box.exec_()
