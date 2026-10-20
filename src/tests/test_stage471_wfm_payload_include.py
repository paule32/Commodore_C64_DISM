"""Stage 471: compact Windows WFM import + external UI payload includes."""
from pathlib import Path
from dataclasses import replace
import re
import struct
import textwrap

import pytest

from windows_asm_macros import (
    externalize_windows_imports,
    externalize_windows_wfm_payload,
    preprocess_windows_asm,
)
from test_stage446_real_pe_link import linkers
from test_stage456_wfm_external_ui_json import model_with_controls


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
@pytest.mark.parametrize('compressed', [False, True])
def test_form_ui_payload_and_import_sidecars_assemble_and_link(tmp_path, monkeypatch, target, compressed):
    import d64dbase.wfm as wfm_module

    model = model_with_controls()
    monkeypatch.setattr(wfm_module, 'parse_dbase_wfm', lambda *args, **kw: model)
    compiler_file = Path(__file__).parent / 'd64_dism.py'
    source = compiler_file.read_text(encoding='utf-8')
    start = source.index('        def _compile_dbase_wfm_fallback(\n')
    end = source.index('        def compile_dbase_form(self) -> bool:', start)
    code = textwrap.dedent(source[start:end])
    env = {
        're': re, 'struct': struct, 'replace': replace,
        '_normalize_project_windows_debug_theme': lambda x: x,
        'AssemblerError': type('AssemblerError', (Exception,), {}),
        'DBASE_WFM_PROPERTY_DEFAULTS_ABI': 1,
        '__name__': 'stage471',
    }
    exec(compile(code, '<wfm471>', 'exec'), env)

    class Stub:
        _compile_dbase_wfm_fallback = env['_compile_dbase_wfm_fallback']
        project_windows_import_packer = {}
        project_windows_dbase_visual = {
            target: {'external_ui_components': True, 'compress_json': compressed}
        }

        @staticmethod
        def _dbase_wfm_int(props, name, default):
            return int(next((v for k, v in (props or {}).items() if k.casefold() == name.casefold()), default))

        @staticmethod
        def _dbase_wfm_prop(props, name, default=None):
            return next((v for k, v in (props or {}).items() if k.casefold() == name.casefold()), default)

        @staticmethod
        def _dbase_wfm_asm_bytes(value):
            return ', '.join(str(b) for b in (str(value).encode('utf-8') + b'\x00'))

    original = Stub()._compile_dbase_wfm_fallback(
        'CLASS Form1 OF FORM\nENDCLASS\n',
        filename=str(tmp_path / 'Form1.wfm'), target=target,
    ).assembly
    assert '__dbase_wfm_external_ui_payload:\n    db ' in original
    asm_path = tmp_path / f'Form1.generated.{target}.asm'
    compact, imports_path, imports_data = externalize_windows_imports(original, asm_path)
    compact, payload_path, payload_data = externalize_windows_wfm_payload(compact, asm_path)

    assert imports_path == tmp_path / f'Form1.generated.{target}.extern.inc'
    assert payload_path == tmp_path / f'Form1.generated.{target}.payload.inc'
    assert compact.startswith(f'%include "{imports_path.name}"\n')
    assert f'__dbase_wfm_external_ui_payload:\n    %include "{payload_path.name}"\n' in compact
    assert '%include "<' not in compact
    assert '    db ' in payload_data
    assert all(re.fullmatch(r'\s+db\s+\d+(?:\s*,\s*\d+)*', line) for line in payload_data.splitlines())
    assert len(compact) < len(original)
    assert '__dbase_wfm_external_ui_slots:' in compact
    assert '.section .bss' in compact

    imports_path.write_text(imports_data, encoding='utf-8')
    payload_path.write_text(payload_data, encoding='utf-8')
    asm_path.write_text(compact, encoding='utf-8')
    expanded = preprocess_windows_asm(compact, filename=str(asm_path)).source
    assert '__dbase_wfm_external_ui_payload:\n' in expanded
    assert 'import DBaseQtFormApplyExternalUi' in expanded
    assert 'db ' in expanded

    ns = linkers()
    inline_obj = ns[f'assemble_{target}_object_source'](original)
    obj = ns[f'assemble_{target}_object_source'](compact, filename=str(asm_path))
    assert obj.code == inline_obj.code  # no change to code layout/calls
    assert obj.data == inline_obj.data  # payload bytes byte-for-byte unchanged
    bits = 64 if target == 'pe64' else 32
    coff = ns[f'write_coff{bits}_object'](obj)
    exe = ns[f'link_coff{bits}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True
    )
    assert exe.executable[:2] == b'MZ'


def test_no_external_ui_does_not_write_payload(tmp_path):
    asm = 'section .text\nret\n.section .data\ns: db 1,2\n'
    compact, inc, text = externalize_windows_wfm_payload(asm, tmp_path / 'Form1.generated.pe32.asm')
    assert (compact, inc, text) == (asm, None, None)


def test_extraction_stops_before_next_label_and_keeps_data_unmodified(tmp_path):
    assembly = ('.section .data\n'
                '__dbase_wfm_external_ui_payload:\n'
                '    db 0, 1, 2\n'
                '    db 3, 4, 255\n'
                'other_label:\n'
                '    dd 0\n'
                '.section .bss\n')
    result, inc, data = externalize_windows_wfm_payload(
        assembly, tmp_path / 'Form1.generated.pe32.asm'
    )
    assert inc.name == 'Form1.generated.pe32.payload.inc'
    assert data == '    db 0, 1, 2\n    db 3, 4, 255\n'
    assert 'other_label:\n    dd 0\n.section .bss\n' in result
    assert result.count('%include') == 1


def test_compiler_writes_both_sidecars_next_to_asm():
    src = (Path(__file__).parent / 'd64_dism.py').read_text('utf-8')
    assert 'externalize_windows_wfm_payload(\n                    generated.assembly, assembly_path' in src
    assert '_asm_payload_include = (_payload_path, _payload_text)' in src
    assert 'if _asm_payload_include is not None:' in src
    assert 'self._write_assembled_program(_inc_path, _inc_text.encode("utf-8"))' in src
