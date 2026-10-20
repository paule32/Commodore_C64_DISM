"""Stage 461: WUIB transport, bin/json size selection and real PE linking."""
import json
import re
import struct
import textwrap
import zlib
from dataclasses import replace
from pathlib import Path

import pytest

from d64dbase.wfm_external_ui import (
    BINARY_MAGIC, binary_form_ui_from_json, convert_form_ui_json_file,
    decode_form_ui_binary, encode_form_ui, encode_form_ui_smart,
    find_embedded_form_ui, select_form_ui_payload, write_form_ui_bin,
    write_form_ui_json,
)
from test_stage456_wfm_external_ui_json import FORM, model_with_controls
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text('utf8')
BRIDGE = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text('utf8')


def test_binary_json_document_roundtrip_and_smaller_size():
    model = model_with_controls()
    raw, text = encode_form_ui(model)
    binary = binary_form_ui_from_json(text)
    assert binary.startswith(BINARY_MAGIC)
    assert len(binary) < len(raw)
    assert decode_form_ui_binary(binary) == json.loads(text)
    assert decode_form_ui_binary(binary + b'junk', _allow_trailing=True) == json.loads(text)
    with pytest.raises(ValueError):
        decode_form_ui_binary(binary + b'junk')
    with pytest.raises(ValueError):
        decode_form_ui_binary(binary[:-1])
    with pytest.raises(ValueError):
        decode_form_ui_binary(b'WUIB\x09' + binary[5:])
    with pytest.raises(ValueError):
        decode_form_ui_binary(BINARY_MAGIC + b'\xff\xff\xff\xff\x7f')


def test_json_to_bin_file_and_live_source_sidecars(tmp_path):
    source = tmp_path/'Form1.wfm'
    source.write_text(FORM, encoding='utf8')
    _, text = encode_form_ui(model_with_controls())
    json_path = write_form_ui_json(source, text)
    bin_path = write_form_ui_bin(source, text)
    assert json_path.exists() and bin_path.exists()
    assert bin_path == tmp_path/'Form1.ui.bin'
    assert decode_form_ui_binary(bin_path.read_bytes()) == json.loads(text)
    bin_path.unlink()
    assert convert_form_ui_json_file(json_path) == bin_path
    assert bin_path.read_bytes() == binary_form_ui_from_json(text)
    assert write_form_ui_bin(tmp_path/'nonexistent.wfm', text) is None


def _large_repetitive_json(count=200):
    return json.dumps({'version':1,'form':'F','elements':[
        {'path':f'C{i}', 'geometry':[5,6,120,30],
         'font':{'family':'Segoe UI','size':9,'bold':False,
                 'italic':False,'underline':False,'strikeout':False},
         'properties':{'Text':'Button','Enabled':'.T.', 'Color':'#ffffff',
                       'Caption':'Hallo','Another':'Hi'}} for i in range(count)
    ]}, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def test_auto_choice_uses_real_compressed_sizes_and_keeps_json_on_tie():
    _, text = encode_form_ui(model_with_controls())
    small_payload, selected, binary = select_form_ui_payload(
        text, store_binary=True, compress=True)
    assert selected == 'binary'
    assert struct.unpack('>I', small_payload[:4])[0] == len(binary)
    assert zlib.decompress(small_payload[4:]) == binary
    larger = _large_repetitive_json()
    packed, selected, binary = select_form_ui_payload(
        larger, store_binary=True, compress=True)
    assert selected == 'json'
    assert zlib.decompress(packed[4:]) == larger.encode('utf8')
    assert len(packed) <= len(zlib.compress(binary, 9))+4
    for store_binary, compress in [(False,False),(False,True),(True,False)]:
        payload, choice, raw_binary = select_form_ui_payload(
            text, store_binary=store_binary, compress=compress)
        assert choice == ('binary' if store_binary else 'json')
        if not compress:
            assert payload == (raw_binary if store_binary else text.encode('utf8'))
    assert encode_form_ui_smart(model_with_controls(), store_binary=True,compress=True)[3] == 'binary'


def test_settings_and_bridge_have_binary_aware_plumbing():
    for target in ('pe32','pe64'):
        assert f'__windows_{target}_dbase_store_binary__' in SOURCE
    for token in ('"store binary data"','StoreBinaryData',
                  'dbase_store_binary_key', 'store_binary_data',
                  'write_form_ui_bin(filename, external_ui_json)',
                  'encode_form_ui_smart(model, store_binary=_store_binary'):
        assert token in SOURCE
    assert 'dbase_wui_decode_binary' in BRIDGE
    assert 'bytes.startsWith(QByteArray("WUIB\\x01", 5))' in BRIDGE
    assert 'DBaseQtWidgetSetProperty(widget' in BRIDGE
    assert 'DBaseQtObjectBindEvent' in SOURCE


def compile_binary_ui(target, binary, compressed, monkeypatch, tmp_path):
    import d64dbase.wfm as wfm
    model = model_with_controls()
    monkeypatch.setattr(wfm, 'parse_dbase_wfm', lambda *a, **k: model)
    start = SOURCE.index('        def _compile_dbase_wfm_fallback(\n')
    stop = SOURCE.index('        def compile_dbase_form(self) -> bool:', start)
    env = {'re':re, 'struct':struct, 'replace':replace,
           '_normalize_project_windows_debug_theme':lambda s:s,
           'AssemblerError':type('AssemblerError',(Exception,),{}),
           'DBASE_WFM_PROPERTY_DEFAULTS_ABI':1,'__name__':'test461'}
    exec(compile(textwrap.dedent(SOURCE[start:stop]), '<test461>', 'exec'),env)
    class Stub:
        _compile_dbase_wfm_fallback = env['_compile_dbase_wfm_fallback']
        project_windows_import_packer = {}
        project_windows_dbase_visual = {target:{
            'external_ui_components': True, 'compress_json': compressed,
            'store_binary_data': binary}}
        @staticmethod
        def _dbase_wfm_int(props,name,default):
            return int(next((v for k,v in (props or {}).items() if k.casefold()==name.casefold()),default))
        @staticmethod
        def _dbase_wfm_prop(props,name,default=None):
            return next((v for k,v in (props or {}).items() if k.casefold()==name.casefold()),default)
        @staticmethod
        def _dbase_wfm_asm_bytes(value):
            return ', '.join(str(b) for b in str(value).encode('utf8'))
    wfm_file=tmp_path/f'{target}_{int(binary)}_{int(compressed)}.wfm'
    wfm_file.write_text(FORM,encoding='utf8')
    asm=Stub()._compile_dbase_wfm_fallback(FORM, filename=str(wfm_file),target=target).assembly
    expected, original, binary_content, chosen = encode_form_ui_smart(
        model, store_binary=binary, compress=compressed)
    assert wfm_file.with_suffix('.ui.json').exists()
    if binary:
        assert wfm_file.with_suffix('.ui.bin').read_bytes() == binary_content
    else:
        assert not wfm_file.with_suffix('.ui.bin').exists()
    assert f'; WFM UI payload: {chosen}, ' in asm
    assert 'call DBaseQtFormApplyExternalUi' in asm
    assert 'call DBaseQtObjectBindEvent' in asm
    if target=='pe32':
        assert f'    push {int(compressed)}\n' in asm
    else:
        assert f'    mov dword ptr [rsp+32], {int(compressed)}\n' in asm
    return asm,expected,chosen


@pytest.mark.parametrize('target',['pe32','pe64'])
@pytest.mark.parametrize('binary,compressed',[(False,False),(False,True),(True,False),(True,True)])
def test_real_pe_assemblies_embed_auto_selected_payload(target,binary,compressed,monkeypatch,tmp_path):
    asm,expected,chosen=compile_binary_ui(target,binary,compressed,monkeypatch,tmp_path)
    lk=linkers()
    obj=lk[f'assemble_{target}_object_source'](asm)
    co=lk[f'write_coff{32 if target=="pe32" else 64}_object'](obj)
    image=lk[f'link_coff{32 if target=="pe32" else 64}_objects'](
        (co,),entry_symbol='__d64_wfm_entry',gui=True).executable
    assert image.startswith(b'MZ')
    assert expected in image
    discovered=find_embedded_form_ui(image)
    assert any(e['document']['form']=='Form1' and e['format']==chosen
               and e['compressed']==compressed for e in discovered)
