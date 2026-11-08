"""Stage 546: IDE and compiler preprocessor must agree on {$L Runtime}.

Run: python -m unittest -v test_stage546
The GUI-independent IDE preprocessor is extracted from the actual d64_dism.py,
so the native Python-3.15 lazy import and optional PyQt dependencies are not
needed for these directed tests on earlier interpreters.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import types
import tempfile
import unittest
from typing import Dict, List, Optional, Tuple, Iterable

from test_stage532 import _compiler

ROOT = Path(__file__).resolve().parent
D64 = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
C = _compiler()


def ide_preprocess():
    begin = D64.index("class PascalPreprocessorError(")
    end = D64.index("\nfrom flags_rc", begin)
    module = types.ModuleType("_stage546_ide_preprocess")
    sys.modules[module.__name__] = module
    namespace = module.__dict__
    namespace.update({"__name__": module.__name__, "__builtins__": __builtins__,
                 "dt": dt, "dataclass": dataclass, "Path": Path, "re": re,
                 "Dict": Dict, "List": List, "Optional": Optional,
                 "Tuple": Tuple, "Iterable": Iterable})
    exec(compile(D64[begin:end], "d64_dism.py", "exec"), namespace)
    return namespace["preprocess_pascal_source"], namespace["PascalPreprocessorError"]


IDE_PREPROCESS, IDE_ERROR = ide_preprocess()


class Stage546Tests(unittest.TestCase):
    def test_bare_dll_name_is_accepted_by_ide_and_pascal_frontend(self):
        for name in ('Runtime', 'Runtime.dll', "'Runtime'", '"Runtime.dll"'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'test_raise.pas'
                text = f'program Test;\n{{$L {name}}}\nbegin end.\n'
                result = IDE_PREPROCESS(text, filename=str(path))
                self.assertEqual([Path(x).name for x in result.link_dlls], ['Runtime.dll'])
                self.assertEqual(result.link_files, ())
                self.assertEqual(text.count('\n'), result.source.count('\n'))
                self.assertNotIn('{$L', result.source)
                second = C.PascalPreprocessor().process(text, filename=str(path))
                self.assertEqual([Path(x).name for x in second.link_dlls], ['Runtime.dll'])

    def test_source_near_dll_or_link_search_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / 'source'
            target_dir = root / 'pe32'
            source_dir.mkdir()
            target_dir.mkdir()
            dll = target_dir / 'Runtime.dll'
            dll.write_bytes(b'EXAMPLE')
            source = source_dir / 'test_raise.pas'
            result = IDE_PREPROCESS('{$L Runtime}', filename=str(source),
                link_search_paths=(target_dir,))
            self.assertEqual(result.link_dlls, (str(dll.resolve()),))

    def test_combined_objects_libs_and_dll_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test_raise.pas'
            content = "\n".join(['{$L Runtime}', '{$L Runtime.dll}',
                '{$L inttostr.o}', '{$LINK strtoint.obj}',
                '{$LINKLIB container.a}', '{$L libhelper.lib}',
                '{$L Runtime}'])
            result = IDE_PREPROCESS(content, filename=str(path))
            self.assertEqual([Path(x).name for x in result.link_dlls], ['Runtime.dll'])
            self.assertEqual([Path(x).name for x in result.link_files],
                ['inttostr.o','strtoint.obj','container.a','libhelper.lib'])

    def test_invalid_extensions_rejected_and_inactive_dll_ignored(self):
        for text in ('{$LINK Runtime}', '{$LINKLIB Runtime}', '{$L foo.txt}',
                     '{$L}', '{$L ""}'):
            with self.subTest(text=text):
                with self.assertRaises(IDE_ERROR):
                    IDE_PREPROCESS(text)
        result = IDE_PREPROCESS('{$ifdef MISSING}\n{$L Runtime}\n{$else}\n{$L inttostr.o}\n{$endif}')
        self.assertFalse(result.link_dlls)
        self.assertEqual([Path(p).name for p in result.link_files], ['inttostr.o'])

    def test_export_directives_survive_only_active_branches(self):
        src = ('{$export TFoo}\n'
               'type TFoo = class end;\n'
               '{$ifdef ABSENT}\n{$export Other}\n{$endif}\n')
        result = IDE_PREPROCESS(src)
        self.assertIn('{$export TFoo}', result.source)
        self.assertNotIn('{$export Other}', result.source)
        self.assertEqual(src.count('\n'), result.source.count('\n'))
        from pascal_class_exports import exported_classes
        self.assertEqual(exported_classes(result.source, C._pascal_code_mask(result.source)), ('TFoo',))
        with self.assertRaisesRegex(IDE_ERROR, 'Klassennamen'):
            IDE_PREPROCESS('{$export Missing.Class}')

    def test_ide_to_compiler_linked_dll_contract_passthrough(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'test_raise.pas'
            preprocess = IDE_PREPROCESS('program Test; {$L Runtime} begin end.', filename=str(src))
            self.assertEqual(len(preprocess.link_dlls), 1)
            # Simulate IDE: the directive has been blanked, but the compiler
            # still receives the dependency explicitly via linked_dll_files.
            pos = C.SourcePosition(1, 1)
            parsed = C.PascalProgram('Test', (), (), C.CompoundStatement(pos, ()))
            from unittest.mock import patch
            with patch.object(C, '_parse_pascal_program_with_progress', return_value=parsed):
                _, details = C._parse_pascal_frontend(preprocess.source,
                    filename=str(src), target='pe32', linked_dll_files=preprocess.link_dlls)
            self.assertEqual(details.link_dlls, preprocess.link_dlls)

    def test_project_and_cli_paths_propagate_dlls(self):
        self.assertIn('compiler_kwargs["linked_dll_files"]', D64)
        self.assertIn('kwargs["linked_dll_files"]', D64)
        self.assertIn('getattr(pascal_preprocessed, "link_dlls", ())', D64)


if __name__ == '__main__':
    unittest.main()
