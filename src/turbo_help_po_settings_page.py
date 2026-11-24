# -*- coding: utf-8 -*-
"""Stage 688: editable Turbo Help PO/HLP Settings tab, modelled on Localize PO/MO."""
from PyQt5.QtCore import QDate, QTime, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel, QLineEdit,
                             QVBoxLayout, QScrollArea, QFrame, QPushButton,
                             QFileDialog, QDateTimeEdit)
from turbo_help_po_metadata import (HEADER_FIELDS, normalize_po_settings,
                                    default_catalog_paths, parse_po_header_datetime,
                                    format_po_header_datetime)


# Gettext metadata contains a timezone offset in addition to the wall clock time.
# The QDateTimeEdit shows the local date/time; the raw original is retained until
# the user actually changes a picker, to avoid silently changing saved headers.
_DATE_HEADERS = frozenset(('POT-Creation-Date', 'PO-Revision-Date'))


class TurboHelpPoSettingsPage(QWidget):
    changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('turbo_help_po_settings')
        self._loading = False
        self._input_overridden = False
        self._output_overridden = False
        self._suggested_po = ''
        self._suggested_hlp = ''
        self._date_header_originals = {}
        self._date_header_edited = {}
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setObjectName('turbo_help_po_settings_scroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget(scroll)
        grid = QGridLayout(content)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        row = 0
        grid.addWidget(QLabel('Input file (*.po):', content), row, 0)
        self.input_file = QLineEdit(content)
        self.input_file.setFont(QFont('Arial', 10))
        self.input_file.setObjectName('turbo_help_po_input')
        grid.addWidget(self.input_file, row, 1)
        browse_po = QPushButton('Load', content)
        grid.addWidget(browse_po, row, 2)
        row += 1
        grid.addWidget(QLabel('Output file (*.hlp):', content), row, 0)
        self.output_file = QLineEdit(content)
        self.output_file.setFont(QFont('Arial', 10))
        self.output_file.setObjectName('turbo_help_hlp_output')
        grid.addWidget(self.output_file, row, 1)
        browse_hlp = QPushButton('Load', content)
        grid.addWidget(browse_hlp, row, 2)
        row += 1
        self.header_edits = {}
        for header in HEADER_FIELDS:
            grid.addWidget(QLabel(header + ':', content), row, 0)
            if header in _DATE_HEADERS:
                field = QDateTimeEdit(content)
                field.setDisplayFormat('yyyy-MM-dd HH:mm')
                field.setCalendarPopup(True)
                field.setToolTip('Datum und Uhrzeit auswählen; Zeitzone wird im PO-Header gespeichert.')
                field.dateTimeChanged.connect(
                    lambda _value, name=header: self._on_datetime_changed(name))
            else:
                field = QLineEdit(content)
                field.textEdited.connect(self._emit_changed)
            field.setObjectName('turbo_help_header_' + header.replace('-', '_'))
            field.setFont(QFont('Arial', 10))
            self.header_edits[header] = field
            grid.addWidget(field, row, 1, 1, 2)
            row += 1
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(row, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.input_file.textEdited.connect(self._on_input_edit)
        self.output_file.textEdited.connect(self._on_output_edit)
        browse_po.clicked.connect(self._browse_po)
        browse_hlp.clicked.connect(self._browse_hlp)

    def _on_datetime_changed(self, name):
        if not self._loading:
            self._date_header_edited[name] = True
            self._emit_changed()

    def _header_value(self, name):
        edit = self.header_edits[name]
        if name not in _DATE_HEADERS:
            return edit.text()
        if not self._date_header_edited.get(name, False):
            return self._date_header_originals.get(name, '')
        date = edit.date()
        time = edit.time()
        return format_po_header_datetime(
            date.year(), date.month(), date.day(), time.hour(), time.minute())

    def _on_input_edit(self, *_args):
        self._input_overridden = True
        self._emit_changed()

    def _on_output_edit(self, *_args):
        self._output_overridden = True
        self._emit_changed()

    def _browse_po(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 'PO-Datei auswählen', self.input_file.text(),
            'PO Dateien (*.po);;Alle Dateien (*)')
        if filename:
            self._input_overridden = True
            self.input_file.setText(filename)
            self._emit_changed()

    def _browse_hlp(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 'HLP-Datei auswählen', self.output_file.text(),
            'HLP Dateien (*.hlp);;Alle Dateien (*)')
        if filename:
            self._output_overridden = True
            self.output_file.setText(filename)
            self._emit_changed()

    def set_data(self, state, main_file=None, project_dir=None):
        state = normalize_po_settings(state)
        recommended_po, recommended_hlp = default_catalog_paths(main_file, project_dir)
        self._loading = True
        try:
            self._suggested_po, self._suggested_hlp = str(recommended_po), str(recommended_hlp)
            self._input_overridden = bool(state['input_file'])
            self._output_overridden = bool(state['output_file'])
            self.input_file.setText(state['input_file'] or self._suggested_po)
            self.output_file.setText(state['output_file'] or self._suggested_hlp)
            self._date_header_originals.clear()
            self._date_header_edited.clear()
            for name in HEADER_FIELDS:
                value = state['headers'].get(name, '')
                if name in _DATE_HEADERS:
                    self._date_header_originals[name] = value
                    stamp = parse_po_header_datetime(value)
                    if stamp is not None:
                        self.header_edits[name].setDate(QDate(stamp.year, stamp.month, stamp.day))
                        self.header_edits[name].setTime(QTime(stamp.hour, stamp.minute))
                    else:
                        # Invalid/empty legacy values remain untouched in the
                        # project until the user selects a new date/time.
                        from datetime import datetime
                        now = datetime.now()
                        self.header_edits[name].setDate(QDate(now.year, now.month, now.day))
                        self.header_edits[name].setTime(QTime(now.hour, now.minute))
                else:
                    self.header_edits[name].setText(value)
        finally:
            self._loading = False

    def refresh_suggested_paths(self, main_file=None, project_dir=None):
        po, hlp = default_catalog_paths(main_file, project_dir)
        self._suggested_po, self._suggested_hlp = str(po), str(hlp)
        if not self._input_overridden:
            self.input_file.setText(self._suggested_po)
        if not self._output_overridden:
            self.output_file.setText(self._suggested_hlp)

    def data(self):
        return {
            'input_file': self.input_file.text().strip() if self._input_overridden else '',
            'output_file': self.output_file.text().strip() if self._output_overridden else '',
            'headers': {name: self._header_value(name) for name in HEADER_FIELDS},
        }

    def _emit_changed(self, *_args):
        if not self._loading:
            self.changed.emit(self.data())
