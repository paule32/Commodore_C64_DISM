"""Stage 539 – deterministic second-stage loader regression without Windows GUI.

The fake compressor is only used to test layout/rebase/stub invariants on Linux.
Actual EXE output still uses the Windows cabinet.dll MSZIP compressor.
"""
from pathlib import Path
import ast
import re
import struct
import typing
import zlib

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'd64_dism.py').read_text('utf-8')
SRC_PARSEABLE = re.sub(r'(?m)^(\s*)lazy (from|import) ', r'\1\2 ', SOURCE)
NODES = ast.parse(SRC_PARSEABLE).body

def make_context():
    ns = dict(Dict=dict, Tuple=tuple, List=list, Optional=typing.Optional,
              struct=struct,
              PE32AssemblerError=type('PE32AssemblerError', (Exception,), {}),
              PE64AssemblerError=type('PE64AssemblerError', (Exception,), {}),
              PE32_IMAGE_BASE=0x400000, PE32_FILE_ALIGNMENT=0x200,
              PE_D64_LOADER_INFO=struct.Struct('<4sHHHHIHHII'),
              PE_D64_LOADER_MAGIC=b'D64L',
              PE64_IMAGE_BASE=0x140000000,
              PE_D64I_MAGIC=b'D64I', PE_D64I_VERSION=3,
              PE_D64I_HEADER=struct.Struct('<4sHHIIHHHHII'),
              PE_D64I_DLL_RECORD=struct.Struct('<IIIIHHII32s32s'),
              PE_D64I_IMPORT_RECORD=struct.Struct('<III'),
              PE_D64_RUNTIME_ABI_INFO_SIZE=80,
              PE_D64I_DLL_CHECK_EXACT=0x10,
              PE_D64I_DLL_CHECK_RUNTIME=0x2,
              PE_D64I_DLL_CHECK_HASH=0x4,
              PE_D64I_DLL_FALLBACK_NAME=0x8,
              PE_D64I_ORDINAL_FLAG=0x80000000,
              PE32_D64Z_HEADER_SIZE=28,
              PE32_COMPRESS_ALGORITHM_MSZIP=2,
              _pe_import_packer_settings=lambda target: {},
              _d64l_info_block=lambda x: b'D64L',
              _pe_d64i_bootstrap_imports=lambda x: {
                  '__d64_loader_' + name: ('kernel32.dll', name)
                  for name in ['CreateDecompressor','VirtualProtect',
                               'Decompress','CloseDecompressor','LoadLibraryA',
                               'GetProcAddress','FlushInstructionCache','ExitProcess']
              },
              PE32_MSZIP_LOADER_IMPORTS={}, PE64_MSZIP_LOADER_IMPORTS={},
              stage527_debug_options=lambda target='pe32':type('D', (), {'ces':True})(),
              _pe32_mszip_compress_buffer=lambda data: zlib.compress(data, 9),
              _align_up=lambda x, n: (x + n - 1) // n * n,
              )
    need = ('_PE32LoaderBuilder','_PE64LoaderBuilder',
            '_build_pe32_mszip_loader','_build_pe64_mszip_loader',
            '_pe32_build_second_stage_bootstrap','_pe64_build_second_stage_bootstrap',
            '_pe_try_compress_second_stage_loader')
    for name in need:
        node = next(x for x in NODES if isinstance(x, (ast.FunctionDef, ast.ClassDef)) and x.name==name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<stage539>', 'exec'), ns)
    ns['PE_LOADER_COMPRESSION_LAST_DECISION'] = {}
    return ns

def iats():
    return {'__d64_loader_' + name: 0xA000 + 4*i
            for i, name in enumerate(('CreateDecompressor','Decompress',
                                      'CloseDecompressor','VirtualProtect',
                                      'FlushInstructionCache','ExitProcess',
                                      'LoadLibraryA','GetProcAddress'))}

def test_bootstrap_architectures():
    n=make_context()
    imports=iats()
    x86=n['_pe32_build_second_stage_bootstrap'](image_base=0x400000,
        loader_rva=0x3000,packed_rva=0x3200,packed_size=420,
        target_rva=0x3800,expanded_size=1500,iat_rvas=imports)
    assert x86.startswith(b'\x55\x8B\xEC')
    assert x86.endswith(b'\xCC')
    assert b'\xFF\xE0' in x86
    assert len(x86)<512
    x64=n['_pe64_build_second_stage_bootstrap'](loader_rva=0x3000,
        packed_rva=0x3200,packed_size=420,
        target_rva=0x3800,expanded_size=1500,iat_rvas=imports)
    assert x64.startswith(b'\x55\x48\x89\xE5')
    assert x64.endswith(b'\xCC')
    assert len(x64)<512
    assert b'\x48\x89\xEC\x5D\xE9' in x64

def test_second_stage_rebased_32_64():
    n=make_context()
    imports=iats()
    # Simulate a large highly compressible D64I resolver (the behavior of
    # the real CES name/error path with many repeating operation fragments).
    for target in ('pe32','pe64'):
        args=dict(loader_rva=0x3000,ztext_rva=0x7000,iat_rvas=imports,
                  image_base=0x400000 if target=='pe32' else 0x140000000,
                  file_alignment=512)
        def generate(rva):
            if target=='pe32':
                builder=n['_PE32LoaderBuilder'](args['image_base']+rva)
                builder.mov_eax_label_va('diag_name')
                builder.emit(b'\x90'*3800)
                builder.label('diag_name')
                builder.emit(b'DLL or missing export\x00')
                return builder.finish()
            builder=n['_PE64LoaderBuilder'](rva)
            builder.rip32(b'\x48\x8D\x0D',rva+3200)
            builder.emit(b'\x90'*3800)
            return builder.finish()
        original=generate(args['loader_rva'])
        raw,virt=n['_pe_try_compress_second_stage_loader'](
            target=target,loader=original,rebuild_loader=generate,**args)
        decision=n['PE_LOADER_COMPRESSION_LAST_DECISION'][target]
        assert decision['enabled'], (target, decision)
        assert len(raw)<len(original)
        assert virt > len(raw)
        assert args['loader_rva']+virt<=args['ztext_rva']
        assert decision['destination_rva'] >= args['loader_rva']+n['_align_up'](len(raw),512)
        decompressed=zlib.decompress(raw[decision['bootstrap_size']:])
        assert decompressed==generate(decision['destination_rva'])
        assert b'DLL or missing export' in decompressed if target=='pe32' else True

def test_d64l_marker_outside_compressed_stream():
    n=make_context()
    imports=iats()
    marker=n['PE_D64_LOADER_INFO'].pack(b'D64L',1,4,0,3,225,1,2,2,0)
    def gen(rva):
        return b'\x90'*3900+marker
    original=gen(0x3000)
    packed,virt=n['_pe_try_compress_second_stage_loader'](
        target='pe32', loader=original, loader_rva=0x3000,
        ztext_rva=0x7000, iat_rvas=imports, image_base=0x400000,
        file_alignment=512, rebuild_loader=gen)
    assert n['PE_LOADER_COMPRESSION_LAST_DECISION']['pe32']['enabled']
    assert packed.endswith(marker)  # no decompression needed for version inspector
    assert packed.count(marker)==1
    decision=n['PE_LOADER_COMPRESSION_LAST_DECISION']['pe32']
    assert zlib.decompress(packed[decision['bootstrap_size']:-len(marker)])==original

def test_safe_fallback_cases():
    n=make_context()
    imports=iats()
    orig=b'\x90'*4000
    f=lambda rva:orig
    base=dict(target='pe32',loader=orig,loader_rva=0x3000,
              ztext_rva=0x7000,iat_rvas=imports,image_base=0x400000,
              file_alignment=512,rebuild_loader=f)
    result,virt=n['_pe_try_compress_second_stage_loader'](**dict(base,peb_resolver=True))
    assert result==orig and virt==len(orig)
    result,virt=n['_pe_try_compress_second_stage_loader'](**dict(base,ztext_rva=0x4000))
    assert result==orig and virt==len(orig)
    n['_pe32_mszip_compress_buffer']=lambda data:bytes(data)  # incompressible
    result,virt=n['_pe_try_compress_second_stage_loader'](**base)
    assert result==orig and virt==len(orig)

def test_pe_section_layout_no_bss_shift():
    ns=make_context()
    ns.update(IMAGE_FILE_MACHINE_I386=0x14c, IMAGE_FILE_MACHINE_AMD64=0x8664,
              PE64_FILE_ALIGNMENT=512, PE64_SECTION_ALIGNMENT=4096,
              PE32_FILE_ALIGNMENT=512, PE32_SECTION_ALIGNMENT=4096,
              PE_STAGE170_DOS_HEADER_SIZE=0x40, PE_IMAGE_LAYOUT_DEFAULT='default',
              _pe_physical_layout_sort_key=lambda name, layout, i:i)
    node=next(x for x in NODES if isinstance(x,ast.FunctionDef) and x.name=='_pe_emit_stage170_image')
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<writer>','exec'),ns)
    for machine,base in ((0x14c,0x400000),(0x8664,0x140000000)):
        orig=b'\x90'*3900
        # Test compression decision, with the same RVA layout used by the PE emitter.
        loader, virt=ns['_pe_try_compress_second_stage_loader'](
            target='pe64' if machine==0x8664 else 'pe32',
            loader=orig,loader_rva=0x3000,ztext_rva=0x7000,
            iat_rvas=iats(),image_base=base,file_alignment=512,
            rebuild_loader=lambda address:orig)
        assert len(loader)<len(orig) and virt>len(loader)
        image=ns['_pe_emit_stage170_image'](machine=machine,image_base=base,
            text_rva=0x1000,text_virtual_size=0x2000,
            loader_rva=0x3000,loader=loader,loader_virtual_size=virt,
            ztext_rva=0x7000,ztext=b'D64Z'+b'x'*100,
            ztext_virtual_size=0x2000,idata_rva=0x9000,idata=b'hello',
            first_iat_rva=0,iat_size=0,entry_rva=0x3000,gui=False,
            bss_rva=0xA000,bss_size=0x300)
        pe=struct.unpack_from('<I',image,0x3c)[0]
        assert image[pe:pe+4]==b'PE\x00\x00'
        n=struct.unpack_from('<H',image,pe+6)[0]
        assert n==5
        optional_size=struct.unpack_from('<H',image,pe+20)[0]
        headers=pe+24+optional_size
        secs={}
        for i in range(n):
            at=headers+40*i
            name=image[at:at+8].rstrip(b'\x00')
            virtual,rva,raw_size,raw_ptr=struct.unpack_from('<IIII',image,at+8)
            secs[name]=(virtual,rva,raw_size,raw_ptr)
        assert secs[b'.loader'][0]==virt
        assert secs[b'.loader'][1]+virt<=secs[b'.ztext'][1]
        assert image[secs[b'.loader'][3]:secs[b'.loader'][3]+len(loader)]==loader
        assert secs[b'.bss'][1]==0xA000 and secs[b'.bss'][2]==0
        assert struct.unpack_from('<I',image,pe+24+0x10)[0]==0x3000

def test_source_integration():
    assert SOURCE.count('loader, loader_virtual_size = _pe_try_compress_second_stage_loader(')==4
    assert SOURCE.count('loader_virtual_size=loader_virtual_size,')==2
    assert SOURCE.count('"virtual_size": loader_virtual_size,')==2
    assert 'max(len(loader), int(loader_virtual_size))' in SOURCE

if __name__=='__main__':
    for fn in (test_bootstrap_architectures,test_second_stage_rebased_32_64,
               test_safe_fallback_cases,test_d64l_marker_outside_compressed_stream,
               test_pe_section_layout_no_bss_shift,test_source_integration):
        fn(); print('PASS',fn.__name__)
