# -*- coding: utf-8 -*-
"""Stage 452: WinError 1/50 NTFS handling and safe DLL deployment."""
from pathlib import Path

import pytest

from d64dbase import pe_dll_pack as pack
from d64dbase.console_runtime import DLL_NAME, EXPORTS
from d64dbase.runtime_builder import create_runtime_dll
from test_stage446_console_dll import get_exports
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).parent


def test_invalid_function_invokes_compact_fallback(monkeypatch, tmp_path):
    dll = tmp_path / 'valid.dll'
    dll.write_bytes(b'MZ' + bytes(200))
    attempts = []
    def invalid_function(*_args):
        raise OSError(1, 'Unzulässige Funktion')
    with monkeypatch.context() as m:
        m.setattr(pack, '_set_ntfs_compression_native', invalid_function)
        m.setattr(pack, '_compact_windows_fallback',
                  lambda path, enabled: attempts.append((path, enabled)) or path)
        m.setattr(pack.os, 'name', 'nt')
        assert pack.set_ntfs_compression(dll, True) == dll
    assert attempts == [(dll, True)]


@pytest.mark.parametrize('code', [1, 5, 32, 50, 87])
def test_all_known_windows_errors_use_verified_fallback(monkeypatch, tmp_path, code):
    dll = tmp_path / 'valid.dll'
    dll.write_bytes(b'MZ' + bytes(200))
    attempts = []
    def fail(*_args):
        raise OSError(code, f'WinError {code}')
    with monkeypatch.context() as m:
        m.setattr(pack, '_set_ntfs_compression_native', fail)
        m.setattr(pack, '_compact_windows_fallback',
                  lambda path, enabled: attempts.append(enabled) or path)
        m.setattr(pack.os, 'name', 'nt')
        assert pack.set_ntfs_compression(dll, True) == dll
    assert attempts == [True]


def test_unexpected_error_is_not_silently_retried(monkeypatch, tmp_path):
    def fail(*_args):
        raise OSError(999, 'Fehler ohne sicheren Fallback')
    def should_not_call(*_args):
        pytest.fail('unexpected compact.exe fallback')
    with monkeypatch.context() as m:
        m.setattr(pack, '_set_ntfs_compression_native', fail)
        m.setattr(pack, '_compact_windows_fallback', should_not_call)
        m.setattr(pack.os, 'name', 'nt')
        with pytest.raises(OSError, match='Fehler ohne sicheren Fallback'):
            pack.set_ntfs_compression(tmp_path / 'whatever.dll')


def test_winerror1_and_compact_failure_has_actionable_filesystem_message(monkeypatch, tmp_path):
    dll = tmp_path / 'valid.dll'
    dll.write_bytes(b'MZ' + bytes(200))
    original = dll.read_bytes()
    def invalid_function(*_args):
        raise OSError(1, 'Unzulässige Funktion')
    def compact_failed(*_args):
        raise OSError('compact.exe: Dateisystem unterstützt kein Komprimieren')
    with monkeypatch.context() as m:
        m.setattr(pack, '_set_ntfs_compression_native', invalid_function)
        m.setattr(pack, '_compact_windows_fallback', compact_failed)
        m.setattr(pack, '_volume_compression_diagnostic',
                  lambda path: 'Ziellaufwerk: T:\\\\; Dateisystem: ReFS; Dateikomprimierung: nicht unterstützt. ')
        m.setattr(pack.os, 'name', 'nt')
        with pytest.raises(OSError, match='NTFS-Ausgabeverzeichnis') as caught:
            pack.set_ntfs_compression(dll)
    message = str(caught.value)
    assert 'ReFS' in message
    assert 'compact.exe' in message
    assert 'pack dll' in message
    assert 'WinError 1/50' in message
    assert dll.read_bytes() == original


@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_expected_winerror_does_not_cancel_build_if_compact_succeeds(monkeypatch, tmp_path, target, machine):
    # Exercise the actual internal PE32 build and export validation. Simulate
    # two filesystem APIs: native FSCTL fails but compact.exe succeeds.
    def invalid_function(*_args):
        raise OSError(1, 'Unzulässige Funktion')
    def compact_success(path, enabled):
        assert enabled
        assert path.name == DLL_NAME
        assert path.read_bytes().startswith(b'MZ')
        return path
    real_compress = pack.set_ntfs_compression
    def simulated_windows_compress(path, enabled=True):
        # Toggle the platform only while entering set_ntfs_compression: a
        # global os.name change would break pathlib.resolve on Linux.
        with monkeypatch.context() as mock_platform:
            mock_platform.setattr(pack.os, 'name', 'nt')
            return real_compress(path, enabled)
    with monkeypatch.context() as m:
        m.setattr(pack, '_set_ntfs_compression_native', invalid_function)
        m.setattr(pack, '_compact_windows_fallback', compact_success)
        m.setattr(pack, 'set_ntfs_compression', simulated_windows_compress)
        # pack_loadable_dll verifies that the MZ/PE bytes are identical.
        ns = linkers()
        created = create_runtime_dll(
            target, tmp_path / 'dll', get_exports=get_exports,
            assemble32=ns['assemble_pe32_object_source'],
            coff32=ns['write_coff32_object'],
            link32=ns['link_coff32_objects'],
            assemble64=ns['assemble_pe64_object_source'],
            coff64=ns['write_coff64_object'],
            link64=ns['link_coff64_objects'],
            pack_dll=True,
        )
    assert created.is_file()
    assert set(EXPORTS).issubset(set(get_exports(created, machine)))
    assert created.read_bytes() == (ROOT / 'd64dbase' / 'bin' / target / DLL_NAME).read_bytes()


def test_filesystem_diagnostic_gracefully_handles_non_windows(tmp_path):
    if pack.os.name != 'nt':
        assert pack._volume_compression_diagnostic(tmp_path) == ''


def test_no_changes_to_windows_ui_build_settings_or_dll_exports():
    src = (ROOT / 'd64_dism.py').read_text('utf-8')
    assert 'QCheckBox("pack dll", runtime_group)' in src
    assert 'QCheckBox("const pool", runtime_group)' in src
    assert 'self.create_dbase_runtime_dll("pe32")' in src
    assert 'self.create_dbase_runtime_dll("pe64")' in src
    assert 'DBaseRuntimeDLLPack' in src
    assert 'DBaseRuntimeConstPool' in src
