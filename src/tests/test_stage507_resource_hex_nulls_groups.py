# -*- coding: utf-8 -*-
"""Stage 507: 8 + 8 byte grouping and visible NULs in UTF-16LE byte-text.

Tests the actual formatter from d64_dism.py without a Qt runtime.
"""
import pytest
from test_stage504_resource_hex_codepage import SCOPE

format_resource_hex = SCOPE['format_resource_hex']


def test_unicode_user_example_exact_8_byte_separator_and_all_nul_dots():
    raw = bytes.fromhex('64 00 72 00 FC 00 63 00 6B 00 74 00 20 00 68 00')
    lines = format_resource_hex(raw, 1200).splitlines()
    assert lines[1].startswith(
        '00000000  64 00 72 00 FC 00 63 00 | 6B 00 74 00 20 00 68 00'
    )
    assert 'd.r.ü.c.k.t. .h.' in lines[1]
    assert lines[1].endswith('drückt h')
    assert '00 = .' in lines[0]
    assert 'Unicode-Text (dekodiert)' in lines[0]


def test_exact_offset_0x140_and_byte_offset_8_separator():
    raw = b'\0' * 0x140 + bytes.fromhex(
        '64 00 72 00 FC 00 63 00 6B 00 74 00 20 00 68 00')
    line = format_resource_hex(raw, 1200).splitlines()[0x140 // 16 + 1]
    assert line.startswith('00000140  64 00 72 00 FC 00 63 00 | 6B 00 74 00 20 00 68 00')
    assert line.endswith('drückt h')


def test_native_stringtable_remains_unicode_even_if_combo_is_utf8():
    raw = b'\x08\x00' + 'Deutsch'.encode('utf-16le') + b'\0\0'
    lines = format_resource_hex(raw, 65001, resource_type=SCOPE['RT_STRING']).splitlines()
    assert 'Windows-UTF-16LE' in lines[0]
    assert 'UTF-8 (Metadaten)' in lines[0]
    assert 'D.e.u.t' in lines[1]
    assert 'Deutsch' in '\n'.join(lines)


@pytest.mark.parametrize('page, value, expected_text', [
    (65001, 'Grüße', 'Grüße'),
    (20127, 'Hello', 'Hello'),
    (1200, 'Grüße', 'Grüße'),
])
def test_encoding_still_respected_with_grouped_bytes(page, value, expected_text):
    raw = SCOPE['_resource_encode_string'](value, page)
    lines = format_resource_hex(raw, page).splitlines()
    assert expected_text in '\n'.join(lines)
    if page == 1200:
        assert 'G.r.ü.ß.e.' in lines[1]
    else:
        assert '00 = .' not in lines[0]


def test_multiple_lines_group_at_8_and_short_last_line_no_ghost_pipe():
    data = bytes(range(24)) + b'AB'
    lines = format_resource_hex(data, 20127).splitlines()
    assert lines[1].startswith('00000000  00 01 02 03 04 05 06 07 | 08 09 0A 0B 0C 0D 0E 0F')
    assert lines[2].startswith('00000010  10 11 12 13 14 15 16 17 | 41 42')
    assert lines[1].index('  ', 10) < lines[1].index('  .')
    assert len(lines) == 3


def test_no_group_separator_for_eight_or_fewer_bytes():
    for length in (1, 7, 8):
        line = format_resource_hex(b'A' * length, 20127).splitlines()[1]
        assert ' | ' not in line
    line = format_resource_hex(b'A' * 9, 20127).splitlines()[1]
    assert '41 41 41 41 41 41 41 41 | 41' in line


def test_utf8_multibyte_straddling_row_remains_decoded():
    raw = b'A' * 15 + '€'.encode('utf-8') + b'\0'
    lines = format_resource_hex(raw, 65001).splitlines()
    assert '€' in lines[2]
    assert '�' not in '\n'.join(lines)
    assert ' | ' in lines[1]
