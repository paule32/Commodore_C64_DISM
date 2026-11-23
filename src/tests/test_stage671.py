# -*- coding: utf-8 -*-
"""Stage 671: dBASE O0/O1 project settings and byte-size-reducing peepholes."""
from __future__ import annotations
import configparser
import re
from pathlib import Path

import pytest

from dbase_size_optimizer import (optimize_dbase_size_assembly,
                                   normalize_dbase_optimization_level)

ROOT=Path(__file__).resolve().parent
MAIN=(ROOT/'d64_dism.py').read_text(encoding='utf8')
USER_SAMPLE=Path('/mnt/data/App001.generated.pe32.asm')


def test_o0_strictly_preserves_assembler_and_unknown_level():
    asm='section .text\nstart:\n    jmp after\nafter:\n    ret\n'
    assert optimize_dbase_size_assembly(asm).assembly==asm
    assert optimize_dbase_size_assembly(asm,level='O0').replacements==0
    assert normalize_dbase_optimization_level('O1')=='O1'
    assert normalize_dbase_optimization_level('o1')=='O1'
    assert normalize_dbase_optimization_level('O2')=='O2'
    assert normalize_dbase_optimization_level(None)=='O0'


def test_o1_generated_control_flow_and_line_numbers():
    src=('bits 32\nsection .text\nstart:\n'
         '    test eax, eax\n    jne true_label\n    jmp false_label\n'
         'true_label:\n    mov eax, 1\n    jmp done\n'
         '    jmp false_label\nfalse_label:\n    mov eax, eax\n'
         'done:\n    ret\nsection .data\ndata_label:\n    dd 42\n')
    out=optimize_dbase_size_assembly(src,level='O1')
    assert out.replacements==2  # conditional branch, unreachable jmp
    assert 'je false_label' in out.assembly
    assert 'jne true_label' not in out.assembly
    assert out.assembly.count('; O1:')==2
    assert len(src.splitlines())==len(out.assembly.splitlines())
    assert out.assembly.split('section .data')[1]==src.split('section .data')[1]
    assert 'mov eax, eax' in out.assembly  # PE64 mov eax,eax zero-extends RAX
    assert optimize_dbase_size_assembly(out.assembly,level='O1').assembly==out.assembly


def test_jump_to_next_instruction_and_no_unsafe_peepholes():
    original=('section .text\nstart:\n    mov eax, 2\n'
              '    jmp around\naround:\n    test eax, eax\n'
              '    jmp somewhere\n    ; intervening comment\nsomewhere:\n    ret\n')
    result=optimize_dbase_size_assembly(original,level='O1')
    assert result.replacements==1
    assert 'jmp somewhere' in result.assembly
    assert 'mov eax, 2' in result.assembly


def test_module_only_optimizes_text_not_import_data_or_vmt():
    source=('import __dbase_obj, "runtime.dll", "fn"\n'
            'section .data\nmy_vmt:\n    dd my_vmt\n'
            'section .text\nmain:\n    jmp end\nend:\n    ret\n'
            'section .bss\nmemory:\n    resd 1\n')
    result=optimize_dbase_size_assembly(source,level='O1')
    assert result.replacements==1
    assert 'import __dbase_obj' in result.assembly
    assert 'dd my_vmt' in result.assembly
    assert 'resd 1' in result.assembly


def test_uploaded_asm_has_a_real_optimization():
    # The specific user-supplied file is an additional fixture, not a
    # prerequisite for downstream standalone Stage 671 regressions.
    sample = USER_SAMPLE if USER_SAMPLE.exists() else ROOT/'tests'/'fixtures'/'App001.generated.pe32.asm'
    if not sample.exists():
        pytest.skip('User fixture not in this checkout')
    assembly=sample.read_text(encoding='utf8')
    original=optimize_dbase_size_assembly(assembly,level='O0')
    modified=optimize_dbase_size_assembly(assembly,level='O1')
    assert original.assembly==assembly
    assert modified.replacements>=2
    assert 'jne __dbase_catch_next_39' in modified.assembly
    assert modified.assembly.count('; O1:')>=2
    assert len(modified.assembly.splitlines())>=len(assembly.splitlines())
    # Stage 672: original line numbers are preserved; the shared output helper
    # is appended after the old source, not inserted before existing lines.
    assert 'call DBaseQtRuntimeWrite' in modified.assembly
    assert '__dbase_vmt_exception:' in modified.assembly


def test_project_persistence_separate_abis_and_radio_first_group():
    assert '"Optimierungsstufen:"' in MAIN
    assert '"O0  -  keine Optimierung"' in MAIN
    assert '"O1  -  Länge Optimierung - JNE JE"' in MAIN
    assert '"O2  -  Static String Optimierung"' in MAIN
    ui=MAIN.index('self.dbase_size_group = QGroupBox(')
    visual=MAIN.index('self.dbase_visual_group = QGroupBox(',ui)
    assert ui < visual
    assert 'self.dbase_size_o0_radio.setChecked(True)' in MAIN
    for key in ('__windows_pe32_dbase_size_level__','__windows_pe64_dbase_size_level__'):
        assert key in MAIN
    assert '"OptimizationLevel":' in MAIN
    assert 'parser.get(_dbase_optimization_section, "OptimizationLevel", fallback="O0")' in MAIN
    assert '"value": self.project_windows_dbase_size_level.get(_target, "O0")' in MAIN
    assert 'self.set_project_windows_dbase_size_level(' in MAIN
    assert 'optimize_dbase_size_assembly(generated.assembly, level=_o_level)' in MAIN


def test_o1_real_coff_pe32_pe64_smaller():
    from test_stage605_link import _load_pe_linker
    native=_load_pe_linker()
    src=('section .text\n global _start\n_start:\n'
         '    test eax, eax\n    jne truthy\n    jmp false_branch\n'
         'truthy:\n    mov eax, 1\n    jmp finished\n'
         '    jmp false_branch\nfalse_branch:\n    xor eax, eax\n'
         'finished:\n    ret\n')
    compact=optimize_dbase_size_assembly(src,level='O1')
    assert compact.replacements==2
    for target in ('pe32','pe64'):
        assemble=native['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
        old=assemble(src)
        new=assemble(compact.assembly)
        # COFF text must strictly decrease without changing exported symbols.
        assert len(new.code) < len(old.code)
        assert set(old.symbols) == set(new.symbols)


def test_real_ini_write_read_optimization_level_without_qt():
    """Exercise the actual writer/parser fragments, not a copy of their rules."""
    from textwrap import dedent
    src=MAIN
    writer_start=src.index('        parser[_settings["dbase_optimization_section"]] = {')
    writer_end=src.index('        parser[_settings["prolog_optimization_section"]] = {',writer_start)
    writer_fragment=src[writer_start:writer_end]
    read_start=src.index('        _dbase_optimization_section = _settings["dbase_optimization_section"]')
    read_end=src.index('        _prolog_optimization_section = _settings["prolog_optimization_section"]',read_start)
    read_fragment=src[read_start:read_end]
    target_settings={
        target: {
            'title':title,
            'dbase_optimization_section':f'Settings.Windows.{title}.Compiler.dBASE.Optimierung',
            'dbase_size_level_key':f'__{target}_size_level__',
            **{key: f'__{target}_{key}__' for key in (
                'dbase_external_ui_key','dbase_compress_json_key',
                'dbase_store_binary_key','dbase_static_numeric_slots_key',
                'dbase_dynamic_typed_variables_key',
                'dbase_peephole_register_width_key',
                'dbase_peephole_processor_flags_key',
                'dbase_peephole_stack_state_key',
            )},
        } for target,title in [('pe32','32Bit'),('pe64','64Bit')]
    }
    state = {
        'PROJECT_WINDOWS_TARGET_SETTINGS':target_settings,
        '_project_bool_entry':lambda entries,key,default=False:
            (entries.get(key,[{'value':str(default)}])[0]['value'].lower()=='true'),
        '_parse_project_bool':lambda raw,default=False:raw.casefold()=='true',
        'normalize_dbase_optimization_level':normalize_dbase_optimization_level,
    }
    exec('def write_levels(parser, entries):\n    for _target, _settings in PROJECT_WINDOWS_TARGET_SETTINGS.items():\n'+writer_fragment,state)
    exec('def load_levels(parser, entries):\n    for _target, _settings in PROJECT_WINDOWS_TARGET_SETTINGS.items():\n'+read_fragment,state)
    parser=configparser.ConfigParser(interpolation=None)
    parser.optionxform=str
    entries={target_settings['pe32']['dbase_size_level_key']:[{'value':'O1'}],
             target_settings['pe64']['dbase_size_level_key']:[{'value':'O0'}]}
    state['write_levels'](parser,entries)
    assert parser['Settings.Windows.32Bit.Compiler.dBASE.Optimierung']['OptimizationLevel']=='O1'
    assert parser['Settings.Windows.64Bit.Compiler.dBASE.Optimierung']['OptimizationLevel']=='O0'
    loaded={}
    state['load_levels'](parser,loaded)
    assert loaded[target_settings['pe32']['dbase_size_level_key']]==[{'value':'O1'}]
    assert loaded[target_settings['pe64']['dbase_size_level_key']]==[{'value':'O0'}]
    parser['Settings.Windows.32Bit.Compiler.dBASE.Optimierung']['OptimizationLevel']='O9'
    state['load_levels'](parser,loaded)
    assert loaded[target_settings['pe32']['dbase_size_level_key']]==[{'value':'O0'}]
