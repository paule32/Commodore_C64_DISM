# -*- coding: utf-8 -*-
"""Stage 450: independent PE32/PE32+ NTFS compression selection and safety."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from d64dbase.console_runtime import DLL_NAME, EXPORTS
from d64dbase.pe_dll_pack import pack_loadable_dll, is_ntfs_compressed, set_ntfs_compression
from d64dbase.runtime_builder import create_runtime_dll
from test_stage446_real_pe_link import linkers
from test_stage446_console_dll import pe_info, get_exports

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text('utf8')


def _create(target, folder, *, pack_dll=False, compressor=None):
    ns = linkers()
    return create_runtime_dll(target, folder, get_exports=get_exports,
                              assemble32=ns['assemble_pe32_object_source'],
                              coff32=ns['write_coff32_object'],
                              link32=ns['link_coff32_objects'],
                              assemble64=ns['assemble_pe64_object_source'],
                              coff64=ns['write_coff64_object'],
                              link64=ns['link_coff64_objects'],
                              pack_dll=pack_dll, compressor=compressor)


def test_architecture_specific_checkbox_exists_at_environment_input():
    assert 'self.console_runtime_pack_checkbox = QCheckBox("pack dll", runtime_group)' in SOURCE
    assert 'f"project_windows_{target_tag}_dbase_runtime_pack"' in SOURCE
    assert 'input_layout.addWidget(runtime_group)' in SOURCE
    assert 'self.console_runtime_pack_checkbox.toggled.connect(self._console_runtime_pack_changed)' in SOURCE
    assert 'project_windows_console_dll_pack' in SOURCE
    assert 'self.console_runtime_directory_edit = QLineEdit(runtime_group)' in SOURCE


def test_both_architecture_flags_persist_in_project_ini_and_entries():
    for target in ('pe32', 'pe64'):
        assert f'"__windows_{target}_console_dll_pack__"' in SOURCE
    assert 'DBaseRuntimeDLLPack' in SOURCE
    assert '"DBaseRuntimeDLLPack", fallback="false"' in SOURCE
    assert 'entries[_settings["console_dll_pack_key"]]' in SOURCE
    assert 'self.set_project_windows_console_dll_pack(' in SOURCE
    assert 'panel.set_console_runtime_pack(' in SOURCE
    assert '"pe32": False,\n                "pe64": False,' in SOURCE


def test_tool_menu_and_settings_share_pack_choice():
    assert 'pack_dll=bool(self.project_windows_console_dll_pack.get(key, False))' in SOURCE
    assert 'self.create_dbase_runtime_dll("pe32")' in SOURCE
    assert 'self.create_dbase_runtime_dll("pe64")' in SOURCE
    assert 'pack_dll=bool(self.project_windows_console_dll_pack.get(' in SOURCE


@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_real_pe_dll_build_with_mocked_transparent_filesystem_pack(tmp_path, target, machine):
    called = []
    def simulate_ntfs(path, enabled):
        assert enabled is True
        called.append(path)
        assert path.name == DLL_NAME
        assert path.read_bytes().startswith(b'MZ')

    result = _create(target, tmp_path / target, pack_dll=True, compressor=simulate_ntfs)
    assert len(called) == 1
    assert called[0] != result  # only a validated temporary file is packed
    assert pe_info(result)[0] == machine
    assert set(EXPORTS).issubset(pe_info(result)[1])
    assert result.read_bytes() == (ROOT / 'd64dbase' / 'bin' / target / DLL_NAME).read_bytes()


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_build_without_pack_does_not_invoke_compression(tmp_path, target):
    result = _create(target, tmp_path / target, pack_dll=False,
                     compressor=lambda *_args: pytest.fail('unexpected compression'))
    assert result.is_file()


def test_pack_failure_preserves_previously_valid_destination(tmp_path):
    directory = tmp_path / 'pe32'
    result = _create('pe32', directory)
    original = result.read_bytes()
    def fail(*_args):
        raise OSError('NTFS unsupported')
    with pytest.raises(OSError, match='NTFS unsupported'):
        _create('pe32', directory, pack_dll=True, compressor=fail)
    assert result.read_bytes() == original
    assert set(EXPORTS).issubset(pe_info(result)[1])


def test_compressor_must_preserve_loader_visible_pe_content(tmp_path):
    path = tmp_path / DLL_NAME
    path.write_bytes((ROOT / 'd64dbase' / 'bin' / 'pe32' / DLL_NAME).read_bytes())
    digest = hashlib.sha256(path.read_bytes()).digest()
    assert pack_loadable_dll(path, compressor=lambda path, enabled: None) == path
    assert hashlib.sha256(path.read_bytes()).digest() == digest
    def corrupt(path, enabled):
        path.write_bytes(path.read_bytes().replace(b'MZ', b'ZZ', 1))
    with pytest.raises(ValueError, match='PE-Dateiinhalt'):
        pack_loadable_dll(path, compressor=corrupt)


def test_compressed_container_is_rejected_as_output(tmp_path):
    path = tmp_path / DLL_NAME
    path.write_bytes(b'PK\x03\x04' + b'\0' * 200)
    with pytest.raises(ValueError, match='PE-Datei'):
        pack_loadable_dll(path, compressor=lambda *_: None)


@pytest.mark.skipif(os.name == 'nt', reason='Checks Linux-only unsupported-platform behavior')
def test_ntfs_pack_requires_windows_and_does_not_change_pe_on_failure(tmp_path):
    path = tmp_path / DLL_NAME
    path.write_bytes((ROOT / 'd64dbase' / 'bin' / 'pe64' / DLL_NAME).read_bytes())
    before = path.read_bytes()
    with pytest.raises(OSError, match='Windows und ein NTFS'):
        pack_loadable_dll(path)
    assert path.read_bytes() == before
    assert not is_ntfs_compressed(path)
    assert set_ntfs_compression(path, False) == path


def test_no_portable_exe_packer_is_misrepresented_as_ntfs_pack():
    text = (ROOT / 'd64dbase' / 'pe_dll_pack.py').read_text('utf8')
    assert 'FSCTL_SET_COMPRESSION' in text
    assert 'CreateFileW' in text
    assert 'DeviceIoControl' in text
    assert 'COMPRESSION_FORMAT_DEFAULT' in text
    assert 'loader' in text
    assert 'NTFS' in text

@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_runtime_deployment_uses_packing_flag_without_changing_pe_bytes(
        tmp_path, monkeypatch, target):
    import d64dbase.console_runtime as runtime
    import d64dbase.pe_dll_pack as packing
    package_dir = ROOT / 'd64dbase'
    packed_calls = []
    def fake_pack(path):
        packed_calls.append(path)
        assert path.read_bytes().startswith(b'MZ')
        return path
    monkeypatch.setattr(packing, 'pack_loadable_dll', fake_pack)
    monkeypatch.setattr(packing, 'is_ntfs_compressed', lambda path: False)
    output = tmp_path / target / 'Form1.exe'
    result = runtime.deploy_runtime(output, target, get_exports=get_exports,
                                    package_root=package_dir, pack_dll=True)
    assert result == output.parent / DLL_NAME
    assert packed_calls
    assert result.read_bytes() == (package_dir / 'bin' / target / DLL_NAME).read_bytes()


def test_failed_compression_during_deployment_leaves_existing_file_untouched(
        tmp_path, monkeypatch):
    import d64dbase.console_runtime as runtime
    import d64dbase.pe_dll_pack as packing
    dest = tmp_path / DLL_NAME
    dest.write_bytes((ROOT / 'd64dbase' / 'bin' / 'pe32' / DLL_NAME).read_bytes())
    before = dest.read_bytes()
    # Packaged DLL is newer than the existing valid DLL by bytes -> force copy.
    # Existing file remains untouched if compression raises after staging.
    fake_package = tmp_path / 'packaged'
    staged = fake_package / 'bin' / 'pe32'
    staged.mkdir(parents=True)
    new_dll = (ROOT / 'd64dbase' / 'bin' / 'pe32' / DLL_NAME).read_bytes()
    staged.joinpath(DLL_NAME).write_bytes(new_dll + b'\0')
    def raise_pack(path):
        raise OSError('NTFS unavailable')
    monkeypatch.setattr(packing, 'pack_loadable_dll', raise_pack)
    with pytest.raises(OSError, match='NTFS unavailable'):
        runtime.deploy_runtime(tmp_path / 'Form1.exe', 'pe32', get_exports=get_exports,
                               package_root=fake_package, pack_dll=True)
    assert dest.read_bytes() == before
