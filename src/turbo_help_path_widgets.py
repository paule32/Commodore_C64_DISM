"""Stage 685: dedicated project-scoped Turbo Help search directories."""
from __future__ import annotations

from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAbstractItemView, QCheckBox, QFileDialog, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QPushButton, QVBoxLayout)


class TurboHelpPathGroup(QGroupBox):
    def __init__(self, owner, target, parent=None):
        super().__init__('Turbo Hilfe:', parent)
        self.owner, self.target = owner, target
        self.setObjectName(f'compiler_{target}_dbase_turbo_help_paths_group')
        self._updating = False
        self._relative = True
        layout = QVBoxLayout(self)
        self.relative_box = QCheckBox('relative Pfade', self)
        layout.addWidget(self.relative_box)
        row = QHBoxLayout()
        row.addWidget(QLabel('Verzeichnis:', self))
        self.edit = QLineEdit(self)
        self.edit.setObjectName(f'compiler_{target}_dbase_turbo_help_input_edit')
        browse = QPushButton('...', self)
        browse.setFixedWidth(42)
        row.addWidget(self.edit, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.items = QListWidget(self)
        self.items.setObjectName(f'compiler_{target}_dbase_turbo_help_input_list')
        self.items.setSelectionMode(QAbstractItemView.SingleSelection)
        self.items.setMinimumHeight(80)
        row.addWidget(self.items, 1)
        buttons = QVBoxLayout()
        actions = {}
        for title in ('Hinzufügen', 'Löschen', 'Alle löschen', '↑', '↓'):
            button = QPushButton(title, self)
            buttons.addWidget(button)
            actions[title] = button
        buttons.addStretch(1)
        row.addLayout(buttons)
        layout.addLayout(row)
        browse.clicked.connect(self._browse)
        self.edit.returnPressed.connect(self._add)
        actions['Hinzufügen'].clicked.connect(self._add)
        actions['Löschen'].clicked.connect(self._delete)
        actions['Alle löschen'].clicked.connect(self._clear)
        actions['↑'].clicked.connect(lambda _v=False: self._move(-1))
        actions['↓'].clicked.connect(lambda _v=False: self._move(1))
        self.relative_box.toggled.connect(self._relative_toggled)

    def _absolute(self, path):
        return self.owner._project_windows_absolute_directory(path)

    def _display(self, path):
        return self.owner._project_windows_display_directory(path, relative=self._relative)

    def paths(self):
        return tuple(str(self.items.item(i).data(Qt.UserRole)) for i in range(self.items.count()))

    def set_values(self, paths, relative=True):
        self._updating = True
        try:
            self._relative = bool(relative)
            self.relative_box.setChecked(self._relative)
            self.relative_box.setText('relative Pfade' if self._relative else 'absolute Pfade')
            self.items.clear()
            for path in paths:
                if path:
                    resolved = self._absolute(path)
                    item = QListWidgetItem(self._display(resolved))
                    item.setData(Qt.UserRole, resolved)
                    self.items.addItem(item)
        finally:
            self._updating = False

    def _changed(self):
        if not self._updating:
            self.owner.set_project_turbo_help_search_paths(self.target, self.paths())

    def _browse(self):
        selected = QFileDialog.getExistingDirectory(
            self, 'Turbo-Hilfe-Verzeichnis auswählen',
            self._absolute(self.edit.text()) if self.edit.text().strip() else str(self.owner.current_directory))
        if selected:
            self.edit.setText(self._display(self._absolute(selected)))
            self._add()

    def _add(self):
        raw = self.edit.text().strip()
        if not raw:
            return
        resolved = self._absolute(raw)
        if resolved.casefold() not in {p.casefold() for p in self.paths()}:
            item = QListWidgetItem(self._display(resolved))
            item.setData(Qt.UserRole, resolved)
            self.items.addItem(item)
            self.items.setCurrentItem(item)
            self._changed()
        self.edit.clear()

    def _delete(self):
        row = self.items.currentRow()
        if row >= 0:
            self.items.takeItem(row)
            self._changed()

    def _clear(self):
        if self.items.count():
            self.items.clear()
            self._changed()

    def _move(self, offset):
        src = self.items.currentRow()
        dest = src + offset
        if src < 0 or not 0 <= dest < self.items.count():
            return
        item = self.items.takeItem(src)
        self.items.insertItem(dest, item)
        self.items.setCurrentRow(dest)
        self._changed()

    def _relative_toggled(self, enabled):
        if self._updating:
            return
        self._relative = bool(enabled)
        self.relative_box.setText('relative Pfade' if enabled else 'absolute Pfade')
        for i in range(self.items.count()):
            item = self.items.item(i)
            item.setText(self._display(item.data(Qt.UserRole)))
        self.owner.set_project_turbo_help_relative(self.target, bool(enabled))
