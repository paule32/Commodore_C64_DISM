"""Stage 609: real pe32/pe64 COFF→DLL smoke checks with peephole enabled.

Runs without Qt; loads the same internal PE assembler/linker as Stage 605.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from d64dbase import compile_dbase_to_assembly
from pascal_console_dependencies import inspect_pe
from test_stage605_link import _load_pe_linker

ROOT=Path(__file__).parent
SOURCE=(ROOT/'runtime/dbase/src/System.Objects.prg').read_text('utf-8')
OPTIONS={'register_width':True,'processor_flags':True,'stack_state':True}

class Stage609Links(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.linker=_load_pe_linker()

    def test_real_pe32_optimized_dbase_runtime_dll(self):
        self._compile_and_link('pe32',0x14c)

    def test_real_pe64_optimized_dbase_runtime_dll(self):
        self._compile_and_link('pe64',0x8664)

    def _compile_and_link(self,target,machine):
        gen=compile_dbase_to_assembly(SOURCE,target=target,source_kind='library',peephole_options=OPTIONS)
        linker=self.linker
        if target=='pe32':
            obj=linker['assemble_pe32_object_source'](gen.assembly, filename='System.Objects.prg')
            blob=linker['write_coff32_object'](obj)
            dll=linker['link_coff32_objects']((blob,),entry_symbol='__d64_dll_entry',dll=True,dll_name='RuntimeDB.dll')
        else:
            obj=linker['assemble_pe64_object_source'](gen.assembly,filename='System.Objects.prg')
            blob=linker['write_coff64_object'](obj)
            dll=linker['link_coff64_objects']((blob,),entry_symbol='__d64_dll_entry',dll=True,dll_name='RuntimeDB.dll')
        with TemporaryDirectory() as directory:
            path=Path(directory)/'RuntimeDB.dll'
            path.write_bytes(dll.executable)
            actual_machine,imports,exports=inspect_pe(path)
        self.assertEqual(actual_machine,machine)
        self.assertIn('libd64_qt5.dll',{name.casefold() for name in imports})
        for symbol in ('__dbase_cls_tobject_create', '__dbase_cls_tobject_free',
                       '__dbase_cls_tobject_vmt','__dbase_cls_tobject_classname'):
            self.assertIn(symbol,exports)
        self.assertEqual(len(exports),12)

if __name__=='__main__':unittest.main()
