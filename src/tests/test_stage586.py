"""Stage 586: x86-Stackframe-Kontexthilfe im ASM-Editor."""

import ast
import re
import unittest
from pathlib import Path

from asm_stack_frame_tooltips import (
    stack_frame_pair_tooltip, stack_frame_allocation_tooltip,
    stack_frame_memory_tooltip, esp_stack_slot_tooltip
)


ROOT = Path(__file__).resolve().parent


class Block:
    def __init__(self, text):
        self._text = text
        self._before = None
        self._after = None

    def text(self):
        return self._text

    def previous(self):
        return self._before if self._before is not None else InvalidBlock()

    def next(self):
        return self._after if self._after is not None else InvalidBlock()

    def isValid(self):
        return True


class InvalidBlock:
    def isValid(self):
        return False


def fake_document(lines):
    blocks = [Block(line) for line in lines]
    for index, block in enumerate(blocks):
        block._before = blocks[index - 1] if index else None
        block._after = blocks[index + 1] if index + 1 < len(blocks) else None
    return blocks


def extract_editor_stack_methods():
    """Lädt die zwei realen ASM-Editor-Methoden isoliert ohne PyQt5."""
    source = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
    # Die unveränderten Python-3.15-Lazy-Imports werden nur zum AST-Test ersetzt.
    source = re.sub(r"(?m)^(\s*)lazy (from|import) ", r"\1\2 ", source)
    module = ast.parse(source)
    classes = [node for node in ast.walk(module)
               if isinstance(node, ast.ClassDef) and node.name == "SourceTextEdit"]
    assert len(classes) == 1
    methods = [node for node in classes[0].body
               if isinstance(node, ast.FunctionDef)
               and node.name in ("_adjacent_asm_instruction_block",
                                 "_stack_frame_tooltip_for_block")]
    assert len(methods) == 2
    cls = ast.ClassDef(name="StackEditor", bases=[], keywords=[], body=methods,
                       decorator_list=[])
    isolated = ast.Module(body=[cls], type_ignores=[])
    ast.fix_missing_locations(isolated)
    scope = {"stack_frame_pair_tooltip": stack_frame_pair_tooltip,
             "stack_frame_allocation_tooltip": stack_frame_allocation_tooltip,
             "stack_frame_memory_tooltip": stack_frame_memory_tooltip,
             "esp_stack_slot_tooltip": esp_stack_slot_tooltip,
             "re": re}
    exec(compile(isolated, "<stage586-isolated>", "exec"), scope)
    return scope["StackEditor"]


class StackFrameTooltipTests(unittest.TestCase):
    def test_pe32_prolog(self):
        tip = stack_frame_pair_tooltip('    push ebp', '    mov ebp, esp')
        self.assertIsNotNone(tip)
        self.assertIn('Funktionsprolog', tip.title)
        self.assertIn('push ebp:', tip.description)
        self.assertIn('mov ebp, esp:', tip.description)
        self.assertIn('nicht der gesamte Stackinhalt', tip.description)

    def test_pe32_epilog(self):
        tip = stack_frame_pair_tooltip('    mov esp, ebp', '    pop ebp')
        self.assertIsNotNone(tip)
        self.assertIn('Funktionsepilog', tip.title)
        self.assertIn('push ebp', tip.description)
        self.assertIn('mov ebp, esp', tip.description)

    def test_comments_spacing_labels_and_case(self):
        tip = stack_frame_pair_tooltip(
            '  start: PUSH EBP ; save', ' MoV EBP , ESP ; create', 'pe32')
        self.assertIsNotNone(tip)
        self.assertIsNotNone(stack_frame_pair_tooltip(
            '  MOV ESP , EBP', '   Pop Ebp  ; restore', 'pe32'))

    def test_other_targets_and_wrong_order(self):
        for target in ('c64', 'amiga'):
            self.assertIsNone(stack_frame_pair_tooltip('push ebp', 'mov ebp,esp', target))
        for a, b in [('push eax', 'mov ebp,esp'),
                     ('push ebp', 'mov esp,ebp'),
                     ('mov ebp,esp', 'push ebp'),
                     ('mov esp,ebp', 'pop eax'),
                     ('; push ebp', 'mov ebp,esp'),
                     ('push ebp!', 'mov ebp,esp'),
                     ('push ebp', 'mov ebp,esi')]:
            self.assertIsNone(stack_frame_pair_tooltip(a, b, 'pe32'), (a, b))

    def test_pe64_analog(self):
        self.assertIn('RBP', stack_frame_pair_tooltip(
            'push rbp', 'mov rbp, rsp', 'pe64').instructions)
        self.assertIn('RSP', stack_frame_pair_tooltip(
            'mov rsp, rbp', 'pop rbp', 'pe64').instructions)
        self.assertIsNone(stack_frame_pair_tooltip('push ebp', 'mov ebp,esp', 'pe64'))

    def test_editor_recognizes_pair_from_both_lines(self):
        Editor = extract_editor_stack_methods()
        obj = Editor()
        obj._assembler_target = 'pe32'
        blocks = fake_document([
            'foo:', '; comment', 'push ebp', '', '; setup', '  mov ebp, esp',
            'sub esp,4', 'mov esp, ebp', '  pop ebp', 'ret',
        ])
        for index in (2, 5):
            tip = obj._stack_frame_tooltip_for_block(blocks[index])
            self.assertIsNotNone(tip)
            self.assertIn('Funktionsprolog', tip.title)
        for index in (7, 8):
            tip = obj._stack_frame_tooltip_for_block(blocks[index])
            self.assertIsNotNone(tip)
            self.assertIn('Funktionsepilog', tip.title)
        allocation_tip = obj._stack_frame_tooltip_for_block(blocks[6])
        self.assertIsNotNone(allocation_tip)
        self.assertIn('sub esp, 4', allocation_tip.description)
        self.assertIsNone(obj._stack_frame_tooltip_for_block(blocks[9]))
        obj._assembler_target = 'c64'
        self.assertIsNone(obj._stack_frame_tooltip_for_block(blocks[2]))

    def test_editor_wont_skip_other_instruction_or_label(self):
        Editor = extract_editor_stack_methods()
        editor = Editor()
        editor._assembler_target = 'pe32'
        blocks = fake_document(['push ebp', 'nop', 'mov ebp,esp'])
        self.assertIsNone(editor._stack_frame_tooltip_for_block(blocks[0]))
        self.assertIsNone(editor._stack_frame_tooltip_for_block(blocks[2]))
        blocks = fake_document(['push ebp', 'other:', 'mov ebp,esp'])
        self.assertIsNone(editor._stack_frame_tooltip_for_block(blocks[2]))

    def test_asm_help_wiring_exists_and_respects_settings(self):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        self.assertIn('self._stack_frame_tooltip_for_block(cursor.block())', source)
        self.assertIn('self._stack_frame_tooltip_for_block(block)', source)
        self.assertIn('if isinstance(semantic, StackFrameTooltip):', source)
        self.assertIn('if not self._assembler_tooltips_allowed():', source)


if __name__ == '__main__':
    unittest.main()
