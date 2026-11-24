# -*- coding: utf-8 -*-
"""Stage 652: dBase2Many Turbo Help multi-document editor (Python, not bridge)."""
from __future__ import annotations

from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence, QPalette
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit,
    QPushButton, QShortcut, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)
from turbo_help_compiler import HelpCompileError, HelpCompiler, read_po, write_mo, write_po
from turbo_help_editor_widgets import TurboHelpSourceEditor

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
        self.resolve_project_help_inputs = None  # Stage 685: main source + nested tree
        self.resolve_project_po_settings = None  # Stage 688: PO/HLP paths and headers
        self.po_settings_page = None
        self.source_path = None
        self.editor = None
        self._active_tab = None  # independent of currentIndex, which changes during mouse clicks
        self._tab_switch_lock = False
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
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, TurboHelpSourceEditor) else None

    def _path_for(self, edit):
        return getattr(edit, '_thlp_path', None)

    def _save_changes_before_switch(self):
        """Save the active source before the user leaves its tab (Stage 662).

        A canceled Save As dialog or failed write must leave the old tab active.
        Untouched new tabs do not trigger a Save As prompt just for switching.
        """
        old = self._active_tab
        if (old is not None and isinstance(old, TurboHelpSourceEditor)
                and self.tabs.indexOf(old) >= 0 and old.document().isModified()):
            return self._save_edit(old)
        return True

    def _sync_current(self, _index=-1):
        """Handle mouse, keyboard and programmatic tab changes consistently."""
        if self._tab_switch_lock:
            return False
        target = self._current_editor()
        old = self._active_tab
        if old is not None and target is not old and self.tabs.indexOf(old) >= 0:
            if not self._save_changes_before_switch():
                # QTabWidget emits currentChanged *after* changing its index.
                # Restore the former tab without entering this handler again.
                self._tab_switch_lock = True
                try:
                    self.tabs.setCurrentWidget(old)
                finally:
                    self._tab_switch_lock = False
                old.setFocus(Qt.OtherFocusReason)
                return False
        self._active_tab = target
        self.editor = target if isinstance(target, TurboHelpSourceEditor) else None
        self.source_path = self._path_for(self.editor) if self.editor is not None else None
        if target is not None:
            target.setFocus(Qt.OtherFocusReason)
        return True

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
        edit = TurboHelpSourceEditor(self.tabs)
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
        close.setToolTip('Tab schließen (bei Änderungen mit Speicherrückfrage)')
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
        if not self._save_changes_before_switch():
            return None
        template = DEFAULT_SOURCE if not any(
            isinstance(self.tabs.widget(i), TurboHelpSourceEditor)
            for i in range(self.tabs.count())) else '%topic "Neues Thema"\n\n'
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
                    if widget is not self._current_editor():
                        if not self._save_changes_before_switch():
                            return False
                        self.tabs.setCurrentIndex(index)
                    widget.setFocus(Qt.OtherFocusReason)
                    return self._current_editor() is widget
            content = source.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError, ValueError) as exc:
            self._show_help_message(QMessageBox.Critical, 'Hilfecompiler', f'Datei kann nicht geöffnet werden:\n{exc}')
            return False
        # Never discard edits to another tab when loading a new project leaf.
        if not self._save_changes_before_switch():
            return False
        # An untouched placeholder can be replaced, but never a modified document.
        if self.tabs.count() == 1:
            blank = self.tabs.widget(0)
            if (isinstance(blank, TurboHelpSourceEditor)
                    and self._path_for(blank) is None
                    and not blank.document().isModified()):
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
            self._show_help_message(QMessageBox.Warning, 'Hilfecompiler', 'Die Dateiendung muss .thlp sein.')
            return False
        path = path.resolve()
        for index in range(self.tabs.count()):
            other = self.tabs.widget(index)
            if other is not edit and self._path_for(other) == path:
                self._show_help_message(QMessageBox.Warning, 'Hilfecompiler', 'Diese Datei ist bereits in einem anderen Tab geöffnet.')
                return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(edit.toPlainText(), encoding='utf-8', newline='\n')
        except OSError as exc:
            self._show_help_message(QMessageBox.Critical, 'Hilfecompiler', f'Datei kann nicht gespeichert werden:\n{exc}')
            return False
        edit._thlp_path = path
        edit.document().setModified(False)
        self._refresh_tab(edit)
        if self._current_editor() is edit:
            self.source_path = path
        self.status_label.setText(f'Gespeichert: {path.name}')
        self.document_saved.emit(str(path), edit)
        return True

    def save_document(self):
        return self._save_edit(self._current_editor())

    def save_document_as(self):
        return self._save_edit(self._current_editor(), True)

    def close_document(self, edit):
        """Close a THLP source with Save / Discard / Cancel (Stage 690).

        A newly created, untouched placeholder has no file path.  It must not
        force a Save As dialog merely because the user closes the first tab
        after opening the Turbo Help root's Settings page.
        """
        index = self.tabs.indexOf(edit)
        if index < 0 or not isinstance(edit, TurboHelpSourceEditor):
            return False
        path = self._path_for(edit)
        if edit.document().isModified() or path is None:
            name = path.name if path is not None else 'Unbenannt.thlp'
            prompt = self._help_message_box(
                QMessageBox.Question, 'Turbo Hilfe – Tab schließen',
                f'Soll die Hilfedatei "{name}" vor dem Schließen gespeichert werden?')
            prompt.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            prompt.setDefaultButton(QMessageBox.Cancel)
            answer = prompt.exec_()
            if answer == QMessageBox.Yes:
                # Canceled Save As or a write error must keep the tab intact.
                if not self._save_edit(edit):
                    return False
            elif answer != QMessageBox.No:
                # Cancel, Escape and closing the dialog leave the editor open.
                return False
        # Removing a tab may trigger currentChanged synchronously.  The
        # removed editor is no longer a tab and therefore will not be saved
        # again by _sync_current's save-before-switch guard.
        self.tabs.removeTab(index)
        edit.deleteLater()
        self._sync_current()
        return True

    def save_all_documents(self):
        for i in range(self.tabs.count()):
            edit = self.tabs.widget(i)
            if not isinstance(edit, TurboHelpSourceEditor):
                continue  # Settings is a form, not a source document.
            if edit.document().isModified() or self._path_for(edit) is None:
                if not self._save_edit(edit):
                    return False
        return True

    def show_settings(self, state, *, main_file=None, project_dir=None, on_changed=None):
        """Open the project-local Settings tab on root-node clicks."""
        from turbo_help_po_settings_page import TurboHelpPoSettingsPage
        if self.po_settings_page is None:
            page = TurboHelpPoSettingsPage(self.tabs)
            self.po_settings_page = page
            self.tabs.addTab(page, 'Settings')
        page = self.po_settings_page
        if on_changed is not None and getattr(page, '_on_changed_callback', None) != on_changed:
            previous = getattr(page, '_on_changed_callback', None)
            if previous is not None:
                try:
                    page.changed.disconnect(previous)
                except (TypeError, RuntimeError):
                    pass
            page.changed.connect(on_changed)
            page._on_changed_callback = on_changed
        page.set_data(state, main_file=main_file, project_dir=project_dir)
        self.tabs.setCurrentWidget(page)
        return page

    def _help_message_box(self, icon, title, message):
        """Theme Turbo Help messages like the parent project's other dialogs.

        The editor is hosted in a QDockWidget. Its direct parent is not
        necessarily MainWindow and normally has no ``dark_mode_enabled``.
        Walk the Qt parent chain and reuse MainWindow's established factory,
        which sets an explicit text palette and button stylesheet.
        """
        current = self
        while current is not None:
            creator = getattr(current, '_create_message_box', None)
            if callable(creator):
                return creator(icon, str(title), str(message))
            parent_widget = getattr(current, 'parentWidget', None)
            current = parent_widget() if callable(parent_widget) else None

        # Stand-alone editor/test harness: still give the message an explicit
        # light/dark palette instead of relying on the platform's native style.
        box = QMessageBox(self)
        box.setObjectName('turbo_help_themed_message_box')
        box.setWindowTitle(str(title))
        box.setIcon(icon)
        box.setTextFormat(Qt.PlainText)
        box.setText(str(message))
        box.setStandardButtons(QMessageBox.Ok)
        box.setAttribute(Qt.WA_StyledBackground, True)
        app = QApplication.instance()
        palette = app.palette() if app is not None else self.palette()
        dark = palette.color(QPalette.Window).lightness() < 128
        if dark:
            stylesheet = (
                'QMessageBox{background-color:#202630;color:#ffffff;}'
                'QMessageBox QLabel{color:#ffffff;background:transparent;}'
                'QMessageBox QPushButton{min-width:78px;color:#ffffff;'
                'background-color:#343e4d;border:1px solid #596779;'
                'border-radius:3px;padding:5px 10px;}'
                'QMessageBox QPushButton:hover{background-color:#414d5f;}'
            )
        else:
            stylesheet = (
                'QMessageBox{background-color:#f0f0f0;color:#000000;}'
                'QMessageBox QLabel{color:#000000;background:transparent;}'
                'QMessageBox QPushButton{min-width:78px;color:#000000;'
                'background-color:#f5f5f5;border:1px solid #9b9b9b;'
                'border-radius:3px;padding:5px 10px;}'
                'QMessageBox QPushButton:hover{background-color:#e4f1fb;}'
            )
        box.setPalette(palette)
        box.setStyleSheet(stylesheet)
        return box

    def _show_help_message(self, icon, title, message):
        return self._help_message_box(icon, title, message).exec_()

    def compile_help(self):
        if self._busy:
            return False
        # No Save-As prompt for an unconfigured project: main selection is
        # mandatory before any F2 compilation can begin.
        if self.use_project_list and callable(self.resolve_project_help_inputs):
            try:
                self.resolve_project_help_inputs()
            except (OSError, ValueError) as exc:
                self.status_label.setText(f'Fehler: {exc}')
                self._show_help_message(QMessageBox.Warning, 'Turbo Hilfe', str(exc))
                return False
        if not self.save_all_documents():
            return False
        self._busy = True
        try:
            paths = []
            root = None
            include_paths = ()
            if self.use_project_list and callable(self.resolve_project_help_inputs):
                selected, root, include_paths = self.resolve_project_help_inputs()
            else:
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
            po_options = (self.resolve_project_po_settings()
                          if self.use_project_list and callable(self.resolve_project_po_settings)
                          else {})
            topics, po_path, hlp_path = compile_help_sources(
                paths, executable, root=root, include_paths=include_paths,
                **po_options)
            self.status_label.setText(f'Erfolgreich: {len(topics)} Themen · {hlp_path}')
            self.compiled.emit(dict(topics), str(po_path), str(hlp_path))
            return True
        except (HelpCompileError, OSError, UnicodeError, ValueError) as exc:
            self.status_label.setText(f'Fehler: {exc}')
            self._show_help_message(QMessageBox.Critical, 'Hilfecompiler', str(exc))
            return False
        finally:
            self._busy = False
