# -*- coding: utf-8 -*-
"""Stage 652: dBase2Many Turbo Help multi-document editor (Python, not bridge)."""
from __future__ import annotations

from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit,
    QPushButton, QShortcut, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)
from turbo_help_compiler import HelpCompileError, HelpCompiler, read_po, write_mo, write_po

DEFAULT_SOURCE = '%topic "index"\n<b>Turbo Vision - dBASE Hilfe</b>\n\nWillkommen zur Hilfe.\n'


class TurboHelpEditor(QWidget):
    """Tabbed THLP editor. F2 compiles all saved project files into GNU .hlp."""
    compiled = pyqtSignal(object, str, str)
    document_saved = pyqtSignal(str, object)

    def __init__(self, source_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName('turbo_help_compiler_editor')
        self._busy = False
        self.project_sources = []
        self.use_project_list = False
        self.resolve_output_executable = None  # supplied by dBase2Many project settings
        self.source_path = None
        self.editor = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)
        tools = QHBoxLayout()
        for caption, slot in (
            ('Neu', self.new_document),
            ('Öffnen ...', self.open_document),
            ('Speichern', self.save_document),
            ('Speichern unter ...', self.save_document_as),
            ('Kompilieren (F2)', self.compile_help),
        ):
            button = QPushButton(caption, self)
            button.clicked.connect(slot)
            tools.addWidget(button)
            if caption.startswith('Kompilieren'):
                button.setObjectName('turbo_help_compile_button')
        tools.addStretch(1)
        layout.addLayout(tools)

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName('turbo_help_source_tabs')
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)  # red X is attached to each tab explicitly
        self.tabs.currentChanged.connect(self._sync_current)
        layout.addWidget(self.tabs, 1)
        self.status_label = QLabel('F2: Hilfethemen nach PO und HLP kompilieren.', self)
        self.status_label.setObjectName('turbo_help_compiler_status')
        layout.addWidget(self.status_label)
        self.compile_shortcut = QShortcut(QKeySequence('F2'), self)
        self.compile_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.compile_shortcut.activated.connect(self.compile_help)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        if source_path is not None and Path(source_path).is_file():
            self.load_document(Path(source_path))
        else:
            self.new_document()

    def _current_editor(self):
        return self.tabs.currentWidget()

    def _path_for(self, edit):
        return getattr(edit, '_thlp_path', None)

    def _sync_current(self, _index=-1):
        self.editor = self._current_editor()
        self.source_path = self._path_for(self.editor) if self.editor else None

    def _refresh_tab(self, edit):
        index = self.tabs.indexOf(edit)
        if index < 0:
            return
        path = self._path_for(edit)
        name = path.name if path else 'Unbenannt.thlp'
        if edit.document().isModified():
            name += ' *'
        self.tabs.setTabText(index, name)
        self.tabs.setTabToolTip(index, str(path) if path else 'Noch nicht gespeichert')

    def _append_tab(self, text, path=None):
        edit = QPlainTextEdit(self.tabs)
        edit.setObjectName('turbo_help_source_editor')
        edit.setFont(QFont('Consolas', 10))
        edit.setTabStopDistance(edit.fontMetrics().horizontalAdvance(' ') * 4)
        edit.setStyleSheet('QPlainTextEdit {background:#17232d; color:#e4f5f5; '
                           'selection-background-color:#155d82; border:1px solid #485b60;}')
        edit._thlp_path = Path(path).resolve() if path else None
        edit.setPlainText(text)
        edit.document().setModified(False)
        edit.document().modificationChanged.connect(lambda _modified, widget=edit: self._refresh_tab(widget))
        index = self.tabs.addTab(edit, '')
        close = QToolButton(self.tabs.tabBar())
        close.setObjectName('turbo_help_tab_close')
        close.setText('×')
        close.setCursor(Qt.PointingHandCursor)
        close.setToolTip('Datei speichern und Tab schließen')
        close.setStyleSheet('QToolButton#turbo_help_tab_close{color:#e93232; border:0; '
                            'font:bold 14pt Arial; background:transparent; padding:0 3px;}'
                            'QToolButton#turbo_help_tab_close:hover{color:#ffffff; background:#a81c1c;}')
        close.clicked.connect(lambda _checked=False, widget=edit: self.close_document(widget))
        self.tabs.tabBar().setTabButton(index, self.tabs.tabBar().RightSide, close)
        self.tabs.setCurrentWidget(edit)
        self._refresh_tab(edit)
        edit.setFocus()
        return edit

    def new_document(self):
        template = DEFAULT_SOURCE if self.tabs.count() == 0 else '%topic "Neues Thema"\n\n'
        self._append_tab(template)
        self.status_label.setText('Neuer Hilfetext: Speichern unter ... (*.thlp)')
        return self._current_editor()

    def open_document(self):
        base = self.source_path.parent if self.source_path else Path.cwd()
        name, _ = QFileDialog.getOpenFileName(self, 'Turbo-Hilfedatei öffnen', str(base),
                                              'Turbo Vision Hilfe (*.thlp);;Alle Dateien (*)')
        if name:
            self.load_document(Path(name))

    def load_document(self, source):
        try:
            source = Path(source).expanduser().resolve(strict=True)
            if source.suffix.casefold() != '.thlp':
                raise ValueError('Nur .thlp-Dateien werden akzeptiert')
            for index in range(self.tabs.count()):
                widget = self.tabs.widget(index)
                if self._path_for(widget) == source:
                    self.tabs.setCurrentIndex(index)
                    widget.setFocus()
                    return True
            content = source.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.critical(self, 'Hilfecompiler', f'Datei kann nicht geöffnet werden:\n{exc}')
            return False
        # An untouched placeholder can be replaced, but never a modified document.
        if self.tabs.count() == 1:
            blank = self.tabs.widget(0)
            if self._path_for(blank) is None and not blank.document().isModified():
                self.tabs.removeTab(0)
                blank.deleteLater()
        self._append_tab(content, source)
        self.status_label.setText(f'Geöffnet: {source.name}')
        return True

    def _save_edit(self, edit, force_as=False):
        if edit is None:
            return False
        path = None if force_as else self._path_for(edit)
        if path is None:
            base = self._path_for(edit)
            initial = str(base or (Path.cwd() / 'System.Help.thlp'))
            name, _ = QFileDialog.getSaveFileName(self, 'Turbo-Hilfedatei speichern', initial,
                                                  'Turbo Vision Hilfe (*.thlp)')
            if not name:
                return False
            path = Path(name)
            if not path.suffix:
                path = path.with_suffix('.thlp')
        if path.suffix.casefold() != '.thlp':
            QMessageBox.warning(self, 'Hilfecompiler', 'Die Dateiendung muss .thlp sein.')
            return False
        path = path.resolve()
        for index in range(self.tabs.count()):
            other = self.tabs.widget(index)
            if other is not edit and self._path_for(other) == path:
                QMessageBox.warning(self, 'Hilfecompiler', 'Diese Datei ist bereits in einem anderen Tab geöffnet.')
                return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(edit.toPlainText(), encoding='utf-8', newline='\n')
        except OSError as exc:
            QMessageBox.critical(self, 'Hilfecompiler', f'Datei kann nicht gespeichert werden:\n{exc}')
            return False
        edit._thlp_path = path
        edit.document().setModified(False)
        self._refresh_tab(edit)
        self._sync_current()
        self.status_label.setText(f'Gespeichert: {path.name}')
        self.document_saved.emit(str(path), edit)
        return True

    def save_document(self):
        return self._save_edit(self._current_editor())

    def save_document_as(self):
        return self._save_edit(self._current_editor(), True)

    def close_document(self, edit):
        index = self.tabs.indexOf(edit)
        if index < 0:
            return False
        # Unsaved changes must be saved, not silently discarded.
        if edit.document().isModified() or self._path_for(edit) is None:
            if not self._save_edit(edit):
                return False
        self.tabs.removeTab(index)
        edit.deleteLater()
        self._sync_current()
        return True

    def save_all_documents(self):
        for i in range(self.tabs.count()):
            edit = self.tabs.widget(i)
            if edit.document().isModified() or self._path_for(edit) is None:
                if not self._save_edit(edit):
                    return False
        return True

    def compile_help(self):
        if self._busy:
            return False
        if not self.save_all_documents():
            return False
        self._busy = True
        try:
            paths = []
            selected = (self.project_sources if self.use_project_list else
                        [self._path_for(self.tabs.widget(i)) for i in range(self.tabs.count())])
            for item in selected:
                if item is not None:
                    candidate = Path(item).resolve()
                    if not candidate.is_file():
                        raise HelpCompileError(f'Projekt-Hilfedatei fehlt: {candidate}')
                    if candidate not in paths:
                        paths.append(candidate)
            if not paths:
                raise HelpCompileError('Keine .thlp-Dateien vorhanden')
            # Stage 655: F2 must never derive output names from a .thlp tab.
            if not callable(self.resolve_output_executable):
                raise HelpCompileError('Kein dBASE-Programmprojekt für die Hilfe ausgewählt.')
            try:
                executable = Path(self.resolve_output_executable())
            except ValueError as exc:
                raise HelpCompileError(str(exc)) from exc
            from turbo_help_sidecar import compile_help_sources
            topics, po_path, hlp_path = compile_help_sources(paths, executable)
            self.status_label.setText(f'Erfolgreich: {len(topics)} Themen · {hlp_path}')
            self.compiled.emit(dict(topics), str(po_path), str(hlp_path))
            return True
        except (HelpCompileError, OSError, UnicodeError, ValueError) as exc:
            self.status_label.setText(f'Fehler: {exc}')
            QMessageBox.critical(self, 'Hilfecompiler', str(exc))
            return False
        finally:
            self._busy = False
