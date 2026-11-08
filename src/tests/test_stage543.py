"""Stage 543: exported-class unit resolver must remember unit names.

These tests intentionally exercise the real resolver with metadata mocks; parser
or Windows are not needed. Run: python -m unittest -v test_stage543
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_stage532 import _compiler

c = _compiler()
P = c.SourcePosition(55, 1)


class Stage543ResolverTests(unittest.TestCase):
    def test_exported_unit_only_once_with_diamond_uses_graph(self):
        # Windows -> (Windows.Application, VCL) -> VCL.Windows.
        graph = {
            "windows": ("Windows.Application", "VCL"),
            "windows.application": ("VCL.Windows",),
            "vcl": ("VCL.Windows",),
            "vcl.windows": (),
        }
        contract = {"name": "TWindow", "methods": [], "fields": [], "properties": []}
        global_proc = c.GlobalRoutineImplementation(
            "function", "GlobalWindowProc", (), "integer", (),
            c.CompoundStatement(P, ()), P,
        )
        parse_count = {}

        def fake_read(path, unit_name):
            key = unit_name.casefold()
            return {"unit": unit_name, "exported_classes": ["TWindow"] if key == "vcl.windows" else []}

        def fake_uses(doc):
            return graph[doc["unit"].casefold()], ()

        def fake_contract(doc):
            return [contract] if doc["unit"].casefold() == "vcl.windows" else []

        def fake_program(doc):
            key = doc["unit"].casefold()
            parse_count[key] = parse_count.get(key, 0) + 1
            return c.PascalProgram(
                f"__pui_{key}", (), (), c.CompoundStatement(P, ()),
                global_routines=(global_proc,) if key == "vcl.windows" else (),
            )

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            resolver = c._PascalUnitResolver(
                filename=str(directory / 'test.pas'),
                include_paths=(directory,),
                preprocessor=c.PascalPreprocessor(),
                target="pe32",
            )
            with (
                patch.object(c, '_find_unit_artifacts', side_effect=lambda name, *_: [directory / f'{name}.pui']),
                patch.object(c, '_find_unit_file', return_value=None),
                patch.object(c, '_read_pui_document', side_effect=fake_read),
                patch.object(c, '_pui_validate_target'),
                patch.object(c, '_pui_is_legacy', return_value=False),
                patch.object(c, '_pui_uses', side_effect=fake_uses),
                patch.object(c, '_pui_primary_object_file', return_value=None),
                patch.object(c, '_pui_link_object_files', return_value=()),
                patch.object(c, '_pui_program_from_metadata', side_effect=fake_program),
                patch('pascal_class_exports.public_class_contract', side_effect=fake_contract),
            ):
                resolver.resolve('Windows')
                resolver.resolve('VCL.Windows')
                self.assertEqual(len(resolver.programs), 4)
                self.assertEqual(parse_count['vcl.windows'], 1)
                self.assertEqual(set(resolver.resolved), set(graph))
                self.assertIn('twindow', resolver.class_export_contracts)
                self.assertNotIn('twindow', resolver.resolved)
                merged = c._merge_global_routines_for_link(
                    resolver.programs,
                    c.PascalProgram('Runtime', (), (), c.CompoundStatement(P, ())),
                )
                self.assertEqual([r.name for r in merged], ['GlobalWindowProc'])

    def test_no_export_unit_already_registered_by_unit_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            resolver=c._PascalUnitResolver(
                filename=str(directory / 'test.pas'),
                include_paths=(directory,),
                preprocessor=c.PascalPreprocessor(),
                target='pe32',
            )
            seen=[]
            def fake_program(doc):
                seen.append(doc['unit'])
                return c.PascalProgram(doc['unit'], (), (), c.CompoundStatement(P, ()))
            with (
                patch.object(c, '_find_unit_artifacts', side_effect=lambda name, *_: [directory / f'{name}.pui']),
                patch.object(c, '_find_unit_file', return_value=None),
                patch.object(c, '_read_pui_document', side_effect=lambda path, name: {'unit':name,'exported_classes':[]}),
                patch.object(c, '_pui_validate_target'),
                patch.object(c, '_pui_is_legacy', return_value=False),
                patch.object(c, '_pui_uses', return_value=((),())),
                patch.object(c, '_pui_primary_object_file', return_value=None),
                patch.object(c, '_pui_link_object_files', return_value=()),
                patch.object(c, '_pui_program_from_metadata', side_effect=fake_program),
                patch('pascal_class_exports.public_class_contract', return_value=[]),
            ):
                resolver.resolve('System')
                resolver.resolve('system')
                self.assertEqual(seen, ['System'])
                self.assertIn('system', resolver.resolved)

    def test_duplicate_implementation_within_single_unit_still_errors(self):
        duplicates=(
            c.GlobalRoutineImplementation('procedure', 'Duplicated', (), None, (), c.CompoundStatement(P, ()), P),
            c.GlobalRoutineImplementation('procedure', 'Duplicated', (), None, (), c.CompoundStatement(P, ()), P),
        )
        program=c.PascalProgram('Bad', (), (), c.CompoundStatement(P, ()), global_routines=duplicates)
        with self.assertRaisesRegex(c.C64PascalError, 'mehrfach implementiert'):
            c._PE32CodeGenerator(program).generate()


if __name__ == '__main__':
    unittest.main()
