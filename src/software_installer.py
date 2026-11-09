"""Stage 554: Software Installer als ein einziges IDE-QDockWidget.

Das eingebettete QWidget enthaelt eine feste Toolbar und einen horizontalen
QSplitter mit Komponenten links und Archiv-/Extern-Tabellen rechts.
Keine verschachtelten QMainWindows oder QDockWidgets.
"""
from __future__ import annotations

from pathlib import Path
import re

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QHeaderView, QHBoxLayout,
    QLabel, QLineEdit, QMenu, QMessageBox, QPlainTextEdit, QSplitter,
    QPushButton, QScrollArea, QSizePolicy, QStyle, QTabWidget, QTableWidget,
    QTableWidgetItem, QToolBar, QToolButton, QVBoxLayout, QWidget,
)
from software_installer_model import (
    INSTALLER_COLUMNS, INSTALLER_FILTERS, INSTALLER_GROUPS,
    InstallerEntry, InstallerProject, InstallerProjectRegistry,
    installer_registry_path, entry_visible,
)
from software_installer_dialogs import (
    InstallerProjectStartDialog, InstallerGeneralInfoDialog,
    InstallerPlatformDialog, InstallerSourcesDialog, InstallerAppearanceDialog,
    InstallerProjectThemeDialog, InstallerLanguagesDialog, InstallerRequirementsDialog,
    InstallerDestinationDialog, InstallerProjectNameDialog,
)


class InstallerCollapsiblePanel(QFrame):
    """Container / Ueberschrift / Inhalt: exakt drei logisch getrennte Panels."""

    def __init__(self, title: str, captions, callback, parent=None):
        super().__init__(parent)
        self.setObjectName("installerPanelContainer")
        self.title_text = title
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        self.header = QFrame(self)
        self.header.setObjectName("installerPanelHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(9, 7, 6, 7)
        self.heading = QLabel(title, self.header)
        self.heading.setObjectName("installerPanelHeading")
        header_layout.addWidget(self.heading, 1)
        self.toggle_button = QToolButton(self.header)
        self.toggle_button.setObjectName("installerPanelToggle")
        self.toggle_button.setArrowType(Qt.UpArrow)
        self.toggle_button.setToolTip(title + " einklappen")
        self.toggle_button.setAutoRaise(True)
        self.toggle_button.clicked.connect(self.toggle)
        header_layout.addWidget(self.toggle_button, 0, Qt.AlignRight)
        outer.addWidget(self.header)

        self.content = QFrame(self)
        self.content.setObjectName("installerPanelContent")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(6, 6, 6, 8)
        content_layout.setSpacing(4)
        for caption in captions:
            button = QPushButton(caption, self.content)
            button.setObjectName("installerPanelButton")
            button.setMinimumHeight(27)
            standard_icon = (QStyle.SP_DirIcon if "Pfad" in caption or "Package" in caption
                             else QStyle.SP_FileIcon)
            button.setIcon(self.style().standardIcon(standard_icon))
            button.setToolTip(caption)
            button.clicked.connect(lambda _checked=False, name=caption: callback(name))
            content_layout.addWidget(button)
        outer.addWidget(self.content)
        self._expanded = True

    def toggle(self, _checked=False):
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        self.toggle_button.setArrowType(Qt.UpArrow if self._expanded else Qt.DownArrow)
        self.toggle_button.setToolTip(
            self.title_text + (" einklappen" if self._expanded else " aufklappen")
        )


class InstallerTable(QTableWidget):
    """Editierbare Tabelle mit Zeilen-Hinzufuegen/-Loeschen via Kontextmenue."""

    def __init__(self, tab_key: str, owner, parent=None):
        super().__init__(0, len(INSTALLER_COLUMNS), parent)
        self.tab_key = tab_key
        self.owner = owner
        self.setObjectName("installerTable")
        self.setHorizontalHeaderLabels(list(INSTALLER_COLUMNS))
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.SelectedClicked
        )
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for index, width in enumerate((165, 140, 260, 86, 126, 110, 95, 110, 100)):
            self.setColumnWidth(index, width)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemChanged.connect(self._on_item_changed)
        self._loading = False

    def _show_context_menu(self, position):
        menu = QMenu(self)
        add_action = menu.addAction("Zeile hinzufügen")
        add_files = menu.addAction("Datei hinzufügen …")
        menu.addSeparator()
        remove_action = menu.addAction("Ausgewählte Zeilen löschen")
        remove_action.setEnabled(bool(self.selectionModel().selectedRows()))
        chosen = menu.exec_(self.viewport().mapToGlobal(position))
        if chosen is add_action:
            self.owner.add_blank_row(self.tab_key)
        elif chosen is add_files:
            self.owner.add_files(self.tab_key)
        elif chosen is remove_action:
            self.owner.delete_selected_rows(self.tab_key)

    def _on_item_changed(self, item):
        if self._loading:
            return
        self.owner.update_row(self.tab_key, item.row())

    def populate(self, entries):
        self._loading = True
        try:
            self.setRowCount(len(entries))
            for row, entry in enumerate(entries):
                for column, value in enumerate(entry.values()):
                    old = self.item(row, column)
                    if old is None:
                        old = QTableWidgetItem()
                        self.setItem(row, column, old)
                    old.setText(str(value))
                    old.setData(Qt.UserRole, row)
        finally:
            self._loading = False


class SoftwareInstallerWorkbench(QWidget):
    """Ein Dockinhalt: feste Werkzeugleiste ueber einem horizontalen Splitter."""

    project_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("softwareInstallerWorkbench")
        self.project = InstallerProject()
        self.project_filename = None
        self.registry = InstallerProjectRegistry()
        self.needs_save_as = True
        self.dirty = True
        self._registry_pending = False
        self._dark_mode = False
        self._initial_split_applied = False

        # QToolBar bleibt innerhalb des einzigen aeusseren IDE-Docks fixiert.
        # Anders als bei QMainWindow kann sie nicht verschoben/ausgedockt werden.
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.filter_bar = QToolBar("Software Installer Filter", self)
        self.filter_bar.setObjectName("softwareInstallerFilterBar")
        self.filter_bar.setMovable(False)
        self.filter_bar.setFloatable(False)
        self.filter_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.filter_bar.addWidget(QLabel("Filter:  ", self.filter_bar))
        self.filter_combo = QComboBox(self.filter_bar)
        self.filter_combo.setObjectName("softwareInstallerFilter")
        for label, value in INSTALLER_FILTERS:
            self.filter_combo.addItem(label, value)
        self.filter_combo.setMinimumWidth(190)
        self.filter_bar.addWidget(self.filter_combo)
        self.filter_bar.addSeparator()
        self.project_caption = QLabel("Projekt: Unbenannt", self.filter_bar)
        self.project_caption.setObjectName("softwareInstallerProjectCaption")
        self.filter_bar.addWidget(self.project_caption)
        self.filter_bar.addSeparator()
        open_action = self.filter_bar.addAction("Installer Projekt öffnen ...")
        open_action.setObjectName("softwareInstallerOpenAction")
        open_action.triggered.connect(self.open_configuration)
        save_action = self.filter_bar.addAction("Installer Projekt speichern ...")
        save_action.setObjectName("softwareInstallerSaveAction")
        save_action.triggered.connect(self.save_configuration)
        self.open_button = self.filter_bar.widgetForAction(open_action)
        self.save_button = self.filter_bar.widgetForAction(save_action)
        if self.open_button is not None:
            self.open_button.setObjectName("softwareInstallerProjectOpenButton")
            self.open_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        if self.save_button is not None:
            self.save_button.setObjectName("softwareInstallerProjectSaveButton")
            self.save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        main_layout.addWidget(self.filter_bar, 0)
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)

        # Beide Seiten sind Widgets, KEINE weiteren Dockfenster. Nur das
        # aeussere IDE-Dock kann vom Benutzer verschoben/geschlossen werden.
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setObjectName("softwareInstallerSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(6)
        main_layout.addWidget(self.splitter, 1)

        # Links: Scrollbereich mit den vier aufklappbaren Komponentengruppen.
        self.files_scroll = QScrollArea(self.splitter)
        self.files_scroll.setObjectName("softwareInstallerFilesScroll")
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setFrameShape(QFrame.NoFrame)
        self.files_scroll.setMinimumWidth(160)
        files_body = QWidget(self.files_scroll)
        files_body.setObjectName("softwareInstallerFilesBody")
        files_layout = QVBoxLayout(files_body)
        files_layout.setContentsMargins(5, 5, 5, 5)
        files_layout.setSpacing(7)
        files_heading = QLabel("Dateien", files_body)
        files_heading.setObjectName("softwareInstallerFilesTitle")
        files_layout.addWidget(files_heading)
        self.panels = {}
        for title, buttons in INSTALLER_GROUPS:
            panel = InstallerCollapsiblePanel(title, buttons, self.handle_panel_action, files_body)
            files_layout.addWidget(panel)
            self.panels[title] = panel
        files_layout.addStretch(1)
        self.files_scroll.setWidget(files_body)
        self.splitter.addWidget(self.files_scroll)

        # Rechts: unveraendertes TabWidget mit Archiv- und Extern-Tabelle.
        self.tabs = QTabWidget(self.splitter)
        self.tabs.setObjectName("softwareInstallerTabs")
        self.tabs.setMinimumWidth(260)
        self.tables = {}
        for title, key in (("Archiv", "archive"), ("Extern", "external")):
            table = InstallerTable(key, self, self.tabs)
            self.tables[key] = table
            self.tabs.addTab(table, title)
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)

        self.refresh_tables()
        self.set_dark_mode(False)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._initial_split_applied:
            QTimer.singleShot(0, self.apply_initial_widths)

    def apply_initial_widths(self):
        """Einmalig ca. 1/4 : 3/4; spaetere Nutzer-Splitterposition behalten."""
        if self._initial_split_applied:
            return
        width = self.splitter.width()
        if width < 450 or not self.isVisible():
            return  # Erst nach dem Platzieren/Expandieren des aeusseren Docks.
        left = max(self.files_scroll.minimumWidth(), width // 4)
        right = width - left - self.splitter.handleWidth()
        if right < self.tabs.minimumWidth():
            right = self.tabs.minimumWidth()
            left = max(self.files_scroll.minimumWidth(), width - right - self.splitter.handleWidth())
        self.splitter.setSizes([left, right])
        self._initial_split_applied = True

    def current_tab_key(self):
        return "archive" if self.tabs.currentIndex() == 0 else "external"

    def refresh_tables(self):
        for key, table in self.tables.items():
            table.populate(self.project.entries[key])
        self.apply_filter()

    def apply_filter(self, _index=None):
        filter_key = self.filter_combo.currentData() or "all"
        if filter_key == "archive":
            self.tabs.setCurrentIndex(0)
        elif filter_key == "external":
            self.tabs.setCurrentIndex(1)
        for key, table in self.tables.items():
            for row, entry in enumerate(self.project.entries[key]):
                table.setRowHidden(
                    row, not entry_visible(filter_key, key, entry.status)
                )

    def update_row(self, tab_key, row):
        table = self.tables[tab_key]
        entries = self.project.entries[tab_key]
        if 0 <= row < len(entries):
            values = [table.item(row, col).text() if table.item(row, col) else ""
                      for col in range(len(INSTALLER_COLUMNS))]
            entries[row].update_from_values(values)
            self.apply_filter()
            self._mark_dirty()

    def add_blank_row(self, tab_key=None):
        key = tab_key or self.current_tab_key()
        self.project.entries[key].append(InstallerEntry())
        self._mark_dirty()
        self.refresh_tables()
        row = len(self.project.entries[key]) - 1
        table = self.tables[key]
        table.setCurrentCell(row, 0)
        table.scrollToItem(table.item(row, 0))
        table.editItem(table.item(row, 0))

    def add_files(self, tab_key=None):
        key = tab_key or self.current_tab_key()
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "Dateien für den Installer auswählen", str(Path.home()),
            "Alle Dateien (*)"
        )
        if filenames:
            if self.project.add_paths(key, filenames):
                self._mark_dirty()
                self.refresh_tables()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Verzeichnis für den Installer auswählen", str(Path.home())
        )
        if folder:
            if self.project.add_paths(self.current_tab_key(), [folder]):
                self._mark_dirty()
                self.refresh_tables()

    def delete_selected_rows(self, tab_key=None):
        key = tab_key or self.current_tab_key()
        table = self.tables[key]
        indices = [index.row() for index in table.selectionModel().selectedRows()]
        if indices:
            if self.project.delete_rows(key, indices):
                self._mark_dirty()
                self.refresh_tables()

    def show_file_properties(self):
        key = self.current_tab_key()
        table = self.tables[key]
        row = table.currentRow()
        if row < 0 or row >= len(self.project.entries[key]):
            QMessageBox.information(self, "Datei Eigenschaften", "Bitte zunächst ein Element auswählen.")
            return
        entry = self.project.entries[key][row]
        dialog = QDialog(self)
        dialog.setWindowTitle("Datei Eigenschaften")
        layout = QFormLayout(dialog)
        edits = {}
        for label, key_name in (("Name", "name"), ("Ziel", "target"),
                                ("Lokaler Pfad", "local_path"),
                                ("Datei Version", "file_version"),
                                ("Package", "package"), ("Short Cut", "shortcut")):
            edit = QLineEdit(getattr(entry, key_name), dialog)
            layout.addRow(label, edit)
            edits[key_name] = edit
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        if dialog.exec_() == QDialog.Accepted:
            for key_name, edit in edits.items():
                setattr(entry, key_name, edit.text())
            self._mark_dirty()
            self.refresh_tables()

    def edit_configuration(self, name):
        """Eingaben fuer Settings/Bildschirme/Aktionen speichern (noch kein Builder)."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Software Installer – " + name)
        dialog.resize(520, 300)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Konfiguration / Inhalt für „" + name + "“:", dialog))
        editor = QPlainTextEdit(dialog)
        editor.setObjectName("softwareInstallerConfigEditor")
        editor.setPlainText(self.project.sections.get(name, ""))
        layout.addWidget(editor, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() == QDialog.Accepted:
            if self.project.sections.get(name, "") != editor.toPlainText():
                self.project.sections[name] = editor.toPlainText()
                self._mark_dirty()

    def handle_panel_action(self, name):
        handlers = {
            "Datei hinzufügen": self.add_files,
            "Pfad hinzufügen": self.add_folder,
            "Elemente Löschen": self.delete_selected_rows,
            "Datei Eigenschaften": self.show_file_properties,
        }
        action = handlers.get(name)
        if action is not None:
            action()
        else:
            self.edit_configuration(name)

    def _mark_dirty(self):
        self.dirty = True
        self._update_project_caption()
        self.project_changed.emit()

    def _update_project_caption(self):
        name = str(self.project.name or "Unbenannt")
        self.project_caption.setText("Projekt: " + name + (" *" if self.dirty else ""))
        dock = self.parentWidget()
        if dock is not None and hasattr(dock, "setWindowTitle"):
            dock.setWindowTitle("Software Installer – " + name + (" *" if self.dirty else ""))

    def new_unnamed_project(self):
        """Abbruch/Neuanlage: kein bisheriger Dateipfad darf wiederverwendet werden."""
        self.project = InstallerProject()
        self.project_filename = None
        self.needs_save_as = True
        self._registry_pending = False
        self.dirty = True
        self.refresh_tables()
        self._update_project_caption()
        self.project_changed.emit()

    def _load_project_file(self, path):
        """Projekt erst nach erfolgreicher Dateipruefung umschalten."""
        loaded = InstallerProject.load(str(path))
        if loaded.name == "Unbenannt":
            loaded.name = Path(path).name.removesuffix(".installer.json")
        self.project = loaded
        self.project_filename = str(Path(path).expanduser().resolve())
        self.needs_save_as = False
        self.dirty = False
        self._registry_pending = False
        self.refresh_tables()
        self._update_project_caption()
        self.project_changed.emit()
        # Ein durch Suchen geladenes Projekt in die kuenftige Liste aufnehmen.
        try:
            self.registry.register(self.project_filename, self.project)
        except (OSError, ValueError, TypeError) as error:
            self._registry_pending = True
            QMessageBox.warning(self, "Installer-Projektliste",
                                "Projekt wurde geoeffnet, aber nicht in die Liste aufgenommen:\n" + str(error))

    def _show_help_topic(self, topic):
        main_window = self.window()
        installer_help = getattr(main_window, "show_software_installer_help", None)
        show_help = getattr(main_window, "show_chm_viewer", None)
        if callable(installer_help):
            installer_help(topic)
        elif callable(show_help):
            show_help(context_word=topic)
        else:
            QMessageBox.information(self, "Installer-Hilfe",
                "Der CHM-Viewer ist in diesem Fenster nicht verfügbar.\nThema: " + topic)

    def _run_wizard(self):
        """Sieben Wizard-Seiten mit persistentem Zustand beim Vor-/Zurueckblaettern.

        Ein Abbruch erzeugt ausschliesslich das ungespeicherte Projekt
        "Unbenannt". Erst nach Seite 7 werden alle Werte in general uebernommen.
        """
        values = dict(self.project.general)
        page_classes = (
            InstallerGeneralInfoDialog,
            InstallerPlatformDialog,
            InstallerSourcesDialog,
            InstallerAppearanceDialog,
            InstallerProjectThemeDialog,
            InstallerLanguagesDialog,
            InstallerRequirementsDialog,
        )
        page = 0
        while page < len(page_classes):
            dialog = page_classes[page](
                self, dark_mode=self._dark_mode, values=values,
                help_callback=self._show_help_topic)
            result = dialog.exec_()
            if result == QDialog.Rejected:
                self.new_unnamed_project()
                return False
            # Auch bei Zurueck die gerade bearbeiteten Felder sichern.
            values.update(dialog.values())
            if result == dialog.BACK:
                page = max(0, page - 1)
                continue
            if result != QDialog.Accepted:
                self.new_unnamed_project()
                return False
            page += 1
        self.project.general = values
        self._mark_dirty()
        return True

    def _confirm_replace_project(self):
        """Keine editierten Projektinhalte beim Oeffnen still verlieren."""
        has_content = bool(
            self.project_filename or self.project.general or self.project.sections
            or self.project.entries["archive"] or self.project.entries["external"]
        )
        if not self.dirty or not has_content:
            return True
        choice = QMessageBox.question(
            self, "Software Installer",
            "Das aktuelle Installer-Projekt wurde geändert. Vor dem Öffnen speichern?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if choice == QMessageBox.Cancel:
            return False
        if choice == QMessageBox.Save:
            return bool(self.save_configuration())
        return True

    def open_configuration(self, _checked=False):
        if not self._confirm_replace_project():
            return False
        dialog = InstallerProjectStartDialog(
            self.registry, self, dark_mode=self._dark_mode,
            help_callback=self._show_help_topic)
        choice = dialog.exec_()
        if choice != QDialog.Accepted:
            # Explizite Vorgabe: Abbrechen legt ein neues Unbenannt-Projekt an.
            self.new_unnamed_project()
            return False
        if dialog.existing_radio.isChecked():
            try:
                self._load_project_file(dialog.selected_path)
            except (OSError, ValueError, TypeError, KeyError) as error:
                QMessageBox.warning(self, "Installer-Projekt",
                                    "Öffnen fehlgeschlagen:\n" + str(error))
                return False
            return True
        self.new_unnamed_project()
        if dialog.wizard_check.isChecked():
            return self._run_wizard()
        return True

    @staticmethod
    def _safe_project_stem(name):
        """Projektname ohne Windows-reservierte Zeichen und Geraetenamen."""
        name = str(name).strip().rstrip(". ")
        if not name or re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
            raise ValueError("Der Projektname enthaelt ungueltige Zeichen.")
        if name.partition(".")[0].upper() in {
            "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10))}:
            raise ValueError("Der Projektname ist unter Windows reserviert.")
        return name

    def save_configuration(self, _checked=False):
        filename = self.project_filename
        new_name = None
        if self.needs_save_as or not filename:
            name_dialog = InstallerProjectNameDialog(
                self, dark_mode=self._dark_mode,
                name=self.project.general.get("product", "") or "Unbenannt")
            if name_dialog.exec_() != QDialog.Accepted:
                return False
            try:
                new_name = self._safe_project_stem(name_dialog.name())
            except ValueError as error:
                QMessageBox.warning(self, "Projektname", str(error))
                return False
            target_directory = installer_registry_path().parent / "installer_projects"
            filename = str(target_directory / (new_name + ".installer.json"))
            if Path(filename).exists() and Path(filename).resolve() != Path(self.project_filename or "").resolve():
                QMessageBox.warning(self, "Projektname",
                                    "Ein Projekt mit diesem Dateinamen existiert bereits.")
                return False
        old_name = self.project.name
        if new_name is not None:
            self.project.name = new_name
        try:
            self.project.save(str(filename))
        except (OSError, ValueError, UnicodeError) as error:
            self.project.name = old_name
            QMessageBox.warning(self, "Installer-Projekt",
                                "Speichern fehlgeschlagen:\n" + str(error))
            return False
        self.project_filename = str(Path(filename).resolve())
        self.needs_save_as = False
        self.dirty = False
        self._registry_pending = False
        try:
            self.registry.register(self.project_filename, self.project)
        except (OSError, ValueError, TypeError) as error:
            self._registry_pending = True
            QMessageBox.warning(self, "Installer-Projektliste",
                                "Projektdatei gespeichert, aber die globale Projektliste konnte nicht "
                                "aktualisiert werden:\n" + str(error))
            self._update_project_caption()
            self.project_changed.emit()
            return False
        self._update_project_caption()
        self.project_changed.emit()
        return True

    def set_dark_mode(self, dark: bool):
        self._dark_mode = bool(dark)
        if dark:
            bg, card, head, fg, border, hover, alternate = (
                "#202329", "#282d36", "#343b47", "#f1f2f4", "#515b6c",
                "#3b4961", "#272f3b"
            )
        else:
            bg, card, head, fg, border, hover, alternate = (
                "#f5f5f5", "#ffffff", "#e8e9ec", "#20242b", "#bfc4cc",
                "#dee8f3", "#f4f7fb"
            )
        self.setStyleSheet(f"""
            QWidget#softwareInstallerWorkbench, QWidget#softwareInstallerFilesBody {{
                background: {bg}; color: {fg}; }}
            QToolBar#softwareInstallerFilterBar {{ background: {card}; color: {fg};
                border: 0; border-bottom: 1px solid {border}; padding: 7px; spacing: 8px; }}
            QSplitter#softwareInstallerSplitter {{ background: {bg}; }}
            QSplitter#softwareInstallerSplitter::handle {{ background: {border}; }}
            QScrollArea#softwareInstallerFilesScroll {{ background: {bg}; border: none; }}
            QLabel#softwareInstallerFilesTitle {{ color: {fg}; font-weight: bold;
                background: {bg}; padding: 5px 8px; }}
            QFrame#installerPanelContainer {{ background: {card};
                border: 1px solid {border}; border-radius: 4px; }}
            QFrame#installerPanelHeader {{ background: {head}; border: none;
                border-bottom: 1px solid {border}; }}
            QLabel#installerPanelHeading {{ color: {fg}; font-weight: bold; border: none; }}
            QFrame#installerPanelContent {{ background: {card}; border: none; }}
            QToolButton#installerPanelToggle {{ color: {fg}; background: transparent;
                border: none; padding: 2px; }}
            QPushButton#installerPanelButton {{ color: {fg}; background: {card};
                border: 1px solid transparent; border-radius: 3px;
                padding: 5px 7px; text-align: left; }}
            QPushButton#installerPanelButton:hover {{ background: {hover};
                border: 1px solid {border}; }}
            QTableWidget#installerTable {{ background: {card}; color: {fg};
                alternate-background-color: {alternate}; gridline-color: {border};
                selection-background-color: {hover}; selection-color: {fg}; }}
            QTableWidget#installerTable QHeaderView::section {{ background: {head};
                color: {fg}; padding: 5px; border: 1px solid {border}; }}
            QTabWidget#softwareInstallerTabs::pane {{ border: 1px solid {border}; }}
            QComboBox#softwareInstallerFilter {{ color: {fg}; background: {card};
                border: 1px solid {border}; padding: 4px; }}
            QLabel#softwareInstallerProjectCaption {{ color: {fg}; background: transparent;
                padding: 0 6px; }}
            QToolButton#softwareInstallerProjectOpenButton,
            QToolButton#softwareInstallerProjectSaveButton {{
                color: {fg}; background: {card}; border: 1px solid {border};
                border-radius: 4px; padding: 5px 9px; margin: 0 2px; }}
            QToolButton#softwareInstallerProjectOpenButton:hover,
            QToolButton#softwareInstallerProjectSaveButton:hover {{
                background: {hover}; }}
            QToolButton#softwareInstallerProjectOpenButton:pressed,
            QToolButton#softwareInstallerProjectSaveButton:pressed {{
                background: {head}; }}
        """)
