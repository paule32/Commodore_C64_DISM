# -*- coding: utf-8 -*-
"""Stage 513: win32/win64 resource DLL output grouped by active codepage."""
from pathlib import Path

import pytest

from test_stage504_resource_hex_codepage import SCOPE
from test_stage512_resource_dll import _pe_headers, _leaf_values


@pytest.mark.parametrize('machine,architecture', [('x86', 'win32'), ('x64', 'win64')])
@pytest.mark.parametrize('page,folder,text', [
    (1200, 'unicode', 'Grüße'),
    (65001, 'utf8', 'Grüße'),
    (20127, 'ascii', 'Hallo'),
])
def test_selected_codepage_output_directory_and_resource_bytes(tmp_path, machine, architecture, page, folder, text):
    rc = tmp_path / 'Resource32.rc'
    rc.write_text(f'#pragma code_page({page})\n101 RCDATA\nBEGIN\n "{text}"\nEND\n', encoding='utf8')
    entries = SCOPE['compile_rc'](rc).entries
    paths = SCOPE['build_resource_dll_files'](rc, entries, machine=machine, codepage=page)
    assert all(p.parent == tmp_path / architecture / folder for p in paths)
    assert [p.name for p in paths] == ['Resource32.res', 'Resource32.o', 'Resource32.dll']
    assert all(p.is_file() for p in paths)
    assert not list((tmp_path / architecture).glob('Resource32.*'))
    assert [e.data for e in SCOPE['read_res'](paths[0])] == [e.data for e in entries]
    blob = paths[2].read_bytes()
    header = _pe_headers(blob)
    assert header['machine'] == (0x14c if machine == 'x86' else 0x8664)
    assert len(_leaf_values(header['data'])) == 1
    assert entries[0].data in blob


def test_all_six_build_destinations_coexist(tmp_path):
    src = tmp_path / 'Resource32.rc'
    contents = {}
    for page, folder, text in [(1200, 'unicode', 'Grüße'), (65001, 'utf8', 'Grüße'), (20127, 'ascii', 'Hallo')]:
        src.write_text(f'#pragma code_page({page})\n101 RCDATA\nBEGIN\n "{text}"\nEND\n', encoding='utf8')
        entries = SCOPE['compile_rc'](src).entries
        for arch in ('x86', 'x64'):
            res, obj, dll = SCOPE['build_resource_dll_files'](src, entries, machine=arch)
            assert dll.parent.name == folder
            assert res.read_bytes() and obj.read_bytes() and dll.read_bytes()
            contents[(arch, folder)] = (res.read_bytes(), obj.read_bytes(), dll.read_bytes())
    assert len(contents) == 6
    for (arch, folder), blobs in contents.items():
        parent = src.parent / ('win32' if arch == 'x86' else 'win64') / folder
        assert [p.name for p in sorted(parent.iterdir())] == ['Resource32.dll', 'Resource32.o', 'Resource32.res']
        assert (parent/'Resource32.res').read_bytes() == blobs[0]
        assert (parent/'Resource32.o').read_bytes() == blobs[1]
        assert (parent/'Resource32.dll').read_bytes() == blobs[2]
    assert contents[('x86', 'unicode')][0] != contents[('x86', 'utf8')][0]


@pytest.mark.parametrize('selected,folder', [
    ('Unicode', 'unicode'), ('UTF-16LE', 'unicode'), ('UTF-8', 'utf8'),
    ('ASCII', 'ascii'), (1200, 'unicode'), (65001, 'utf8'), (20127, 'ascii'),
    (0, 'unicode'),
])
def test_codepage_mapping_and_legacy_res_default(selected, folder):
    assert SCOPE['resource_dll_codepage_directory'](selected) == folder


def test_unsupported_codepage_does_not_create_folders(tmp_path):
    rc = tmp_path / 'Resource32.rc'
    rc.write_text('#pragma code_page(1200)\n101 RCDATA\nBEGIN\n "Hello"\nEND\n', encoding='utf8')
    entries = SCOPE['compile_rc'](rc).entries
    with pytest.raises(SCOPE['ResourceCompilerError'], match='Codepage'):
        SCOPE['build_resource_dll_files'](rc, entries, machine='x86', codepage=1252)
    assert not (tmp_path/'win32').exists()


def test_gui_uses_active_codepage_combo_before_rebuilding_resources():
    source = Path(__file__).with_name('d64_dism.py').read_text('utf8')
    helper = source[source.index('    def _selected_dll_codepage(self)'):source.index('    def compile_to_resource_dll(', source.index('    def _selected_dll_codepage(self)'))]
    assert 'getattr(self, "properties"' in helper and 'combo.currentData()' in helper
    fn = source[source.index('    def compile_to_resource_dll(self, machine: str) -> bool:'):source.index('    def compile_to_coff(',source.index('    def compile_to_resource_dll(self, machine: str) -> bool:'))]
    assert fn.index('self._selected_dll_codepage()') < fn.index('self._compile_current_rc()')
    assert 'codepage=selected_page' in fn
    assert 'self.set_target(' not in fn


def test_gui_click_uses_saved_combo_choice_even_if_compile_rebuilds_properties(tmp_path):
    """Simulate the real button handler without requiring PyQt5 to be installed."""
    import textwrap
    source = Path(__file__).with_name('d64_dism.py').read_text('utf8')
    start = source.index('    def _selected_dll_codepage(self)')
    end = source.index('    def compile_to_coff(', start)
    scope = {
        'ResourceCompilerError': SCOPE['ResourceCompilerError'],
        'build_resource_dll_files': SCOPE['build_resource_dll_files'],
        'Optional': __import__('typing').Optional,
    }
    exec(textwrap.dedent(source[start:end]), scope)
    path = tmp_path/'Resource32.rc'
    path.write_text('#pragma code_page(65001)\n101 RCDATA\nBEGIN\n "Grüße"\nEND\n', encoding='utf8')

    class Combo:
        def objectName(self):
            return 'resource_codepage_combo'
        def currentData(self):
            return 65001

    class Props:
        def cellWidget(self, row, col):
            assert (row, col) == (8, 1)
            return Combo()

    class GUI:
        _selected_dll_codepage = scope['_selected_dll_codepage']
        compile_to_resource_dll = scope['compile_to_resource_dll']
        _resource_build_options = scope['_resource_build_options']
        def __init__(self):
            self.properties = Props()
            self.current_path = path
            self.entries = []
            self.errors = []
            self.messages = []
            self.target = 'pe64'  # The DLL build must not change the selected editor target.
        def _compile_current_rc(self):
            self.entries = SCOPE['compile_rc'](path).entries
            # The real editor recreates the property table during recompilation.
            self.properties = None
        def set_target(self, target):
            self.target = target
        def _set_status(self, value):
            self.messages.append(value)
        def _critical(self, title, message):
            self.errors.append((title, message))

    gui = GUI()
    assert gui.compile_to_resource_dll('x86') is True
    assert not gui.errors
    assert gui.target == 'pe64'
    assert (tmp_path/'win32'/'utf8'/'Resource32.dll').exists()
    assert 'win32' in gui.messages[-1] and 'utf8' in gui.messages[-1]
