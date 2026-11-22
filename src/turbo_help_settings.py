"""Turbo Help search/compressor project settings (Stage 663).

Shared between the Windows PE32 and PE64 project settings trees.  A CHM
reader uses the development paths; deployed programs use application paths.
"""
from copy import deepcopy
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QLabel,
    QLineEdit, QPushButton, QListWidget, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox, QStyle,
)

SCOPES = ('entwicklung', 'anwendung')


def default_help_settings():
    return {key: {'relative': False, 'paths': [], 'compressor': 'internal',
                  'hh_path': ''} for key in SCOPES}


def normalize_help_settings(value):
    result = default_help_settings()
    if not isinstance(value, dict):
        return result
    for key in SCOPES:
        item = value.get(key, {})
        if not isinstance(item, dict):
            continue
        paths = item.get('paths', [])
        if not isinstance(paths, list):
            paths = []
        result[key] = {
            'relative': bool(item.get('relative', False)),
            'paths': [str(p) for p in paths if str(p).strip()],
            'compressor': ('microsoft' if item.get('compressor') == 'microsoft'
                           else 'internal'),
            'hh_path': str(item.get('hh_path', '') or ''),
        }
    return result


def search_directories(settings, scope, project_path=None, executable=None):
    """Resolve configured search paths in order, avoiding process CWD."""
    entry = normalize_help_settings(settings).get(scope, {})
    base = Path(project_path).resolve().parent if project_path else None
    if scope == 'anwendung' and executable is not None:
        base = Path(executable).resolve().parent
    if base is None:
        base = Path.cwd()
    result = []
    for raw in entry.get('paths', []):
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = base / path
        path = path.resolve()
        if path not in result:
            result.append(path)
    return result


class TurboHelpSettingsPage(QWidget):
    changed = pyqtSignal(str, dict)

    def __init__(self, scope, parent=None):
        super().__init__(parent)
        if scope not in SCOPES:
            raise ValueError(scope)
        self.scope = scope
        self.project_base = None
        self._syncing = False
        self.setObjectName('project_turbo_help_' + scope)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(9)

        group = QGroupBox('Suchpfade:', self)
        group_layout = QVBoxLayout(group)
        self.relative = QCheckBox('relative Pfade', group)
        self.relative.setObjectName('turbo_help_' + scope + '_relative')
        group_layout.addWidget(self.relative)
        directory_row = QHBoxLayout()
        directory_row.addWidget(QLabel('Verzeichnis:', group))
        self.directory = QLineEdit(group)
        self.directory.setObjectName('turbo_help_' + scope + '_directory')
        directory_row.addWidget(self.directory, 1)
        self.browse_directory = QPushButton(group)
        self.browse_directory.setObjectName('turbo_help_' + scope + '_directory_browse')
        self.browse_directory.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.browse_directory.setToolTip('Verzeichnis wählen')
        directory_row.addWidget(self.browse_directory)
        group_layout.addLayout(directory_row)
        listing = QHBoxLayout()
        self.paths = QListWidget(group)
        self.paths.setObjectName('turbo_help_' + scope + '_paths')
        listing.addWidget(self.paths, 1)
        actions = QVBoxLayout()
        self.add_button = QPushButton('Hinzufügen', group)
        self.delete_button = QPushButton('Löschen', group)
        self.cancel_button = QPushButton('Abbrechen', group)
        self.up_button = QPushButton('↑', group)
        self.down_button = QPushButton('↓', group)
        self.up_button.setToolTip('Eintrag nach oben')
        self.down_button.setToolTip('Eintrag nach unten')
        for button in (self.add_button, self.delete_button, self.cancel_button,
                       self.up_button, self.down_button):
            actions.addWidget(button)
        actions.addStretch(1)
        listing.addLayout(actions)
        group_layout.addLayout(listing)
        layout.addWidget(group, 1)

        compressor = QGroupBox('Compressor', self)
        compressor_layout = QVBoxLayout(compressor)
        self.microsoft = QRadioButton('Microsoft CHM', compressor)
        self.internal = QRadioButton('internal', compressor)
        self.radio_group = QButtonGroup(compressor)
        self.radio_group.addButton(self.microsoft)
        self.radio_group.addButton(self.internal)
        compressor_layout.addWidget(self.microsoft)
        executable_row = QHBoxLayout()
        executable_row.addWidget(QLabel('Pfad:', compressor))
        self.hh_path = QLineEdit(compressor)
        self.hh_path.setObjectName('turbo_help_' + scope + '_hh_exe')
        executable_row.addWidget(self.hh_path, 1)
        self.browse_hh = QPushButton(compressor)
        self.browse_hh.setObjectName('turbo_help_' + scope + '_hh_browse')
        self.browse_hh.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.browse_hh.setToolTip('HH.EXE suchen')
        executable_row.addWidget(self.browse_hh)
        compressor_layout.addLayout(executable_row)
        compressor_layout.addWidget(self.internal)
        layout.addWidget(compressor)

        self.browse_directory.clicked.connect(self._choose_directory)
        self.browse_hh.clicked.connect(self._choose_hh)
        self.add_button.clicked.connect(self._add_path)
        self.delete_button.clicked.connect(self._delete_path)
        self.cancel_button.clicked.connect(self.directory.clear)
        self.cancel_button.clicked.connect(self.directory.setFocus)
        self.up_button.clicked.connect(lambda: self._move_path(-1))
        self.down_button.clicked.connect(lambda: self._move_path(1))
        self.directory.returnPressed.connect(self._add_path)
        self.paths.itemClicked.connect(lambda item: self.directory.setText(item.text()))
        self.relative.toggled.connect(self._emit_changed)
        self.microsoft.toggled.connect(self._toggle_compressor)
        self.internal.toggled.connect(self._toggle_compressor)
        self.hh_path.editingFinished.connect(self._emit_changed)
        self.set_data(default_help_settings()[scope])

    def _canonical_display_path(self, raw):
        import os
        path = Path(raw).expanduser()
        if not self.relative.isChecked() or self.project_base is None:
            return str(path)
        base = Path(self.project_base).resolve()
        if not path.is_absolute():
            return str(path)
        try:
            return os.path.relpath(str(path.resolve()), str(base))
        except ValueError:  # Windows paths on different drives
            return str(path)

    def _choose_directory(self):
        text = self.directory.text().strip()
        start = Path(text).expanduser() if text else Path.home()
        if text and not start.is_absolute() and self.project_base is not None:
            start = Path(self.project_base) / start
        path = QFileDialog.getExistingDirectory(self, 'Hilfe-Suchverzeichnis', str(start))
        if path:
            self.directory.setText(self._canonical_display_path(path))
            self.directory.setFocus(Qt.OtherFocusReason)

    def _choose_hh(self):
        start = self.hh_path.text().strip() or str(Path.home())
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Microsoft HTML Help auswählen', start,
            'Microsoft HTML Help (hh.exe);;Programme (*.exe);;Alle Dateien (*)')
        # QFileDialog accepts double-click and OK; Cancel returns an empty path.
        if filename:
            self.hh_path.setText(filename)
            self._emit_changed()
        self.hh_path.setFocus(Qt.OtherFocusReason)

    def _add_path(self):
        name = self._canonical_display_path(self.directory.text().strip())
        if not name:
            self.directory.setFocus(Qt.OtherFocusReason)
            return
        if not any(self.paths.item(i).text().casefold() == name.casefold()
                   for i in range(self.paths.count())):
            self.paths.addItem(name)
            self._emit_changed()
        self.paths.setCurrentRow(self.paths.count() - 1)

    def _delete_path(self):
        item = self.paths.currentItem()
        if item is None:
            return
        if QMessageBox.question(self, 'Suchpfad löschen',
                                f"Soll '{item.text()}' gelöscht werden?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        self.paths.takeItem(self.paths.row(item))
        self._emit_changed()

    def _move_path(self, delta):
        row = self.paths.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < self.paths.count():
            return
        item = self.paths.takeItem(row)
        self.paths.insertItem(target, item)
        self.paths.setCurrentRow(target)
        self._emit_changed()

    def _toggle_compressor(self, _checked=False):
        self.hh_path.setEnabled(self.microsoft.isChecked())
        self.browse_hh.setEnabled(self.microsoft.isChecked())
        self._emit_changed()

    def data(self):
        return {
            'relative': self.relative.isChecked(),
            'paths': [self.paths.item(i).text() for i in range(self.paths.count())],
            'compressor': 'microsoft' if self.microsoft.isChecked() else 'internal',
            'hh_path': self.hh_path.text().strip(),
        }

    def set_data(self, value):
        item = normalize_help_settings({self.scope: value})[self.scope]
        self._syncing = True
        try:
            self.relative.setChecked(item['relative'])
            self.paths.clear()
            self.paths.addItems(item['paths'])
            self.directory.clear()
            self.hh_path.setText(item['hh_path'])
            self.microsoft.setChecked(item['compressor'] == 'microsoft')
            self.internal.setChecked(item['compressor'] != 'microsoft')
            self.hh_path.setEnabled(self.microsoft.isChecked())
            self.browse_hh.setEnabled(self.microsoft.isChecked())
        finally:
            self._syncing = False

    def _emit_changed(self, *_args):
        if not self._syncing:
            self.changed.emit(self.scope, self.data())


def write_application_help_manifest(executable, settings):
    """Publish the application help search paths next to <project>.exe.

    The Qt5 bridge uses paths relative to the running EXE, independently of
    the IDE's working directory. The <project>.hlp sidecar remains first.
    """
    import json
    import os
    import tempfile
    exe = Path(executable).expanduser().resolve()
    if exe.suffix.casefold() != '.exe':
        raise ValueError('Die Hilfe-Suchpfade benötigen einen EXE-Dateinamen.')
    item = normalize_help_settings(settings)['anwendung']
    output = exe.with_suffix('.help.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'format': 'd64-turbo-help-paths-v1',
        'relative': item['relative'],
        'directories': item['paths'],
    }
    temp = None
    try:
        with tempfile.NamedTemporaryFile('w', dir=output.parent,
                                         prefix=output.name + '.', suffix='.tmp',
                                         encoding='utf-8', delete=False) as handle:
            temp = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, output)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    return output
