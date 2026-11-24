# -*- coding: utf-8 -*-
"""Stage 691: date/time PO-header editors and animated GIF loading splashes.

The Qt5 installation is not part of the test container; source-level UI
checks complement unit tests for the actual pure-Python date serializer.
"""
from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
import re

import pytest

from turbo_help_po_metadata import (
    HEADER_FIELDS, default_po_settings, format_po_header_datetime,
    normalize_po_settings, parse_po_header_datetime,
)

ROOT = Path(__file__).parent
PAGE_SOURCE = (ROOT / 'turbo_help_po_settings_page.py').read_text(encoding='utf-8')
MAIN_SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
LAUNCHER_SOURCE = (ROOT / 'examples' / '__main__.py').read_text(encoding='utf-8')


@pytest.mark.parametrize('raw,expected', [
    ('2026-11-24 19:26+0100', (2026, 11, 24, 19, 26)),
    ('2026-05-24 17:06+02:00', (2026, 5, 24, 17, 6)),
    ('2026-11-24 19:26:33+0100', (2026, 11, 24, 19, 26)),
    ('2026-11-24 19:26', (2026, 11, 24, 19, 26)),
])
def test_gettext_timestamp_loads_into_datetime_edit(raw, expected):
    got = parse_po_header_datetime(raw)
    assert got is not None
    assert (got.year, got.month, got.day, got.hour, got.minute) == expected


@pytest.mark.parametrize('raw', ['', 'not a timestamp', '2026-02-30 08:00+0100'])
def test_invalid_date_is_not_silently_reinterpreted(raw):
    assert parse_po_header_datetime(raw) is None


def test_datetime_picker_writes_valid_po_header_with_timezone():
    text = format_po_header_datetime(2026, 11, 24, 19, 26)
    assert re.fullmatch(r'2026-11-24 19:26[+-]\d{4}', text), text
    stamp = datetime.strptime(text, '%Y-%m-%d %H:%M%z')
    assert stamp.year == 2026 and stamp.minute == 26


def test_datetime_picker_validates_calendar_dates():
    with pytest.raises(ValueError):
        format_po_header_datetime(2026, 2, 30, 10, 10)


def test_po_header_project_roundtrip_preserves_date_strings():
    original = default_po_settings()
    original['headers']['POT-Creation-Date'] = '2026-01-25 09:47+0100'
    original['headers']['PO-Revision-Date'] = '2026-06-22 17:47+0200'
    saved = normalize_po_settings(original)
    assert saved['headers']['POT-Creation-Date'] == original['headers']['POT-Creation-Date']
    assert saved['headers']['PO-Revision-Date'] == original['headers']['PO-Revision-Date']


def test_turbo_help_settings_replaces_only_the_two_dates_with_picker():
    assert PAGE_SOURCE.count('QDateTimeEdit(content)') == 1  # loop conditional
    assert "('POT-Creation-Date', 'PO-Revision-Date')" in PAGE_SOURCE
    assert 'field.setCalendarPopup(True)' in PAGE_SOURCE
    assert "field.setDisplayFormat('yyyy-MM-dd HH:mm')" in PAGE_SOURCE
    assert 'field.dateTimeChanged.connect(' in PAGE_SOURCE
    assert "field.textEdited.connect(self._emit_changed)" in PAGE_SOURCE
    assert '_date_header_originals' in PAGE_SOURCE
    assert '_date_header_edited' in PAGE_SOURCE
    assert "'headers': {name: self._header_value(name) for name in HEADER_FIELDS}" in PAGE_SOURCE
    assert set(HEADER_FIELDS).issuperset({'POT-Creation-Date', 'PO-Revision-Date'})
    ast.parse(PAGE_SOURCE)


def test_operation_splash_plays_gif_only_when_valid_and_stops_on_hide():
    start = MAIN_SOURCE.index('class D64OperationPreludeDialog(QDialog):')
    end = MAIN_SOURCE.index('class C64ToolEditorDock(QDockWidget):', start)
    section = MAIN_SOURCE[start:end]
    assert 'd64_resolve_runtime_resource("data/loader.gif")' in section
    assert 'QMovie(str(gif_path), QByteArray(), self)' in section
    assert 'movie.isValid()' in section
    assert 'title_row.addWidget(self._loader_label, 0, Qt.AlignRight | Qt.AlignTop)' in section
    assert 'self._loader_movie.start()' in section
    assert 'self._loader_movie.stop()' in section
    assert 'self._loader_label.setMovie(movie)' in section


def test_startup_splash_loads_existing_gif_next_to_application():
    assert "Path(__file__).resolve().parent.parent / 'data' / 'loader.gif'" in LAUNCHER_SOURCE
    assert "Path(sys.executable).resolve().parent / 'data' / 'loader.gif'" in LAUNCHER_SOURCE
    assert 'QMovie(str(loader_path))' in LAUNCHER_SOURCE
    assert "loader_label.setObjectName('c64_startup_loader')" in LAUNCHER_SOURCE
    assert 'loader_movie.start()' in LAUNCHER_SOURCE
    assert 'loader_movie.stop()' in LAUNCHER_SOURCE
    ast.parse(LAUNCHER_SOURCE)


def test_loader_resource_is_optional_and_old_progress_bar_retained():
    start = MAIN_SOURCE.index('class D64OperationPreludeDialog(QDialog):')
    end = MAIN_SOURCE.index('class C64ToolEditorDock(QDockWidget):', start)
    section = MAIN_SOURCE[start:end]
    assert 'if gif_path.is_file():' in section
    assert 'progress.setRange(0, 0)' in section
    assert 'layout.addWidget(progress)' in section
    assert 'if loader_path is not None:' in LAUNCHER_SOURCE


def test_original_python315_imports_are_unchanged():
    assert 'lazy from app_lang.deu import APP_LANGUAGE as LANG_DEU' in MAIN_SOURCE
    assert 'lazy from app_lang.enu import APP_LANGUAGE as LANG_ENU' in MAIN_SOURCE

class _FakeDate:
    def __init__(self, y, m, d):
        self._parts = (y, m, d)

    def year(self): return self._parts[0]
    def month(self): return self._parts[1]
    def day(self): return self._parts[2]


class _FakeTime:
    def __init__(self, h, m):
        self._parts = (h, m)

    def hour(self): return self._parts[0]
    def minute(self): return self._parts[1]


class _FakeField:
    def __init__(self, text=''):
        self.value = text
        self.d = _FakeDate(2026, 1, 1)
        self.t = _FakeTime(0, 0)

    def text(self): return self.value
    def setText(self, text): self.value = text
    def setDate(self, date): self.d = date
    def setTime(self, time): self.t = time
    def date(self): return self.d
    def time(self): return self.t


class _FakeChanged:
    def __init__(self): self.values = []
    def emit(self, value): self.values.append(value)


def _fake_page():
    """Run the actual non-UI TurboHelpPoSettingsPage methods against stubs."""
    source_ast = ast.parse(PAGE_SOURCE)
    node = next(n for n in source_ast.body if isinstance(n, ast.ClassDef)
                and n.name == 'TurboHelpPoSettingsPage')
    names = {'set_data', 'data', '_on_datetime_changed', '_header_value',
             '_emit_changed'}
    ns = {
        'QDate': _FakeDate, 'QTime': _FakeTime,
        'HEADER_FIELDS': HEADER_FIELDS, '_DATE_HEADERS': frozenset(
            ('POT-Creation-Date', 'PO-Revision-Date')),
        'default_catalog_paths': __import__('turbo_help_po_metadata').default_catalog_paths,
        'normalize_po_settings': normalize_po_settings,
        'parse_po_header_datetime': parse_po_header_datetime,
        'format_po_header_datetime': format_po_header_datetime,
    }
    for method in node.body:
        if isinstance(method, ast.FunctionDef) and method.name in names:
            code = ast.Module(body=[method], type_ignores=[])
            ast.fix_missing_locations(code)
            exec(compile(code, 'turbo_help_po_settings_page.py', 'exec'), ns)

    class Page:
        pass

    for name in names:
        setattr(Page, name, ns[name])
    page = Page()
    page._loading = False
    page._date_header_originals = {}
    page._date_header_edited = {}
    page._input_overridden = False
    page._output_overridden = False
    page._suggested_po = ''
    page._suggested_hlp = ''
    page.input_file = _FakeField()
    page.output_file = _FakeField()
    page.header_edits = {name: _FakeField() for name in HEADER_FIELDS}
    page.changed = _FakeChanged()
    return page


def test_actual_settings_methods_keep_saved_header_dates_until_user_changes_them(tmp_path):
    page = _fake_page()
    saved = default_po_settings()
    saved['headers'].update({
        'POT-Creation-Date': '2026-01-05 14:22+0100',
        'PO-Revision-Date': '2026-07-19 16:45+0200',
        'Last-Translator': 'Example Name',
    })
    page.set_data(saved, main_file=tmp_path/'Main.thlp', project_dir=tmp_path)
    data = page.data()
    assert data['headers']['POT-Creation-Date'] == '2026-01-05 14:22+0100'
    assert data['headers']['PO-Revision-Date'] == '2026-07-19 16:45+0200'
    assert data['headers']['Last-Translator'] == 'Example Name'
    assert page.changed.values == []
    page.header_edits['POT-Creation-Date'].setTime(_FakeTime(9, 12))
    page._on_datetime_changed('POT-Creation-Date')
    assert re.fullmatch(r'2026-01-05 09:12[+-]\d{4}', page.data()['headers']['POT-Creation-Date'])
    assert page.data()['headers']['PO-Revision-Date'] == '2026-07-19 16:45+0200'
    assert len(page.changed.values) == 1


def test_actual_settings_methods_update_header_without_overriding_date(tmp_path):
    page = _fake_page()
    state = default_po_settings()
    state['headers']['POT-Creation-Date'] = '2026-11-24 12:30+0100'
    page.set_data(state, main_file=tmp_path/'a.thlp')
    page.header_edits['Last-Translator'].setText('Updated')
    page._emit_changed()
    last = page.changed.values[-1]
    assert last['headers']['Last-Translator'] == 'Updated'
    assert last['headers']['POT-Creation-Date'] == '2026-11-24 12:30+0100'
    assert last['output_file'] == ''  # derived path, not a manual override
