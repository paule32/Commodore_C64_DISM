# -*- coding: utf-8 -*-
"""Stage 519: project environment is read LIVE when either DLL button is clicked."""
from __future__ import annotations
from pathlib import Path

import pytest
from test_stage504_resource_hex_codepage import SCOPE
from test_stage516_resource_mapping import _method, _execute


class FakePage:
    def __init__(self, *, ascii=False, utf8=False, enabled=False, mode='transparent'):
        self.state = {'ascii': ascii, 'utf8': utf8, 'enabled': enabled, 'mode': mode}

    def resource_build_settings(self):
        return dict(self.state)


class FakePanel:
    def __init__(self, p32, p64):
        self.pages = {'pe32': p32, 'pe64': p64}

    def page_for_target(self, target):
        return self.pages[target]


def make_host():
    namespace = {}
    _execute(_method('project_windows_resource_build_settings'), namespace)

    class Host:
        _project_windows_target_key = lambda self, target: 'pe64' if str(target) in ('pe64', 'win64') else 'pe32'
        project_windows_resource_mapping = {
            'pe32': {'ascii': False, 'utf8': False},
            'pe64': {'ascii': False, 'utf8': False},
        }
        project_windows_resource_compression = {
            'pe32': {'enabled': False, 'mode': 'transparent'},
            'pe64': {'enabled': False, 'mode': 'transparent'},
        }
        project_windows_resource_build_settings = namespace['project_windows_resource_build_settings']
    host = Host()
    p32, p64 = FakePage(utf8=True, enabled=True, mode='custom'), FakePage()
    host.project_settings_panel = FakePanel(p32, p64)
    return host, p32, p64


def test_live_windows_settings_override_cache_and_are_abi_specific():
    host, page32, page64 = make_host()
    # Project cache still says WITHOUT and compression disabled, yet the UI is live.
    assert host.project_windows_resource_build_settings('pe32') == {
        'ascii': False, 'utf8': True, 'enabled': True, 'mode': 'custom'}
    assert host.project_windows_resource_build_settings('pe64') == {
        'ascii': False, 'utf8': False, 'enabled': False, 'mode': 'transparent'}
    # No rebuild of editor/settings panel required after UI changes.
    page32.state['utf8'] = False
    page64.state.update(utf8=True, enabled=True, mode='custom')
    assert host.project_windows_resource_build_settings('pe32')['utf8'] is False
    assert host.project_windows_resource_build_settings('pe64')['utf8'] is True
    # Also works before the settings dock was ever created.
    host.project_settings_panel = None
    assert host.project_windows_resource_build_settings('pe64')['enabled'] is False


def make_editor(tmp_path, host, page=65001):
    namespace = {'ResourceCompilerError': SCOPE['ResourceCompilerError'],
                 'build_resource_dll_files': SCOPE['build_resource_dll_files']}
    for name in ('_resource_build_options', 'compile_to_resource_dll'):
        _execute(_method(name), namespace)
    source = tmp_path/'Resource.rc'
    source.write_text('''#pragma code_page(65001)
STRINGTABLE
BEGIN
  1 "Drück mich"
END
100 MENU
BEGIN
 POPUP "Datei"
 BEGIN
 MENUITEM "Öffnen", 3011
 END
END
200 RCDATA
BEGIN
 "'''+('ABCD'*200)+'''"
END
''', encoding='utf8')

    class Editor:
        current_path = source
        resource_build_settings_provider = host.project_windows_resource_build_settings
        _resource_build_options = namespace['_resource_build_options']
        compile_to_resource_dll = namespace['compile_to_resource_dll']
        _selected_dll_codepage = lambda self: page
        def __init__(self):
            self.entries = []
            self.errors = []
            self.status = ''
        def _compile_current_rc(self):
            self.entries = SCOPE['compile_rc'](source).entries
        def set_target(self, target):
            self.current_target = target
        def _set_status(self, message):
            self.status = message
        def _critical(self, title, message):
            self.errors.append((title, message))
    return Editor(), source


def test_both_buttons_use_different_live_mapping_and_compression(tmp_path):
    host, page32, page64 = make_host()
    editor, source = make_editor(tmp_path, host)
    assert editor.compile_to_resource_dll('x86') is True, editor.errors
    res32 = SCOPE['read_res'](tmp_path/'win32'/'utf8'/'Resource.res')
    dll32 = (tmp_path/'win32'/'utf8'/'Resource.dll').read_bytes()
    assert {6, 0xF006, 4, 0xF004} <= {e.type_id for e in res32}
    assert b'D64PK001' in dll32
    assert 'Compress DLL: custom' in editor.status
    assert 'mit UTF-16LE-Kopie' in editor.status

    assert editor.compile_to_resource_dll('x64') is True, editor.errors
    res64 = SCOPE['read_res'](tmp_path/'win64'/'utf8'/'Resource.res')
    dll64 = (tmp_path/'win64'/'utf8'/'Resource.dll').read_bytes()
    assert {e.type_id for e in res64} >= {0xF004, 0xF006}
    assert 4 not in {e.type_id for e in res64} and 6 not in {e.type_id for e in res64}
    assert b'D64PK001' not in dll64
    assert 'Compress DLL: aus' in editor.status
    assert 'ohne UTF-16LE-Kopie' in editor.status

    # Change settings AFTER creating the editor and perform builds again.
    page32.state.update(utf8=False, enabled=False)
    page64.state.update(utf8=True, enabled=True, mode='custom')
    assert editor.compile_to_resource_dll('x86') is True, editor.errors
    assert b'D64PK001' not in (tmp_path/'win32'/'utf8'/'Resource.dll').read_bytes()
    assert {e.type_id for e in SCOPE['read_res'](tmp_path/'win32'/'utf8'/'Resource.res')} == {
        0xF004, 0xF006, 10}
    assert editor.compile_to_resource_dll('x64') is True, editor.errors
    assert b'D64PK001' in (tmp_path/'win64'/'utf8'/'Resource.dll').read_bytes()
    assert {4, 6, 0xF004, 0xF006} <= {e.type_id for e in SCOPE['read_res'](
        tmp_path/'win64'/'utf8'/'Resource.res')}


def test_build_options_support_existing_standalone_editor_providers():
    namespace = {'ResourceCompilerError': SCOPE['ResourceCompilerError']}
    _execute(_method('_resource_build_options'), namespace)
    class Editor:
        _resource_build_options = namespace['_resource_build_options']
        resource_mapping_provider = lambda self, target: {'ascii': target == 'pe32', 'utf8': target == 'pe64'}
        resource_compression_provider = lambda self, target: {'enabled': target == 'pe64', 'mode': 'custom'}
    editor = Editor()
    assert editor._resource_build_options('x86', 20127)['include_native_utf16'] is True
    assert editor._resource_build_options('x64', 65001)['compress_enabled'] is True
    assert editor._resource_build_options('x64', 1200)['include_native_utf16'] is False


def test_wiring_uses_live_provider_when_opening_or_reusing_dock():
    src=Path(__file__).with_name('d64_dism.py').read_text('utf8')
    assert 'editor.resource_build_settings_provider = self.project_windows_resource_build_settings' in src
    assert src.count('editor.resource_build_settings_provider = self.project_windows_resource_build_settings') == 2
    region=src.split('    def compile_to_resource_dll(self, machine: str) -> bool:',1)[1].split(
        '    def compile_to_coff(self, machine: str):',1)[0]
    assert 'options = self._resource_build_options(machine, effective_page)' in region
    for arg in ('include_native_utf16', 'compress_enabled', 'compress_mode'):
        assert f'{arg}=options["{arg}"]' in region


def test_win32_transparent_settings_passed_to_builder_including_ascii_copy(tmp_path):
    """Windows NTFS itself is not available here; verify the GUI's exact args."""
    host, page32, _page64 = make_host()
    page32.state.update(ascii=True, utf8=False, enabled=True, mode='transparent')
    calls=[]
    def fake_builder(*args, **kwargs):
        calls.append(kwargs)
        return tuple(tmp_path/name for name in ('result.res','result.o','result.dll'))
    ns={'ResourceCompilerError':SCOPE['ResourceCompilerError'],
        'build_resource_dll_files':fake_builder}
    for name in ('_resource_build_options','compile_to_resource_dll'):
        _execute(_method(name),ns)
    class Editor:
        current_path=tmp_path/'Test.rc'
        _selected_dll_codepage=lambda self:20127
        resource_build_settings_provider=host.project_windows_resource_build_settings
        _resource_build_options=ns['_resource_build_options']
        compile_to_resource_dll=ns['compile_to_resource_dll']
        def __init__(self):
            self.errors=[]
            self.status=''
            self.entries=[]
        def _compile_current_rc(self):
            self.entries=SCOPE['compile_rc'](self.current_path).entries
        def set_target(self,target):self.current_target=target
        def _set_status(self,s):self.status=s
        def _critical(self,*args):self.errors.append(args)
    Editor.current_path.write_text('#pragma code_page(20127)\nSTRINGTABLE\nBEGIN\n1 "Hello"\nEND\n',encoding='utf8')
    editor=Editor()
    assert editor.compile_to_resource_dll('x86') is True,editor.errors
    assert calls==[dict(machine='x86',codepage=20127,
                        include_native_utf16=True,compress_enabled=True,
                        compress_mode='transparent')]
    assert 'Compress DLL: transparent' in editor.status
