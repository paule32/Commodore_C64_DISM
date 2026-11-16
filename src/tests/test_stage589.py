"""Stage 589: Stackframe-Tooltip-Slots und pixelgenaue Sprungziele."""
import ast
import re
import textwrap
import unittest
from pathlib import Path

from asm_stack_frame_tooltips import stack_frame_memory_tooltip
from test_stage586 import extract_editor_stack_methods, fake_document

ROOT = Path(__file__).resolve().parent
BASE_EXAMPLE = '''
__pas_global_example:
push ebp
mov ebp, esp
sub esp, 4
call __pas_cookie_initialize
mov edx, dword ptr [__pas_cookie_secret]
xor edx, ebp
mov dword ptr [ebp-4], edx
push ebx
push esi
push edi
sub esp, 4
xor eax, eax
mov ebx, dword ptr [ebp-8]
mov esi, dword ptr [ebp-12]
mov edi, dword ptr [ebp-16]
mov esp, ebp
pop ebp
ret
'''.strip().splitlines()


class FrameMemoryTooltipTests(unittest.TestCase):
    def test_store_edx_is_local_not_parameter(self):
        tip = stack_frame_memory_tooltip(BASE_EXAMPLE, 7)
        self.assertIsNotNone(tip)
        self.assertIn('EBP-4', tip.instructions)
        self.assertIn('32-Bit', tip.description)
        self.assertIn('Stack-Cookie', tip.description)
        self.assertIn('[EBP+8]', tip.description)
        self.assertIn('kein erster Funktionsparameter', tip.description)

    def test_register_restores_are_not_parameters(self):
        for i in (13, 14, 15):
            tip = stack_frame_memory_tooltip(BASE_EXAMPLE, i)
            self.assertIsNotNone(tip)
            self.assertIn('EBX', tip.instructions)
            self.assertIn('ESI', tip.instructions)
            self.assertIn('EDI', tip.instructions)
            self.assertIn('keine zweiten, dritten oder vierten Funktionsparameter', tip.description)
            self.assertIn('PUSH EBX', tip.description)

    def test_missing_prolog_or_allocation_does_not_guess(self):
        self.assertIsNone(stack_frame_memory_tooltip([
            'mov dword ptr [ebp-4], edx'], 0))
        self.assertIsNone(stack_frame_memory_tooltip([
            'push ebp', 'mov ebp, esp', 'mov dword ptr [ebp-4], edx'], 2))
        self.assertIsNone(stack_frame_memory_tooltip(BASE_EXAMPLE, 7, 'pe64'))
        self.assertIsNone(stack_frame_memory_tooltip(BASE_EXAMPLE, 7, 'c64'))
        self.assertIsNone(stack_frame_memory_tooltip([
            'push ebp','mov ebp,esp','sub esp,4','ret',
            'mov dword ptr [ebp-4],edx'], 4))

    def test_false_register_restore_without_push_is_not_described(self):
        data = [line for line in BASE_EXAMPLE if not re.match(r'^push (?:ebx|esi|edi)$', line)]
        idx = data.index('mov ebx, dword ptr [ebp-8]')
        self.assertIsNone(stack_frame_memory_tooltip(data, idx))

    def test_offsets_change_if_extra_stack_space_used(self):
        data = BASE_EXAMPLE.copy()
        at = data.index('push ebx')
        data.insert(at, 'sub esp, 4')
        idx = data.index('mov ebx, dword ptr [ebp-8]')
        self.assertIsNone(stack_frame_memory_tooltip(data, idx))
        data[idx] = 'mov ebx, dword ptr [ebp-12]'
        data[idx+1] = 'mov esi, dword ptr [ebp-16]'
        data[idx+2] = 'mov edi, dword ptr [ebp-20]'
        self.assertIsNotNone(stack_frame_memory_tooltip(data, idx))

    def test_editor_integration_respects_hovered_mnemonic(self):
        editor = extract_editor_stack_methods()()
        editor._assembler_target = 'pe32'
        blocks = fake_document(BASE_EXAMPLE)
        for idx in (7, 13, 14, 15):
            self.assertIsNotNone(editor._stack_frame_tooltip_for_block(blocks[idx]))
        editor._assembler_target = 'c64'
        self.assertIsNone(editor._stack_frame_tooltip_for_block(blocks[7]))


class _Rect:
    def __init__(self, left):
        self._left=left
    def left(self): return self._left
    def top(self): return 0
    def bottom(self): return 16


class _Point:
    def __init__(self,x,y=8): self._x=x; self._y=y
    def x(self): return self._x
    def y(self): return self._y


class _DocCursor:
    def __init__(self, document): self.position = 0
    def setPosition(self,p): self.position=p


class _Block:
    def __init__(self,text): self._text=text
    def text(self): return self._text
    def position(self): return 0


class _Cursor:
    def __init__(self,block,pos): self._block=block; self._pos=pos
    def block(self): return self._block
    def positionInBlock(self): return self._pos


class _Highlighter:
    JUMP_TARGET_PATTERN = re.compile(
        r'^\s*(?:JNE|JMP|CALL)\s+(?P<target>[A-Za-z_.$][A-Za-z0-9_.$]*)',re.I)
    def jump_target_at(self,text,pos):
        match=self.JUMP_TARGET_PATTERN.match(text)
        return match.group('target') if match and match.start('target') <= pos <= match.end('target') else None


class JumpPixelHitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        first = source.index('        def _jump_target_at_point(self, point):',
                             source.index('class SourceTextEdit'))
        last = source.index('\n        def _jump_to_label(', first)
        isolated = 'class Editor:\n' + textwrap.indent(textwrap.dedent(source[first:last]).rstrip(), '    ') + '\n'
        scope={'QTextCursor':_DocCursor}
        exec(compile(isolated, '<stage589-jump-hitbox>', 'exec'),scope)
        cls.Editor = scope['Editor']

    def test_hitbox_stops_at_end_of_label_not_editor_width(self):
        editor=self.Editor()
        editor._assembler_navigation_enabled=True
        editor._assembler_highlighter=_Highlighter()
        editor.document=lambda: None
        editor.cursorForPosition=lambda point: _Cursor(_Block('JNE destination'), min(len('JNE destination'), point.x()//8))
        editor.cursorRect=lambda cursor: _Rect(cursor.position*8)
        self.assertEqual(editor._jump_target_at_point(_Point(4*8+1)), 'destination')
        self.assertEqual(editor._jump_target_at_point(_Point(14*8)), 'destination')
        self.assertIsNone(editor._jump_target_at_point(_Point(15*8)))
        self.assertIsNone(editor._jump_target_at_point(_Point(80*8)))
        self.assertIsNone(editor._jump_target_at_point(_Point(4*8+1,25)))

    def test_other_targets_and_comments(self):
        editor=self.Editor()
        editor._assembler_navigation_enabled=True
        editor._assembler_highlighter=_Highlighter()
        editor.document=lambda: None
        editor.cursorRect=lambda c:_Rect(c.position*8)
        for line in ('CALL proc1 ; comment','JMP next','JNE otherwise'):
            editor.cursorForPosition=lambda point, line=line: _Cursor(_Block(line), min(len(line),point.x()//8))
            start=re.search(r'\s(\w+)',line).start(1)
            self.assertIsNotNone(editor._jump_target_at_point(_Point((start+1)*8)))
            self.assertIsNone(editor._jump_target_at_point(_Point(90*8)))


if __name__ == '__main__':
    unittest.main()
