"""Stage 588: ASM-SUB-Stackreservierung im Kontext des Funktionsprologs."""
import unittest

from asm_stack_frame_tooltips import (
    stack_frame_allocation_tooltip,
    stack_frame_pair_tooltip,
)
from test_stage586 import extract_editor_stack_methods, fake_document


class StackFrameAllocationTooltipTests(unittest.TestCase):
    def test_pe32_sub_reserves_four_bytes_and_does_not_write(self):
        tip = stack_frame_allocation_tooltip(
            ' push ebp', ' mov ebp, esp', ' sub esp, 4', 'pe32'
        )
        self.assertIsNotNone(tip)
        self.assertIn('PUSH EBP', tip.instructions)
        self.assertIn('MOV EBP, ESP', tip.instructions)
        self.assertIn('SUB ESP, 4', tip.instructions)
        self.assertIn('32-Bit-Wert', tip.description)
        self.assertIn('[ebp-4]', tip.description)
        self.assertIn('nach unten', tip.description)
        self.assertIn('noch keinen Variablenwert', tip.description)
        self.assertIn('pop ebp', tip.description)

    def test_assembler_editor_shows_triple_only_on_sub(self):
        editor = extract_editor_stack_methods()()
        editor._assembler_target = 'pe32'
        blocks = fake_document([
            'start:', 'push ebp ; old base', '  ; info',
            ' MOV EBP, ESP', '', 'sub esp, 4 ; local integer',
            'mov dword ptr [ebp-4], 123',
        ])
        for index in (1, 3):
            tip = editor._stack_frame_tooltip_for_block(blocks[index])
            self.assertIsNotNone(tip)
            self.assertIn('Stackframe sichern', tip.title)
        tip = editor._stack_frame_tooltip_for_block(blocks[5])
        self.assertIsNotNone(tip)
        self.assertIn('Stack-Speicher', tip.title)
        self.assertIsNone(editor._stack_frame_tooltip_for_block(blocks[6]))

    def test_not_triggered_on_unrelated_sub_or_other_targets(self):
        for candidate in (
            'sub eax, 4', 'sub esp, eax', 'sub esp, -4',
            'sub esp, 0', 'sub esp, 4 garbage',
            '; sub esp, 4', 'add esp, 4',
        ):
            self.assertIsNone(stack_frame_allocation_tooltip(
                'push ebp', 'mov ebp, esp', candidate), candidate)
        for first, second in (
            ('push ebx', 'mov ebp, esp'),
            ('push ebp', 'mov esp, ebp'),
            ('mov ebp, esp', 'push ebp'),
        ):
            self.assertIsNone(stack_frame_allocation_tooltip(
                first, second, 'sub esp, 4'))
        self.assertIsNone(stack_frame_allocation_tooltip(
            'push ebp', 'mov ebp, esp', 'sub esp, 4', 'c64'))
        self.assertIsNone(stack_frame_allocation_tooltip(
            'push ebp', 'mov ebp, esp', 'sub rsp, 4', 'pe32'))

    def test_does_not_cross_real_instructions_or_labels(self):
        editor = extract_editor_stack_methods()()
        editor._assembler_target = 'pe32'
        for texts in (
            ['push ebp', 'mov ebp, esp', 'nop', 'sub esp,4'],
            ['push ebp', 'some_label:', 'mov ebp, esp', 'sub esp,4'],
            ['push ebp', 'mov ebp, esp', 'some_label:', 'sub esp,4'],
            ['push ebp', ';a',';b',';c',';d',';e', 'mov ebp, esp','sub esp,4'],
        ):
            blocks = fake_document(texts)
            self.assertIsNone(editor._stack_frame_tooltip_for_block(blocks[-1]), texts)

    def test_pe64_equivalent_and_other_sizes(self):
        tip = stack_frame_allocation_tooltip(
            'push rbp', 'mov rbp, rsp', 'sub rsp, 8', 'pe64'
        )
        self.assertIsNotNone(tip)
        self.assertIn('64-Bit-Wert', tip.description)
        self.assertIn('[rbp-8]', tip.description)
        tip = stack_frame_allocation_tooltip(
            'label: PUSH EBP ; save', 'mov ebp,esp',
            'SUB ESP, 0x10 ; 16 local bytes', 'pe32'
        )
        self.assertIn('16 Byte', tip.description)
        self.assertIn('SUB ESP, 16', tip.instructions)
        self.assertIsNotNone(stack_frame_allocation_tooltip(
            'push ebp', 'mov ebp,esp', 'sub esp, 04'))

    def test_existing_epilog_remains_unchanged(self):
        tip = stack_frame_pair_tooltip('mov esp, ebp', 'pop ebp')
        self.assertIn('Funktionsepilog', tip.title)


if __name__ == '__main__':
    unittest.main()
