# -*- coding: utf-8 -*-
"""Stage 459: avoid false WFM DLL mismatch from name-only UTF-8/JSON exports."""
from __future__ import annotations
import hashlib
import re
import struct
import textwrap
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SOURCE = (HERE/'d64_dism.py').read_text(encoding='utf-8')
DEF = (HERE/'d64qt5'/'d64qt5_bridge.def').read_text(encoding='utf-8')
EXPECTED = bytes.fromhex('02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7')
OPTIONAL = {
    'DBaseQtFormApplyExternalUi', 'DBaseUtf8Substring',
    'DBaseUtf8SubstringUpper', 'DBaseUtf8SubstringLower',
    'DBaseUtf8Upper', 'DBaseUtf8Lower',
    'DBaseQtRuntimeStartup', 'DBaseQtRuntimeShutdown',
    'DBaseQtWfmModalParameter', 'DBaseQtFormRun',
}


def _load():
    start = SOURCE.index('D64_QT5_OPTIONAL_NAME_EXPORTS = frozenset(')
    end = SOURCE.index('PE_D64_QT5_ORDINAL_MAP_HASH = bytes.fromhex(', start)
    header = SOURCE[start:end]
    start2 = SOURCE.index('def _pe_export_ordinal_map_hash(')
    end2 = SOURCE.index('def _pe_file_sha256(', start2)
    export = SOURCE[start2:end2]
    start3 = SOURCE.index('def _d64_qt5_source_ordinal_map_hash(')
    end3 = SOURCE.index('PE_D64I_BOOTSTRAP_IMPORTS:', start3)
    source = SOURCE[start3:end3]
    env = {'hashlib':hashlib, 're':re, 'Path':Path, '__file__':str(HERE/'d64_dism.py'),
           'PE_D64_QT5_ORDINAL_MAP_HASH':EXPECTED}
    exec(compile('from __future__ import annotations\n'+header+'\n'+export+'\n'+source,
                 '<stage459>', 'exec'),env)
    return env


def _exports():
    exports={}
    for raw in DEF.splitlines():
        match=re.match(r'^\s*([^\s]+)\s+@(\d+)',raw)
        if match:
            exports[match.group(1)]=int(match.group(2))
    return exports


def test_original_64_export_abi_remains_unchanged():
    env=_load()
    exports=_exports()
    assert len(exports)==78
    assert env['_pe_export_ordinal_map_hash'](exports)==EXPECTED
    assert env['_d64_qt5_source_ordinal_map_hash']()==EXPECTED
    assert env['D64_QT5_OPTIONAL_NAME_EXPORTS']==OPTIONAL
    old={name:ordinal for name,ordinal in exports.items()
         if not name.startswith('DBaseQtProlog') and name not in OPTIONAL}
    assert len(old)==64
    assert env['_pe_export_ordinal_map_hash'](old)==EXPECTED
    assert env['_pe_export_ordinal_map_hash']({**old,'DBaseUtf8Upper':1009})==EXPECTED
    different={**old,'DBaseQtFormOpen':1099}
    assert env['_pe_export_ordinal_map_hash'](different)!=EXPECTED


def test_gui_wfm_optional_exports_derived_only_from_actual_imports():
    env=_load()
    assembly='''\nimport DBaseUtf8SubstringLower, "libd64_qt5.dll", "DBaseUtf8SubstringLower"\nimport __ui_read, "libd64_qt5.dll", "DBaseQtFormApplyExternalUi"\nimport foo, "other.dll", "DBaseUtf8Upper"\n; DBaseUtf8SubstringUpper is only in comments\n'''
    assert env['_d64_qt5_required_name_exports'](assembly)=={
        'DBaseUtf8SubstringLower', 'DBaseQtFormApplyExternalUi'}
    assert env['_d64_qt5_required_name_exports']('import foo, "libd64_qt5.dll", "DBaseQtFormOpen"')==set()


def test_cplusplus_runtime_hash_generator_consistent():
    from importlib.util import spec_from_file_location, module_from_spec
    gen=HERE/'d64qt5'/'generate_runtime_abi.py'
    spec=spec_from_file_location('_d64_runtime_abi_459',gen)
    module=module_from_spec(spec)
    spec.loader.exec_module(module)
    rows=module.read_exports()
    core=[(o,n) for o,n in rows if not n.startswith('DBaseQtProlog') and n not in OPTIONAL]
    assert len(core)==64
    assert hashlib.sha256(''.join(f'{o}:{n}\n' for o,n in core).encode('ascii')).digest()==EXPECTED
    assert EXPECTED.hex() == '02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7'


def _wfm_stub(tmp_path, all_exports, needed):
    start=SOURCE.index('        def _prepare_dbase_form_runtime(self, output_path: Path) -> bool:')
    end=SOURCE.index('        def start_dbase_form(self) -> bool:',start)
    method=textwrap.dedent(SOURCE[start:end])
    env=_load()
    env.update({'IMAGE_FILE_MACHINE_I386':0x14c,
                'IMAGE_FILE_MACHINE_AMD64':0x8664,
                'PE_D64_QT5_ORDINAL_MAP_HASH':EXPECTED,
                '_pe_file_machine':lambda p:0x14c,
                '_pe_export_name_ordinals':lambda path,machine:dict(all_exports),
                'shutil':shutil})
    exec(compile('from __future__ import annotations\n'+method,'<wfm-runtime459>','exec'),env)
    output=tmp_path/'program.exe'
    output.write_bytes(b'MZ')
    dest=tmp_path/'libd64_qt5.dll'
    dest.write_bytes(b'PE')
    class Editor:
        def toPlainText(self):
            return '\n'.join(f'import {n}, "libd64_qt5.dll", "{n}"' for n in needed)
    class Document:
        generated_assembly_editor=Editor()
    class Stub:
        dbase_form_build_document=Document()
        current_directory=tmp_path
        errors=[]
        logs=[]
        _prepare_dbase_form_runtime=env['_prepare_dbase_form_runtime']
        def show_error(self,title,msg):self.errors.append((title,msg))
        def log(self,msg):self.logs.append(msg)
    return Stub(),output


def test_new_dll_is_accepted_with_name_only_exports(tmp_path):
    all_exports=_exports()
    stub,output=_wfm_stub(tmp_path,all_exports,{'DBaseUtf8SubstringLower', 'DBaseQtFormApplyExternalUi'})
    assert stub._prepare_dbase_form_runtime(output) is True
    assert not stub.errors


def test_old_dll_is_rejected_only_when_new_function_needed(tmp_path):
    old={n:o for n,o in _exports().items() if not n.startswith('DBaseQtProlog') and n not in OPTIONAL}
    old_stub,output=_wfm_stub(tmp_path,old,{'DBaseUtf8SubstringLower'})
    assert old_stub._prepare_dbase_form_runtime(output) is False
    assert any('Fehlende Runtime-Exporte: DBaseUtf8SubstringLower' in text
               for _,text in old_stub.errors)
    plain_stub,output=_wfm_stub(tmp_path,old,set())
    assert plain_stub._prepare_dbase_form_runtime(output) is True
