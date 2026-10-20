# -*- coding: utf-8 -*-
"""Stage 453: packed runtime's FINAL output status and true disk allocation."""
from pathlib import Path
import os
import pytest
from d64dbase.pe_dll_pack import replace_verified_runtime, compression_report
from d64dbase.runtime_builder import create_runtime_dll
from d64dbase.console_runtime import DLL_NAME, EXPORTS
from test_stage446_real_pe_link import linkers
from test_stage446_console_dll import get_exports

ROOT = Path(__file__).parent


def test_recompress_at_final_destination_if_rename_loses_attribute(tmp_path):
    old = tmp_path / DLL_NAME
    old.write_bytes(b'previous DLL')
    temp = tmp_path / 'staging'
    temp.mkdir()
    candidate = temp / DLL_NAME
    candidate.write_bytes(b'MZnew dll')
    markers = []
    compressed = {'value': False}
    def check(path):
        assert path == old
        return compressed['value']
    def repack(path):
        markers.append(path)
        compressed['value'] = True
    assert replace_verified_runtime(candidate, old, pack_dll=True, check=check, repack=repack) == old
    assert markers == [old]
    assert old.read_bytes() == b'MZnew dll'
    assert not candidate.exists()
    assert not (temp / ('.__dbase_runtime_backup_' + DLL_NAME)).exists()


def test_failed_final_pack_rolls_back_previous_dll(tmp_path):
    old = tmp_path / DLL_NAME
    old.write_bytes(b'previous DLL')
    temp = tmp_path / 'staging'
    temp.mkdir()
    candidate = temp / DLL_NAME
    candidate.write_bytes(b'MZnew dll')
    with pytest.raises(OSError, match='nicht NTFS-komprimiert'):
        replace_verified_runtime(candidate, old, pack_dll=True,
                                 check=lambda _: False, repack=lambda _: None)
    assert old.read_bytes() == b'previous DLL'


def test_failing_pack_restores_previous_dll(tmp_path):
    old = tmp_path / DLL_NAME
    old.write_bytes(b'previous DLL')
    staging = tmp_path / 'staging'
    staging.mkdir()
    candidate = staging / DLL_NAME
    candidate.write_bytes(b'MZreplacement')
    def raise_on_pack(_):
        raise OSError('Windows verweigert pack')
    with pytest.raises(OSError, match='Windows verweigert'):
        replace_verified_runtime(candidate, old, pack_dll=True,
                                 check=lambda _: False, repack=raise_on_pack)
    assert old.read_bytes() == b'previous DLL'


def test_failed_final_pack_without_previous_removes_invalid_output(tmp_path):
    dest = tmp_path / DLL_NAME
    staging = tmp_path / 'staging'
    staging.mkdir()
    candidate = staging / DLL_NAME
    candidate.write_bytes(b'MZreplacement')
    with pytest.raises(OSError, match='nicht NTFS-komprimiert'):
        replace_verified_runtime(candidate, dest, pack_dll=True,
                                 check=lambda _: False, repack=lambda _: None)
    assert not dest.exists()


def test_regular_unpacked_replacement(tmp_path):
    dest = tmp_path / DLL_NAME
    dest.write_bytes(b'previous')
    staging = tmp_path / 'staging'
    staging.mkdir()
    candidate = staging / DLL_NAME
    candidate.write_bytes(b'MZnormal')
    replace_verified_runtime(candidate, dest)
    assert dest.read_bytes() == b'MZnormal'


def test_compression_report_does_not_confuse_logical_size_with_packing(tmp_path):
    if os.name == 'nt':
        pytest.skip('NTFS allocation requires a real Windows volume')
    file = tmp_path / DLL_NAME
    file.write_bytes(b'MZ' + bytes(127))
    info = compression_report(file)
    assert info == {'compressed': False, 'logical_bytes': 129,
                    'allocated_bytes': None}


@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_real_internal_dll_build_after_refactor(tmp_path, target, machine):
    ns = linkers()
    result = create_runtime_dll(target, tmp_path / target,
           get_exports=get_exports,
           assemble32=ns['assemble_pe32_object_source'],
           coff32=ns['write_coff32_object'],
           link32=ns['link_coff32_objects'],
           assemble64=ns['assemble_pe64_object_source'],
           coff64=ns['write_coff64_object'],
           link64=ns['link_coff64_objects'])
    assert set(EXPORTS).issubset(set(get_exports(result, machine)))
    assert result.read_bytes().startswith(b'MZ')


def test_ide_prints_confirmed_disk_allocation():
    src = (ROOT / 'd64_dism.py').read_text('utf8')
    assert 'compression_report(destination)' in src
    assert 'NTFS-komprimiert (bestätigt)' in src
    assert 'Ersparnis' in src
    assert 'DBaseRuntimeDLLPack' in src
    assert 'QCheckBox("pack dll", runtime_group)' in src
