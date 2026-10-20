"""Stage 456: WFM UI JSON serializer, settings wiring, actual PE linker builds."""
from pathlib import Path
import json
import struct
import zlib
import re
import pytest
from d64dbase.wfm_external_ui import encode_form_ui, write_form_ui_json
from d64dbase.wfm import DBaseWfmControl, parse_dbase_wfm
from test_stage451_wfm_size_optimizations import compile_wfm, FORM
from test_stage446_real_pe_link import linkers

ROOT = Path(__file__).parent
TEXT = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
BRIDGE = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')


def model_with_controls():
    model = parse_dbase_wfm(FORM)
    model.properties.update({'Left': 180, 'Width': 710, 'Text': 'Übersicht'})
    model.controls.append(DBaseWfmControl(
        path='THIS.ButtonA', class_name='PUSHBUTTON', parent_path='THIS',
        properties={'Left': 10, 'Top': 40, 'Width': 190, 'Height': 32,
                    'Text': 'Grüße', 'Enabled': False, 'ToolTip': 'Klicken'},
        order=1, events={'OnClick': 'PushButton1_onClick'}))
    return model


def test_json_writer_payload_and_compression_roundtrip():
    model = model_with_controls()
    plain, text = encode_form_ui(model, compress=False)
    zipped, text2 = encode_form_ui(model, compress=True)
    assert text == text2 and plain == text.encode('utf-8')
    assert json.loads(text)['elements'][1]['properties']['ToolTip'] == 'Klicken'
    assert json.loads(text)['elements'][1]['properties']['Text'] == 'Grüße'
    assert json.loads(text)['elements'][0]['geometry'][2] == 710
    assert struct.unpack('>I', zipped[:4])[0] == len(plain)
    assert zlib.decompress(zipped[4:]) == plain
    assert len(zipped) < len(plain)


def test_sidecar_only_for_real_wfm(tmp_path):
    source = tmp_path / 'Form1.wfm'
    source.write_text(FORM, 'utf-8')
    _, content = encode_form_ui(model_with_controls())
    sidecar = write_form_ui_json(source, content)
    assert sidecar == tmp_path / 'Form1.ui.json'
    assert json.loads(sidecar.read_text('utf-8'))['version'] == 1
    assert write_form_ui_json(tmp_path/'missing.wfm', content) is None


def test_settings_persistence_navigation_and_callbacks():
    for t in ('pe32', 'pe64'):
        assert f'__windows_{t}_dbase_external_ui__' in TEXT
        assert f'__windows_{t}_dbase_compress_json__' in TEXT
    for token in ('compiler.dbase.optimization', 'Visuelle Elemente',
                  'external UI components', 'compress json',
                  'ExternalUIComponents', 'CompressJson',
                  'set_project_windows_dbase_visual_settings',
                  'getattr(self, "project_windows_dbase_visual", {}).get(_opt_target, {})'):
        assert token in TEXT
    assert 'DBaseQtFormApplyExternalUi' in BRIDGE
    assert 'qUncompress(bytes)' in BRIDGE
    assert 'QJsonDocument::fromJson(bytes' in BRIDGE


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
@pytest.mark.parametrize('compress', [False, True])
def test_external_ui_compiles_links_and_omits_per_property_calls(target, compress, monkeypatch):
    import d64dbase.wfm as wfm_mod
    model = model_with_controls()
    monkeypatch.setattr(wfm_mod, 'parse_dbase_wfm', lambda *a, **k: model)
    from test_stage451_wfm_size_optimizations import compile_wfm as old_compiler
    # Stage-451 helper supplies an external compiler stub; activate Stage-456 settings by
    # temporarily adjusting its fake self through the method's class closure equivalent.
    # Use a local adaptation of the source-driven extraction for architecture tests.
    import textwrap
    import struct as std_struct
    from dataclasses import replace
    source = TEXT
    start = source.index('        def _compile_dbase_wfm_fallback(\n')
    stop = source.index('        def compile_dbase_form(self) -> bool:', start)
    env = {'re': re, 'struct': std_struct, 'replace': replace,
           '_normalize_project_windows_debug_theme': lambda s: s,
           'AssemblerError': type('AssemblerError', (Exception,), {}),
           'DBASE_WFM_PROPERTY_DEFAULTS_ABI': 1, '__name__': 'test456'}
    exec(compile(textwrap.dedent(source[start:stop]), '<wfm456>', 'exec'), env)
    class Stub:
        _compile_dbase_wfm_fallback = env['_compile_dbase_wfm_fallback']
        project_windows_import_packer = {}
        project_windows_dbase_visual = {'pe32': {'external_ui_components': True, 'compress_json': compress},
                                        'pe64': {'external_ui_components': True, 'compress_json': compress}}
        @staticmethod
        def _dbase_wfm_int(props, name, default):
            return int(next((v for k,v in (props or {}).items() if k.lower()==name.lower()), default))
        @staticmethod
        def _dbase_wfm_prop(props, name, default=None):
            return next((v for k,v in (props or {}).items() if k.lower()==name.lower()), default)
        @staticmethod
        def _dbase_wfm_asm_bytes(value):
            return ', '.join(str(b) for b in (str(value).encode('utf-8')+b'\0'))
    asm = Stub()._compile_dbase_wfm_fallback(FORM,filename='fake456.wfm',target=target).assembly
    assert 'call DBaseQtFormApplyExternalUi' in asm
    assert 'import DBaseQtFormApplyExternalUi, "libd64_qt5.dll", "DBaseQtFormApplyExternalUi"' in asm
    assert '__dbase_wfm_external_ui_payload:' in asm
    assert '__dbase_wfm_external_ui_slots:' in asm
    # The initial properties come entirely from JSON; native event bindings remain.
    assert 'call DBaseQtWidgetSetGeometry' not in asm
    assert 'call DBaseQtObjectBindEvent' in asm
    if target == 'pe32':
        assert f'    push {int(compress)}\n' in asm
    else:
        assert f'    mov dword ptr [rsp+32], {int(compress)}\n' in asm
    lk = linkers()
    prog = lk['assemble_pe32_object_source'](asm) if target=='pe32' else lk['assemble_pe64_object_source'](asm)
    obj = lk['write_coff32_object'](prog) if target=='pe32' else lk['write_coff64_object'](prog)
    image = (lk['link_coff32_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable
             if target=='pe32' else lk['link_coff64_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable)
    assert image[:2] == b'MZ'
    assert b'DBaseQtFormApplyExternalUi' in image
