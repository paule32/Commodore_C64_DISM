"""Stage 688: project-local Turbo Hilfe Settings, PO/HLP without separate MO."""
from __future__ import annotations

import gettext
import io
from pathlib import Path

import pytest

from turbo_help_po_metadata import (
    HEADER_FIELDS, default_po_headers, default_catalog_paths,
    normalize_po_settings, resolve_catalog_paths,
)
from turbo_help_sidecar import compile_help_sources, compile_project_help

HERE = Path(__file__).resolve().parent


class FakeQSettings:
    def __init__(self, fields=None):
        self.fields = fields or {}

    def value(self, key, default=None):
        return self.fields.get(key, default)


def test_settings_use_existing_localize_header_schema_and_default_values():
    src = (HERE / 'd64_dism.py').read_text(encoding='utf-8')
    localize_schema = src.split('class LocalizeToolWindow(QDialog):', 1)[1].split('def __init__(', 1)[0]
    assert all(f'"{name}"' in localize_schema for name in HEADER_FIELDS)
    saved = FakeQSettings({
        'localize/header/Last-Translator': 'Example Author',
        'localize/header/Language': 'DEU:ENU',
        'localize/header/Project-Id-Version': 'v9.1',
    })
    headers = default_po_headers(saved)
    assert headers['Last-Translator'] == 'Example Author'
    assert headers['Project-Id-Version'] == 'v9.1'
    assert headers['Language'] == 'DEU:ENU'
    assert headers['Content-Type'] == 'text/plain; charset=UTF-8'
    defaults = default_po_headers(FakeQSettings({
        'localize/source_lang': 'ENU', 'localize/dest_lang': 'DEU'}))
    assert defaults['Language'] == 'ENU:DEU'


def test_default_paths_are_based_on_main_thlp_and_end_in_po_hlp(tmp_path):
    main = tmp_path / 'Help' / 'Main.thlp'
    po, hlp = default_catalog_paths(main)
    assert po == main.with_suffix('.po')
    assert hlp == main.with_suffix('.hlp')
    actual = resolve_catalog_paths({}, main_file=main, project_dir=tmp_path)
    assert actual == (po.resolve(), hlp.resolve())
    relative = resolve_catalog_paths(
        {'input_file': 'catalog/settings.po', 'output_file': 'catalog/settings.hlp'},
        main_file=main, project_dir=tmp_path)
    assert relative == ((tmp_path / 'catalog/settings.po').resolve(),
                        (tmp_path / 'catalog/settings.hlp').resolve())
    with pytest.raises(ValueError, match=r'\.hlp'):
        resolve_catalog_paths({'output_file': 'bad.mo'}, main_file=main, project_dir=tmp_path)


def test_normalize_po_settings_preserves_overrides_and_header_fields():
    state = normalize_po_settings({'input_file': 'file.po', 'output_file': 'file.hlp',
                                   'headers': {'Last-Translator': 'A. Example'}})
    assert state['output_file'] == 'file.hlp'
    assert state['headers']['Last-Translator'] == 'A. Example'
    assert set(state['headers']) == set(HEADER_FIELDS)


def test_actual_help_build_writes_header_to_po_and_hlp_but_no_mo(tmp_path):
    helpdir = tmp_path / 'Sources'
    helpdir.mkdir()
    main = helpdir / 'Start.thlp'
    main.write_text('%topic "index"\nWillkommen!\n', encoding='utf-8')
    exe = tmp_path / 'build' / 'Example.exe'
    po, requested_hlp = default_catalog_paths(main)
    headers = default_po_headers(FakeQSettings({
        'localize/header/Project-Id-Version': 'Turbo Help 1.2',
        'localize/header/Last-Translator': 'Translator',
    }))
    topics, result_po, runtime_hlp = compile_help_sources(
        [main], exe, po_path=po, hlp_path=requested_hlp, metadata=headers)
    assert topics['index'] == 'Willkommen!'
    assert result_po == po
    assert runtime_hlp == exe.with_suffix('.hlp')
    assert requested_hlp.exists() and runtime_hlp.exists()
    assert requested_hlp.read_bytes() == runtime_hlp.read_bytes()
    assert not list(tmp_path.rglob('*.mo')), 'Separate MO-Dateien sind nicht erlaubt'
    content = result_po.read_text(encoding='utf-8')
    assert '"Project-Id-Version: Turbo Help 1.2\\n"' in content
    assert '"Last-Translator: Translator\\n"' in content
    catalog = gettext.GNUTranslations(fp=io.BytesIO(requested_hlp.read_bytes()))
    assert catalog.gettext('index') == 'Willkommen!'
    assert catalog.info()['project-id-version'] == 'Turbo Help 1.2'
    assert catalog.info()['last-translator'] == 'Translator'


def test_linktime_help_keeps_exe_named_hlp_and_no_mo(tmp_path):
    main = tmp_path / 'Main.thlp'
    main.write_text('%topic "index"\nTest\n', encoding='utf8')
    exe = tmp_path / 'Demo.exe'
    exe.write_bytes(b'MZ')
    chosen = tmp_path / 'MyHelp.hlp'
    actual = compile_project_help([main], exe, po_path=tmp_path / 'MyHelp.po',
                                  hlp_path=chosen, metadata=default_po_headers())
    assert chosen.is_file()
    assert actual == tmp_path / 'Demo.hlp'
    assert actual.is_file()
    assert not (tmp_path / 'MyHelp.mo').exists()


def test_gui_and_project_format_use_correct_names_and_callbacks():
    src = (HERE / 'd64_dism.py').read_text(encoding='utf-8')
    assert 'PROJECT_TURBO_PO_SETTINGS_KEY' in src
    assert 'Settings.TurboHelp.PO' in src
    assert 'self._project_turbo_help_settings_open()' in src
    assert 'self.set_project_modified(True)' in src
    assert "'hlp_path': hlp" in src
    assert 'self.project_turbo_po_settings = normalize_po_settings(' in src
    assert 'self.project_turbo_po_settings = default_po_settings(self.settings)' in src
    settings_widget = (HERE / 'turbo_help_po_settings_page.py').read_text(encoding='utf-8')
    assert "QLabel('Input file (*.po):'" in settings_widget
    assert "QLabel('Output file (*.hlp):'" in settings_widget
    assert "'turbo_help_hlp_output'" in settings_widget
    assert 'page.set_data(state, main_file=main_file, project_dir=project_dir)' in (HERE / 'turbo_help_gui.py').read_text(encoding='utf8')
    assert 'mo_path.write_bytes' not in (HERE / 'turbo_help_sidecar.py').read_text(encoding='utf-8')
    gui = (HERE / 'turbo_help_gui.py').read_text(encoding='utf-8')
    assert 'return widget if isinstance(widget, TurboHelpSourceEditor) else None' in gui
