# -*- coding: utf-8 -*-
"""Add source-preserving RC language variants to both resource editor frontends.

Used by the main d64_dism editor and by the stand-alone resource editor.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path


def install_resource_editor(editor_class, compile_rc):
    """Patch an existing editor frontend; safe to call more than once."""
    if getattr(editor_class, '_d64_multilang_installed', False):
        return editor_class
    from PyQt5.QtCore import QTimer, Qt
    from PyQt5.QtWidgets import QAction, QInputDialog
    from resource_multilang import edit_resource_language

    old_build_ui = editor_class._build_ui

    def _build_ui(self):
        old_build_ui(self)
        if hasattr(self, 'template_toolbar'):
            self.template_toolbar.addSeparator()
            action = QAction('Sprachvariante hinzufügen ...', self)
            action.setObjectName('resource_add_language_variant')
            action.setToolTip('Ausgewählte Ressource in einer weiteren Sprache duplizieren')
            action.triggered.connect(self.add_resource_language_variant)
            self.template_toolbar.addAction(action)
            self.act_add_language_variant = action

    def _edit_language_variant(self, index: int, lang_id: int, *, duplicate=False) -> bool:
        if not 0 <= index < len(self.entries):
            return False
        lang_id &= 0xFFFF
        selected = self.entries[index]
        path = self.current_path
        if path is None or path.suffix.lower() == '.rc':
            path = path or (Path.cwd() / 'untitled.rc')
            text = self.source_edit.toPlainText()
            try:
                updated, compiled, selection = edit_resource_language(
                    text, selected, lang_id,
                    lambda content: compile_rc(
                        path, include_dirs=[path.parent], source_text=content
                    ).entries,
                    duplicate=duplicate,
                )
            except Exception as exc:
                self._set_status(f'Sprache unverändert: {exc}')
                self._warning('Ressourcen-Sprache', str(exc))
                QTimer.singleShot(0, lambda idx=index: self._populate_tree(selected_index=idx))
                return False
            if updated == text:
                return True
            self._set_source_text_preserve_cursor(updated)
            self.entries = compiled
            if hasattr(self, '_preview_source_text'):
                self._preview_source_text = updated
            timer = getattr(self, '_source_preview_timer', None)
            if timer is not None:
                timer.stop()
            QTimer.singleShot(0, lambda idx=selection: self._populate_tree(selected_index=idx))
        else:
            # .res is binary: preserve all other entries and save via save_res.
            key = (selected.type_id, selected.name_id, lang_id)
            if any(e.key() == key for i, e in enumerate(self.entries)
                   if duplicate or i != index):
                self._warning('Ressourcen-Sprache', 'Diese Sprachvariante existiert bereits.')
                return False
            if duplicate:
                self.entries.append(replace(selected, language=lang_id))
                selection = len(self.entries) - 1
            else:
                selected.language = lang_id
                selection = index
            self._dirty = True
            QTimer.singleShot(0, lambda idx=selection: self._populate_tree(selected_index=idx))
        self._set_status(
            ('Sprachvariante hinzugefügt' if duplicate else 'Sprache geändert')
            + f': LANGID 0x{lang_id:04X}'
        )
        return True

    def add_resource_language_variant(self, checked=False) -> bool:
        del checked
        item = self.resource_tree.currentItem()
        index = item.data(0, Qt.UserRole) if item is not None else None
        if not isinstance(index, int) or not 0 <= index < len(self.entries):
            self._warning('Ressourcen-Sprache', 'Bitte eine Ressource auswählen.')
            return False
        selected = self.entries[index]
        present = {e.language & 0xFFFF for e in self.entries
                   if e.type_id == selected.type_id and e.name_id == selected.name_id}
        choices = [(f'{code} – {title} (0x{langid:04X})', langid)
                   for code, title, _flag, langid in self.language_codes
                   if langid not in present]
        if not choices:
            self._warning('Ressourcen-Sprache', 'Keine weitere Sprache verfügbar.')
            return False
        label, ok = QInputDialog.getItem(
            self, 'Sprachvariante hinzufügen', 'Neue Sprache:',
            [label for label, _ in choices], 0, False,
        )
        if not ok:
            return False
        language = next(langid for title, langid in choices if title == label)
        return self._edit_language_variant(index, language, duplicate=True)

    def _language_changed(self, index: int, lang_id: int) -> None:
        self._edit_language_variant(index, lang_id, duplicate=False)

    editor_class._build_ui = _build_ui
    editor_class._edit_language_variant = _edit_language_variant
    editor_class.add_resource_language_variant = add_resource_language_variant
    editor_class._language_changed = _language_changed
    editor_class._d64_multilang_installed = True
    return editor_class
