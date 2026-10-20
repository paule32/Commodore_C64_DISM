"""Stage 458: DLL-backed UTF-8 WFM operations and PE-embedded UI JSON."""
from pathlib import Path
import json
import re
import struct
import textwrap
import zlib
from dataclasses import replace
import pytest

from test_stage443_wfm_len_event import _compile_wfm_for_test
from test_stage446_real_pe_link import linkers
from test_stage456_wfm_external_ui_json import model_with_controls

HERE = Path(__file__).parent
BRIDGE = (HERE / 'd64qt5' / 'd64qt5_bridge.def').read_text()

FORM = '''Form1 = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE "Straße Äpfel" TO Text
        STORE 2 TO Start
        STORE 3 TO Count
        ? !($(Text, Start, Count))
        ? LOWER($(Text, Start, Count))
        ? $(Text, Start, Count)
        ? !(Text)
        ? LOWER(Text)
        RETURN
ENDCLASS
'''


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_fused_functions_are_single_call_and_link(target):
    assembly = _compile_wfm_for_test(FORM, target=target).assembly
    names = ('DBaseUtf8SubstringUpper', 'DBaseUtf8SubstringLower',
             'DBaseUtf8Substring', 'DBaseUtf8Upper', 'DBaseUtf8Lower')
    for name in names:
        assert assembly.count('    call ' + name + '\n') == 1
        assert f'import {name}, "libd64_qt5.dll", "{name}"' in assembly
        assert re.search(rf'\b{name} @10\d\d\b', BRIDGE)
    assert 'start_convert:' not in assembly
    assert '__wfm_upper_2_loop:' not in assembly
    lk = linkers()
    obj = lk[f'assemble_{target}_object_source'](assembly)
    obj_data = lk[f'write_coff{32 if target=="pe32" else 64}_object'](obj)
    image = lk[f'link_coff{32 if target=="pe32" else 64}_objects'](
        (obj_data,), entry_symbol='__d64_wfm_entry', gui=True).executable
    assert image[:2] == b'MZ'
    assert b'DBaseUtf8SubstringLower' in image


def _json_compiled_image(target, compressed, monkeypatch):
    from d64dbase import wfm as wfm_mod
    from d64dbase.wfm_external_ui import encode_form_ui
    model = model_with_controls()
    monkeypatch.setattr(wfm_mod, 'parse_dbase_wfm', lambda *a, **k: model)
    source = (HERE/'d64_dism.py').read_text(encoding='utf8')
    start = source.index('        def _compile_dbase_wfm_fallback(\n')
    stop = source.index('        def compile_dbase_form(self) -> bool:', start)
    context = {'re': re, 'struct': struct, 'replace': replace,
               '_normalize_project_windows_debug_theme': lambda x: x,
               'AssemblerError': type('AssemblerError',(Exception,),{}),
               'DBASE_WFM_PROPERTY_DEFAULTS_ABI': 1, '__name__': 'test458'}
    exec(compile(textwrap.dedent(source[start:stop]), '<wfm458>', 'exec'),context)
    class Stub:
        _compile_dbase_wfm_fallback = context['_compile_dbase_wfm_fallback']
        project_windows_import_packer = {}
        project_windows_dbase_visual = {target: {'external_ui_components': True,
                                                 'compress_json': compressed}}
        @staticmethod
        def _dbase_wfm_int(props, name, default):
            return int(next((v for k,v in (props or {}).items() if k.casefold()==name.casefold()),default))
        @staticmethod
        def _dbase_wfm_prop(props, name, default=None):
            return next((v for k,v in (props or {}).items() if k.casefold()==name.casefold()),default)
        @staticmethod
        def _dbase_wfm_asm_bytes(value):
            return ', '.join(str(b) for b in str(value).encode('utf8'))
    asm = Stub()._compile_dbase_wfm_fallback(FORM,filename='test458.wfm',target=target).assembly
    lk=linkers()
    obj=lk[f'assemble_{target}_object_source'](asm)
    co=lk[f'write_coff{32 if target=="pe32" else 64}_object'](obj)
    image=lk[f'link_coff{32 if target=="pe32" else 64}_objects'](
        (co,),entry_symbol='__d64_wfm_entry',gui=True).executable
    return image,encode_form_ui(model,compress=compressed)[0]


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
@pytest.mark.parametrize('compress', [False, True])
def test_json_is_actually_in_linked_pe_image(target, compress, monkeypatch):
    image, payload = _json_compiled_image(target,compress,monkeypatch)
    assert image[:2] == b'MZ'
    assert payload in image  # linker did not discard .data
    assert len(payload) > 30
    from d64dbase.wfm_external_ui import find_embedded_form_ui
    embedded = find_embedded_form_ui(image)
    assert any(e['document']['form'] == 'Form1' and e['compressed'] == compress for e in embedded)
    if compress:
        assert image.find(b'{"elements":') == -1
        assert zlib.decompress(payload[4:]).startswith(b'{"elements":')
    else:
        assert b'{"elements":' in image


def test_api_is_name_export_only_and_uses_original_mapping_table():
    header=(HERE/'d64qt5'/'d64_dbase_runtime.hpp').read_text()
    for name in ('DBaseUtf8Substring', 'DBaseUtf8SubstringUpper',
                 'DBaseUtf8SubstringLower','DBaseUtf8Upper','DBaseUtf8Lower'):
        assert name in header
    assert 'g_dbase_runtime_context.upperTable' in header
    assert 'g_dbase_runtime_context.lowerTable' in header
