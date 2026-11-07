"""Stage 527 focused tests; compatible with Python before 3.15 by parsing legacy-lazy source in memory."""
from pathlib import Path
import re, ast, struct, configparser, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from debug_options import DebugOptions, update_project_file, read_options

BASE = Path(__file__).parent
SOURCE = (BASE/'d64_dism.py').read_text('utf-8')
SOURCE_LEGACY = re.sub(r'(?m)^(\s*)lazy (from|import) ',r'\1\2 ',SOURCE)
NODES = ast.parse(SOURCE_LEGACY).body

def func(name):
    node = next(x for x in NODES if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
    return compile(ast.Module(body=[node],type_ignores=[]), '<d64_dism>', 'exec')

def test_syntax():
    compile(SOURCE_LEGACY, '<d64_dism>', 'exec')

def test_config(tmp_path):
    f=tmp_path/'x.pro'
    f.write_text('[Project]\nFormat = dBase2Many Project\n\n[Other]\nValue = abc\n')
    expected=DebugOptions(True,True,True,2)
    update_project_file(f,expected)
    assert read_options(f)==expected
    assert '[Other]\nValue = abc' in f.read_text()

def test_pe32_ces_codegen():
    ns={'struct':struct,'Dict':dict,'Tuple':tuple,'List':list,'Optional':__import__('typing').Optional,
        'PE32AssemblerError':type('PE32AssemblerError',(Exception,),{}),
        'PE_D64I_MAGIC':b'D64I','PE_D64I_VERSION':3,
        'PE32_D64Z_HEADER_SIZE':20,
        'PE_D64I_HEADER':struct.Struct('<4sHHIIHHHHII'),
        'PE_D64I_DLL_RECORD':struct.Struct('<15I'),
        'PE_D64I_IMPORT_RECORD':struct.Struct('<3I'),
        'PE_D64_RUNTIME_ABI_INFO_SIZE':100,
        'PE_D64I_DLL_CHECK_EXACT':0x20,'PE_D64I_DLL_CHECK_RUNTIME':1,
        'PE_D64I_DLL_CHECK_HASH':2,'PE_D64I_DLL_FALLBACK_NAME':4,
        'PE_D64I_ORDINAL_FLAG':0x80000000,
        'PE_D64_LOADER_VERSION_PACKED':1,
        '_pe_import_packer_settings':lambda target:{},
        '_d64l_info_block':lambda x:b'D64L',
        '_pe_d64i_bootstrap_imports':lambda x:{k:('',k) for k in ('__d64_loader_CreateDecompressor','__d64_loader_VirtualProtect','__d64_loader_Decompress','__d64_loader_CloseDecompressor','__d64_loader_LoadLibraryA','__d64_loader_GetProcAddress','__d64_loader_FlushInstructionCache','__d64_loader_ExitProcess')},
        'PE32_MSZIP_LOADER_IMPORTS':{},
        'stage527_debug_options':lambda:DebugOptions(ces=True),
    }
    exec(func('_PE32LoaderBuilder'),ns)
    exec(func('_build_pe32_mszip_loader'),ns)
    names=list(ns['_pe_d64i_bootstrap_imports'](False))
    args=dict(image_base=0x400000,text_rva=0x1000,text_size=0x900,ztext_rva=0x5000,packed_size=200,
        original_entry_rva=0x1000,iat_rvas={k:0x8000+4*i for i,k in enumerate(names)},d64i_rva=0x1800,loader_rva=0x3000)
    data=ns['_build_pe32_mszip_loader'](**args)
    assert b'CES: LoadLibraryA failed' in data and b'CES: GetProcAddress failed' in data
    assert b'MessageBoxA\0' in data
    ns['stage527_debug_options']=lambda:DebugOptions()
    plain=ns['_build_pe32_mszip_loader'](**args)
    assert b'CES: LoadLibraryA failed' not in plain
    assert len(data)>len(plain)

if __name__=='__main__':
    import tempfile
    test_syntax()
    with tempfile.TemporaryDirectory() as folder: test_config(Path(folder))
    test_pe32_ces_codegen()
    print('Stage 527 tests passed: 3')
