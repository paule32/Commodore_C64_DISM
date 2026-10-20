# -*- coding: utf-8 -*-
"""Stage 451: WFM data/code reductions and safe runtime packaging fallback."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import struct
import textwrap
from dataclasses import replace

import pytest

from d64dbase.wfm_optimizer import optimize_wfm_branches
from test_stage446_real_pe_link import linkers

ROOT=Path(__file__).parent
SOURCE=(ROOT/'d64_dism.py').read_text('utf8')

FORM='''Form1 = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        STORE 0 TO A
        STORE 0 TO C
        IF A > 0 .AND. C < 10
            ? "Beide Bedingungen erfüllt"
        ELSE
            ? "Bedingung nicht erfüllt"
        ENDIF
        IF .NOT. (A = 0 .OR. C >= 10)
            ? "NOT OR"
        ENDIF
        IF (A > 0) .XOR. (C < 0)
            ? "XOR"
        ENDIF
        RETURN
ENDCLASS
'''


def compile_wfm(source=FORM, target='pe32', const_pool=False):
    start=SOURCE.index('        def _compile_dbase_wfm_fallback(\n')
    stop=SOURCE.index('        def compile_dbase_form(self) -> bool:',start)
    definition=textwrap.dedent(SOURCE[start:stop])
    ctx={'re':re,'struct':struct,'replace':replace,
         '_normalize_project_windows_debug_theme':lambda value:value,
         'AssemblerError':type('AssemblerError',(Exception,),{}),
         'DBASE_WFM_PROPERTY_DEFAULTS_ABI':1,
         '__name__':'stage451_wfm_test'}
    exec(compile(definition,'<wfm>','exec'),ctx)
    class Stub:
        _compile_dbase_wfm_fallback=ctx['_compile_dbase_wfm_fallback']
        project_windows_import_packer={}
        project_windows_console_const_pool={'pe32':const_pool,'pe64':const_pool}
        @staticmethod
        def _dbase_wfm_int(props,name,default):
            return int(next((v for k,v in (props or {}).items() if k.casefold()==name.casefold()),default))
        @staticmethod
        def _dbase_wfm_prop(props,name,default=None):
            return next((v for k,v in (props or {}).items() if k.casefold()==name.casefold()),default)
        @staticmethod
        def _dbase_wfm_asm_bytes(value):
            return ', '.join(str(b) for b in str(value).encode('utf8'))
    return Stub()._compile_dbase_wfm_fallback(source,filename='test451.wfm',target=target,
                                               workstation_mode=False,debug_theme='default')


def test_ini_per_architecture_and_gui_setting_wired():
    for key in ('__windows_pe32_console_const_pool__', '__windows_pe64_console_const_pool__'):
        assert key in SOURCE
    assert 'self.console_runtime_const_pool_checkbox = QCheckBox("const pool", runtime_group)' in SOURCE
    assert 'DBaseRuntimeConstPool' in SOURCE
    assert 'self.console_runtime_const_pool_checkbox.toggled.connect(' in SOURCE
    assert 'self.set_project_windows_console_const_pool(' in SOURCE
    assert 'entries[_settings["console_const_pool_key"]]' in SOURCE
    assert 'panel.set_console_runtime_const_pool(' in SOURCE


def test_local_optimizer_preserves_target_and_inverts_conditional():
    fragment='''    jae __dbase_wfm_flow_false_1
    jmp __dbase_wfm_flow_true_2
__dbase_wfm_flow_false_1:
    jmp __dbase_wfm_flow_end_3
__dbase_wfm_flow_end_3:
'''
    optimized=optimize_wfm_branches(fragment)
    assert '    jb __dbase_wfm_flow_true_2\n' in optimized
    assert '    jae __dbase_wfm_flow_false_1' not in optimized
    assert '    jmp __dbase_wfm_flow_end_3' not in optimized
    assert '__dbase_wfm_flow_false_1:' in optimized


def test_optimizer_does_not_modify_other_asm_or_intervening_instructions():
    source='''    je externally_visible
    jmp anywhere
externally_visible:
    je __dbase_wfm_flow_one_1
    mov eax, 1
    jmp __dbase_wfm_flow_two_2
__dbase_wfm_flow_one_1:
'''
    assert optimize_wfm_branches(source)==source


@pytest.mark.parametrize('target',['pe32','pe64'])
def test_const_pool_reduces_repeated_zero_constants_and_links(target):
    full=compile_wfm(target=target,const_pool=False).assembly
    pooled=compile_wfm(target=target,const_pool=True).assembly
    data=lambda s: re.findall(r'^__dbase_wfm_numconst_\d+:$',s,re.M)
    assert len(data(pooled)) < len(data(full))
    assert '    fldz' in pooled
    assert '    fldz' not in full.split('; Stage 133: WFM Event-/Methoden-Code')[-1]
    assert pooled.count('dd 0, 0') < full.count('dd 0, 0')
    assert '    je __dbase_wfm_flow_' in pooled or '    jne __dbase_wfm_flow_' in pooled
    links=linkers()
    program=(links['assemble_pe32_object_source'](pooled) if target=='pe32'
             else links['assemble_pe64_object_source'](pooled))
    obj=(links['write_coff32_object'](program) if target=='pe32'
         else links['write_coff64_object'](program))
    image=(links['link_coff32_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable
           if target=='pe32' else links['link_coff64_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable)
    assert image.startswith(b'MZ')
    assert b'c64_dbase_runtime.dll' in image


@pytest.mark.parametrize("target", ["pe32", "pe64"])
def test_property_table_identical_data_interned(monkeypatch, target):
    import d64dbase.wfm as wfm_module
    from d64dbase.wfm import DBaseWfmControl, parse_dbase_wfm
    model=parse_dbase_wfm(FORM)
    for index in (1,2):
        model.controls.append(DBaseWfmControl(
            path=f'THIS.Button{index}',class_name='BUTTON',parent_path='THIS',
            properties={'Text':'Same','ToolTip':'Same hint','Enabled':False,'Width':130,'Height':26},order=index))
    monkeypatch.setattr(wfm_module,'parse_dbase_wfm',lambda *_a,**_kw:model)
    asm=compile_wfm(target=target).assembly
    tables=re.findall(r'^__dbase_wfm_property_table_\d+:$',asm,re.M)
    if target == "pe64":
        references=re.findall(r'\bmov rdx, (__dbase_wfm_property_table_\d+)\b',asm)
    else:
        references=re.findall(r'\bpush (__dbase_wfm_property_table_\d+)\b',asm)
    assert tables, 'expected packed property table'
    # Two identical controls must reference the SAME immutable table.
    assert len(references)>len(tables)
    assert len(set(references))==len(tables)
    links=linkers()
    machine=(links['assemble_pe32_object_source'](asm) if target=='pe32'
             else links['assemble_pe64_object_source'](asm))
    obj=(links['write_coff32_object'](machine) if target=='pe32'
         else links['write_coff64_object'](machine))
    image=(links['link_coff32_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable
           if target=='pe32' else links['link_coff64_objects']((obj,),entry_symbol='__d64_wfm_entry',gui=True).executable)
    assert image.startswith(b'MZ')


def test_windows_access_denied_fallback_is_not_silent(monkeypatch,tmp_path):
    from d64dbase import pe_dll_pack as pack
    file=tmp_path/'example.dll';file.write_bytes(b'MZ'+b'0'*120)
    def deny(*_a):raise PermissionError(13,'Access denied')
    called=[]
    monkeypatch.setattr(pack,'_set_ntfs_compression_native',deny)
    monkeypatch.setattr(pack,'_compact_windows_fallback',lambda f,enabled:called.append((f,enabled)))
    monkeypatch.setattr(pack.os,'name','nt')
    pack.set_ntfs_compression(file)
    assert called==[(file,True)]
