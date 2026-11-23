# -*- coding: utf-8 -*-
"""Stage 670: deduplicated native dBASE VMT ABI, legacy compatibility."""
from __future__ import annotations

import ctypes
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from d64dbase.object_abi import (JIT_VMT_SHARED_METHOD_FLAG, NativeClassMethod,
                                 emit_classes, METHOD_BY_NAME)
from d64dbase import compile_dbase_to_assembly

ROOT = Path(__file__).resolve().parent


def _class(name, parent='TObject', methods=()):
    return SimpleNamespace(name=name, parent=parent,
                           methods=tuple(methods), properties=())


@pytest.mark.parametrize('target,ptr,instance_size', [('pe32','dd',4),('pe64','dq',8)])
def test_shared_class_table_and_compact_layout(target, ptr, instance_size):
    classes = [_class(f'TException{i}') for i in range(100)]
    imports, code, data = emit_classes(classes, target=target)
    asm = '\n'.join(data)
    assert asm.count('__dbase_class_object:') == 1
    assert asm.count(f'{ptr} __dbase_class_object') == 101  # TObject plus 100 children
    assert asm.count(f'{ptr} __dbase_cls_tobject_free\n') == 1
    assert asm.count(f'{ptr} __dbase_cls_tobject_inheritsfrom\n') == 1
    for item in classes:
        vmt = asm.split('__dbase_vmt_' + item.name.casefold() + ':', 1)[1]
        lines = vmt.split('__dbase_vmt_' + item.name.casefold() + '_name:', 1)[0].strip().splitlines()
        assert len(lines) == 6
        assert lines[-1].strip() == f'{ptr} __dbase_class_object'
        assert lines[2].strip() == f'{ptr} 0x{(instance_size|JIT_VMT_SHARED_METHOD_FLAG):08X}'
    # For 100 classes + TObject, old 14 pointer words/class;
    # now six pointer words/class, plus one nine-word shared table.
    assert (14*101 - (6*101 + 9))*instance_size > 0


@pytest.mark.parametrize('target,ptr', [('pe32','dd'),('pe64','dq')])
def test_override_inheritance_creates_only_one_extra_table(target,ptr):
    overridden = NativeClassMethod('procedure','Free',(),'',3,((4,'return'),))
    classes = [_class('TAlpha'), _class('TBeta','TAlpha',(overridden,)),
               _class('TGamma','TBeta'), _class('TDelta')]
    _imports, code, data = emit_classes(classes,target=target)
    asm='\n'.join(data)
    assert asm.count('__dbase_class_methods_1:') == 1
    assert asm.count('__dbase_class_methods_2:') == 0
    for klass,table in [('TAlpha','__dbase_class_object'),
                        ('TBeta','__dbase_class_methods_1'),
                        ('TGamma','__dbase_class_methods_1'),
                        ('TDelta','__dbase_class_object')]:
        text=asm.split(f'__dbase_vmt_{klass.lower()}:',1)[1]
        line=text.split(f'__dbase_vmt_{klass.lower()}_name:',1)[0].splitlines()[-1]
        assert line.strip() == f'{ptr} {table}'
    own=asm.split('__dbase_class_methods_1:',1)[1].split('__dbase_vmt_',1)[0]
    assert f'{ptr} __dbase_cls_tbeta_free' in own
    assert f'    {ptr} __dbase_cls_tobject_free\n' not in own
    assert '__dbase_cls_tbeta_free:' in '\n'.join(code)


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_generated_code_keeps_legacy_virtual_lookup_api(target):
    asm=compile_dbase_to_assembly('CLASS TChild OF TObject ENDCLASS\n'
                                   'obj = new TChild()\nobj.Free()\n',
                                   target=target).assembly
    assert 'call __dbase_obj_jit_get_virtual_object' in asm
    assert '__dbase_class_object:' in asm
    assert '__dbase_vmt_tchild:' in asm
    assert '__dbase_class_object' in asm


@pytest.mark.skipif(not shutil.which('g++'),reason='Native GNU C++ compiler not installed')
def test_real_native_runtime_legacy_and_compact_dispatch(tmp_path):
    """Build the real runtime/jitObject.cc with tiny allocation stubs on Linux.

    It tests the actual JitVmt C++ implementation, not a Python reimplementation
    of the virtual lookup.  Windows builds use MinGW and have their own toolchain.
    """
    if not __import__('sys').platform.startswith('linux'):
        pytest.skip('Linux-native C++ smoke test')
    source = ROOT / 'runtime' / 'jitObject.cc'
    stub = tmp_path / 'stubs.cpp'
    stub.write_text('#include <cstdlib>\n'
                    'extern "C" void* _jit_calloc(unsigned n, unsigned s) { return std::calloc(n,s); }\n'
                    'extern "C" void _jit_free(void* p) { std::free(p); }\n'
                    'extern "C" int _jit_printf(const char*,...) { return 0; }\n')
    a = tmp_path / 'jit.o'
    b = tmp_path / 'stubs.o'
    so = tmp_path / 'libjit.so'
    subprocess.run(['g++','-std=c++20','-fPIC','-fpermissive','-DDLL_BUILD',
                    '-D__declspec(x)=','-I'+str(source.parent),'-c',str(source),'-o',str(a)],
                   check=True,capture_output=True,text=True)
    subprocess.run(['g++','-std=c++20','-fPIC','-c',str(stub),'-o',str(b)],
                   check=True,capture_output=True,text=True)
    subprocess.run(['g++','-shared',str(a),str(b),'-o',str(so)],
                   check=True,capture_output=True,text=True)
    lib=ctypes.CDLL(str(so))
    vp=ctypes.c_void_p
    class Header(ctypes.Structure):
        _fields_ = [('parent',vp),('class_name',vp),('instance_size',ctypes.c_uint32),
                    ('initialize',vp),('finalize',vp),('destroy',vp)]
    class Legacy(ctypes.Structure):
        _fields_ = [('header',Header),('methods',vp*8)]
    callback=ctypes.CFUNCTYPE(None,vp)
    fired=[]
    @callback
    def destructor(ptr):fired.append('destroy')
    @callback
    def method0(ptr):fired.append('method0')
    @callback
    def method7(ptr):fired.append('method7')
    def address(cb):return ctypes.cast(cb,vp).value
    methods=[address(method0)]*7+[address(method7)]
    old=Legacy()
    old.header.instance_size=ctypes.sizeof(vp)
    old.header.destroy=address(destructor)
    old.methods[:]=methods
    new=Header()
    new.instance_size=JIT_VMT_SHARED_METHOD_FLAG|ctypes.sizeof(vp)
    shared=(vp*9)(address(destructor),*methods)
    new.destroy=ctypes.addressof(shared)
    lib.jit_class_instance_size.argtypes=[vp]
    lib.jit_class_instance_size.restype=ctypes.c_uint32
    lib.jit_get_virtual_vmt.argtypes=[vp,ctypes.c_uint32]
    lib.jit_get_virtual_vmt.restype=vp
    lib.jit_get_virtual_object.argtypes=[vp,ctypes.c_uint32]
    lib.jit_get_virtual_object.restype=vp
    lib.jit_object_instance_new.argtypes=[vp]
    lib.jit_object_instance_new.restype=vp
    lib.jit_object_free.argtypes=[vp]
    lib.jit_object_error_last.restype=ctypes.c_int
    for label,klass in [('legacy',old),('shared',new)]:
        handle=ctypes.addressof(klass)
        assert lib.jit_class_instance_size(handle)==ctypes.sizeof(vp),label
        assert lib.jit_get_virtual_vmt(handle,0)==address(method0),label
        assert lib.jit_get_virtual_vmt(handle,7)==address(method7),label
        instance=lib.jit_object_instance_new(handle)
        assert instance,label
        assert lib.jit_get_virtual_object(instance,7)==address(method7),label
        callback_result=lib.jit_get_virtual_object(instance,0)
        ctypes.cast(callback_result,callback)(instance)
        lib.jit_object_free(instance)
        assert fired[-2:]==['method0','destroy'],label
    assert lib.jit_get_virtual_vmt(ctypes.addressof(new),8) is None
    assert lib.jit_object_error_last()==4
