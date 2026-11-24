"""Stage 683: lossless versioned .drectve compression and project checkbox."""
from __future__ import annotations

import re
import struct
from pathlib import Path

import pytest

from d64_coff_metadata import encode_coff_link_metadata, decode_coff_link_metadata
from d64dbase import compile_dbase_to_assembly
from test_stage605_link import _load_pe_linker

ROOT = Path(__file__).resolve().parent


def _drectve(coff: bytes) -> bytes:
    count = struct.unpack_from('<H', coff, 2)[0]
    for number in range(count):
        off = 20 + number * 40
        if coff[off:off+8].rstrip(b'\0') == b'.drectve':
            size, ptr = struct.unpack_from('<II', coff, off+16)
            return coff[ptr:ptr+size]
    return b''


def _modify_drectve(coff: bytes) -> bytes:
    raw = bytearray(coff)
    count = struct.unpack_from('<H', raw, 2)[0]
    for number in range(count):
        off = 20 + number * 40
        if raw[off:off+8].rstrip(b'\0') == b'.drectve':
            size, ptr = struct.unpack_from('<II', raw, off+16)
            assert size > 16
            raw[ptr + size - 2] ^= 0x5a
            return bytes(raw)
    raise AssertionError('no .drectve')


def test_versioned_stream_roundtrip_and_validation():
    raw = (b'{"imports":{"dll":"user32.dll","member":"MessageBoxA"}}' * 80)
    packed = encode_coff_link_metadata(raw, compress=True)
    assert packed.startswith(b'D64JZ\x01')
    assert len(packed) < len(raw)
    assert decode_coff_link_metadata(packed) == raw
    assert decode_coff_link_metadata(raw) == raw
    assert encode_coff_link_metadata(raw) == raw
    for invalid in (packed[:10], packed[:-3], packed + b'x',
                    packed[:6] + struct.pack('<II', 0xFFFFFFFF, 0) + packed[14:]):
        with pytest.raises(ValueError):
            decode_coff_link_metadata(invalid)
    bad_crc = bytearray(packed)
    bad_crc[10] ^= 1
    with pytest.raises(ValueError, match='CRC32'):
        decode_coff_link_metadata(bad_crc)


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_full_coff_assemble_parse_and_link_mixed_objects(target):
    api = _load_pe_linker()
    generated = compile_dbase_to_assembly('? "Hello COFF"', target=target).assembly
    assemble = api['assemble_pe32_coff_object' if target=='pe32' else 'assemble_pe64_coff_object']
    parse = api['parse_coff32_object' if target=='pe32' else 'parse_coff64_object']
    link = api['link_coff32_objects' if target=='pe32' else 'link_coff64_objects']
    old = assemble(generated, compress_metadata=False)
    packed = assemble(generated, compress_metadata=True)
    original_metadata = _drectve(old)
    compressed_metadata = _drectve(packed)
    assert original_metadata.startswith(b'{')
    assert compressed_metadata.startswith(b'D64JZ\x01')
    assert decode_coff_link_metadata(compressed_metadata) == original_metadata
    assert len(compressed_metadata) < len(original_metadata)
    older = parse(old)
    newer = parse(packed)
    assert older.imports == newer.imports
    assert older.exports == newer.exports
    assert older.dll_name == newer.dll_name
    assert older.imports
    assert link((packed,), entry_symbol='_start', gui=True).executable[:2] == b'MZ'
    assert link((old,), entry_symbol='_start', gui=True).executable[:2] == b'MZ'
    with pytest.raises((api['PE32AssemblerError'] if target=='pe32' else api['PE64AssemblerError']),
                       match='Komprimierte COFF-Metadaten'):
        parse(_modify_drectve(packed))


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_project_setting_is_separate_for_both_targets(target):
    source = (ROOT / 'd64_dism.py').read_text('utf8')
    assert f'"dbase_compress_meta_key": "__windows_{target}_dbase_compress_meta__"' in source
    assert '"CompressMetaInformations": "true" if _project_bool_entry(' in source
    assert '("dbase_compress_meta_key", "CompressMetaInformations")' in source
    assert '"Compress Meta Informations", self.dbase_meta_group' in source
    assert 'f"project_windows_{target_tag}_dbase_compress_meta"' in source
    assert 'self.project_settings_panel.set_dbase_compress_meta_enabled(' in source
    assert 'self.set_project_windows_dbase_compress_meta(' in source
    assert 'compress_metadata=(document.is_dbase_document and' in source

