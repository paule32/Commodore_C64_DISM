# -*- coding: utf-8 -*-
"""Stage 678: one Qt5 DLL for JIT, Pascal and dBASE native exports."""
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import pytest
from d64dbase import compile_dbase_to_assembly
from d64dbase.native_runtime_deploy import (
    DLL_NAME, REQUIRED_EXPORTS, DBASE_EXPORTS, deploy_runtime,
)
from pascal_console_dependencies import obsolete_console_dependencies

ROOT=Path(__file__).resolve().parent

def test_qt_native_imports_and_abi_exports():
    assert DLL_NAME == 'libd64_qt5.dll'
    define=(ROOT/'d64qt5/d64qt5_bridge.def').read_text()
    table=dict((m.group(1),int(m.group(2))) for m in re.finditer(r'^\s*([A-Za-z_]\w*)\s+@(\d+)',define,re.M))
    assert len(set(table.values())) == len(table)
    assert all(name in table for name in REQUIRED_EXPORTS)
    assert table['jit_object_instance_new'] >= 2000
    assert table['_jit_malloc'] >= 2000
    assert table['DBaseQtRuntimeWrite'] == 1019
    assert table['DBaseQtRuntimeWriteText'] == 1021
    core=sorted((ordinal,name) for name,ordinal in table.items() if 1<=ordinal<=64)
    digest=hashlib.sha256(''.join(f'{ordinal}:{name}\n' for ordinal,name in core).encode()).hexdigest()
    assert digest=='02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7'


def test_static_archive_build_no_old_dll_or_qt_entry_conflict():
    builder=(ROOT/'runtime/build.qt5_embedded.win32.sh').read_text()
    pro=(ROOT/'d64qt5/d64qt5_bridge.pro').read_text()
    assert 'libd64_qt5_native.a' in pro and 'libd64_qt5_native.a' in builder
    assert '-Wl,--whole-archive' in pro
    assert 'qt5_native_runtime.commands' in pro
    assert 'dllmain' not in re.search(r'modules=\(([^)]*)\)',builder).group(1)
    assert 'loader' not in re.search(r'modules=\(([^)]*)\)',builder).group(1)
    assert '-dD64_QT5_EMBEDDED=1' in builder
    assert '-DD64_QT5_EMBEDDED' in builder
    assert 'D64_QT5_EMBEDDED' in (ROOT/'runtime/windows.cc').read_text()
    assert 'D64_QT5_EMBEDDED' in (ROOT/'runtime/memory_nt32.asm').read_text()
    if shutil.which('bash'):
        subprocess.run(['bash','-n',str(ROOT/'runtime/build.qt5_embedded.win32.sh')],check=True)


def test_qt_no_longer_loads_old_runtime_and_pascal_string_alloc_is_direct():
    qt=(ROOT/'d64qt5/d64qt5_bridge.cpp').read_text()
    console=(ROOT/'d64qt5/d64_pascal_console.cpp').read_text()
    assert 'GetModuleHandleA("libd64_runtime.dll")' not in qt
    assert 'LoadLibraryA("libd64_runtime.dll")' not in qt
    assert 'GetProcAddress(module, "DBaseConsoleWrite")' not in qt
    assert 'DBaseConsoleWrite(text, length);' in qt
    assert '_jit_malloc(1024)' in console
    assert 'GetProcAddress(runtime, "_jit_malloc")' not in console


@pytest.mark.parametrize('target',('pe32','pe64'))
@pytest.mark.parametrize('level',('O0','O1','O2'))
def test_real_coff_pe_imports_only_qt5(target,level,tmp_path):
    from dbase_size_optimizer import optimize_dbase_size_assembly
    from test_stage605_link import _load_pe_linker
    from pascal_console_dependencies import inspect_pe
    n=_load_pe_linker()
    source='? "Hallo"\n? "Welt"\n'
    asm=compile_dbase_to_assembly(source,target=target).assembly
    if level!='O0':
        asm=optimize_dbase_size_assembly(asm,level=level).assembly
    assert '"libd64_runtime.dll"' not in asm
    assert '"c64_dbase_runtime.dll"' not in asm
    assert '"libd64_qt5.dll"' in asm
    assemble=n['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source']
    writer=n['write_coff32_object' if target=='pe32' else 'write_coff64_object']
    link=n['link_coff32_objects' if target=='pe32' else 'link_coff64_objects']
    obj=assemble(asm)
    pe=link((writer(obj),),entry_symbol='_start',gui=True)
    output=tmp_path/'app.exe';output.write_bytes(pe.executable)
    machine,imports,_=inspect_pe(output)
    assert machine==(0x14c if target=='pe32' else 0x8664)
    assert 'libd64_runtime.dll' not in imports
    assert 'c64_dbase_runtime.dll' not in imports
    assert 'libd64_qt5.dll' in imports
    assert 'DBaseConsoleWrite' in imports['libd64_qt5.dll']
    assert 'DBaseConsoleShutdown' in imports['libd64_qt5.dll']


def test_existing_pascal_and_dbase_runtime_prototypes_use_qt5():
    for rel in ('d64dbase/object_abi.py','d64dbase/compiler.py',
                'c64pascal/compiler.py','d64_dism.py',
                'c64pascal/units/System/Objects.pui',
                'runtime/dbase/src/System.Objects.prg'):
        source=(ROOT/rel).read_text()
        # old library name may only appear in diagnostics / legacy compatibility
        assert '"libd64_runtime.dll"' not in source
    assert 'libd64_qt5.dll' in (ROOT/'c64pascal/compiler.py').read_text()
    assert 'libd64_qt5.dll' in (ROOT/'runtime/dbase/src/System.Objects.prg').read_text()


def test_reject_old_pascal_objects():
    manifest={'imports':[{'dll':'libd64_runtime.dll','member':'_jit_malloc'}]}
    assert obsolete_console_dependencies(ROOT/'nonexistent.exe',manifest) == {'libd64_runtime.dll'}


def test_deployment_rejects_incomplete_qt_and_accepts_full_exports(tmp_path):
    src=tmp_path/'pkg';(src/'d64qt5/release').mkdir(parents=True)
    dll=src/'d64qt5/release/libd64_qt5.dll';dll.write_bytes(b'new DLL')
    output=tmp_path/'out'/'App.exe'
    def get_exports(path,machine):
        if machine!=0x14c: raise ValueError('machine')
        if Path(path).read_bytes()==b'old DLL': return {'DBaseQtShowWindow'}
        return dict.fromkeys(REQUIRED_EXPORTS)
    output.parent.mkdir()
    (output.parent/'libd64_qt5.dll').write_bytes(b'old DLL')
    got=deploy_runtime(output,'pe32',get_exports=get_exports,package_root=src)
    assert got.read_bytes()==b'new DLL'
    dll.unlink()
    assert deploy_runtime(output,'pe32',get_exports=get_exports,package_root=src)==got
    got.unlink()
    with pytest.raises(FileNotFoundError,match='libd64_qt5.dll'):
        deploy_runtime(output,'pe32',get_exports=get_exports,package_root=src)


@pytest.mark.skipif(not shutil.which('clang++'),reason='clang++ unavailable')
def test_actual_native_runtime_cpp_compiles_for_win32(tmp_path):
    for name in ('jitObject','dbase_runtime_merged','args','error','exception',
                 'print','locale','windows','qt5_embedded_misc'):
        result=subprocess.run([
          'clang++','-target','i686-w64-windows-gnu',
          '-std=c++20','-fsyntax-only','-fno-exceptions','-fno-rtti',
          '-nostdinc','-DDLL_BUILD','-DD64_QT5_EMBEDDED',
          '-I'+str(ROOT/'runtime'),str(ROOT/'runtime'/f'{name}.cc')],
          text=True,capture_output=True)
        assert result.returncode==0,(name,result.stderr)
