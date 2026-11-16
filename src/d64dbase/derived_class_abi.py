"""Stage 612 – typed dBASE native derived CLASS/PROPERTY support.

Uses the existing JitVmt ABI. The first pointer in every instance is its
VMT; instance fields follow it in declaration order (including ancestors).
String fields have an adjacent ownership word. No source-manager state is
emitted into the PE image.
"""
from __future__ import annotations

import ast
import re

from .object_abi import _NativeSourceEmitter, method_label, vmt_label


def property_default(prop):
    """Return (type, value) for a statically initialized native field."""
    value = prop.initial_value.strip()
    if not value:
        return 'pointer', 0
    if value[0] in ('"', "'"):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            parsed = None
        if not isinstance(parsed, str):
            raise ValueError(f'PROPERTY {prop.name}: ungueltiger String-Startwert')
        return 'string', parsed
    try:
        return 'number', int(value, 0)
    except ValueError:
        raise ValueError(f'PROPERTY {prop.name}: Initialisierung erwartet String- oder Ganzzahl-Literal') from None


def field_layout(name, classes, word):
    """List (property, declaring-class, byte-offset, type) including ancestors."""
    current = classes[name.casefold()]
    ancestry = []
    seen = set()
    while current is not None:
        key = current.name.casefold()
        if key in seen:
            raise ValueError('Zyklische CLASS-Vererbung: ' + current.name)
        seen.add(key)
        ancestry.append(current)
        parent = str(getattr(current, 'parent', '') or '')
        current = classes.get(parent.casefold()) if parent else None
        if parent and current is None:
            raise ValueError(f'Unbekannte Elternklasse: {parent}')
    result = []
    for cls in reversed(ancestry):
        for prop in getattr(cls, 'properties', ()):
            if any(p.name.casefold() == prop.name.casefold() for p, *_ in result):
                raise ValueError(f'PROPERTY darf geerbte Felder nicht verdecken: {cls.name}.{prop.name}')
            result.append((prop, cls.name, word * (1 + 2 * len(result)), property_default(prop)[0]))
    return result


def _literal_data(label, value):
    # dBASE/Win32 strings are 8-bit ANSI and nul terminated.
    octets = value.encode('cp1252') + b'\x00'
    return [f'{label}:', '    db ' + ', '.join(str(ch) for ch in octets)]


def _concat3_assembly(is64):
    """One allocation for up to 3 parts: LocalAlloc + lstrcpyA/lstrcatA."""
    code = ['__dbase_cls_concat3:']
    if is64:
        code += [
            '    push rbp', '    mov rbp, rsp', '    sub rsp, 96',
            '    mov qword ptr [rbp-8], rcx',
            '    mov qword ptr [rbp-16], rdx',
            '    mov qword ptr [rbp-24], r8',
        ]
        for offset in (8, 16, 24):
            prefix = f'__dbase_cls_concat3_part{offset}'
            code += [f'    cmp qword ptr [rbp-{offset}], 0',
                     f'    jne {prefix}',
                     '    mov rax, __dbase_cls_empty',
                     f'    mov qword ptr [rbp-{offset}], rax',
                     f'{prefix}:']
        code += [
            '    mov rcx, qword ptr [rbp-8]', '    call __dbase_cls_api_lstrlenA',
            '    mov dword ptr [rbp-32], eax',
            '    mov rcx, qword ptr [rbp-16]', '    call __dbase_cls_api_lstrlenA',
            '    add dword ptr [rbp-32], eax',
            '    mov rcx, qword ptr [rbp-24]', '    call __dbase_cls_api_lstrlenA',
            '    add eax, dword ptr [rbp-32]', '    add eax, 1',
            '    mov edx, eax', '    mov ecx, 64', '    call __dbase_cls_api_LocalAlloc',
            '    mov qword ptr [rbp-40], rax', '    test rax, rax',
            '    jz __dbase_cls_concat3_done',
            '    mov rcx, rax', '    mov rdx, qword ptr [rbp-8]',
            '    call __dbase_cls_api_lstrcpyA',
            '    mov rcx, qword ptr [rbp-40]', '    mov rdx, qword ptr [rbp-16]',
            '    call __dbase_cls_api_lstrcatA',
            '    mov rcx, qword ptr [rbp-40]', '    mov rdx, qword ptr [rbp-24]',
            '    call __dbase_cls_api_lstrcatA',
            '    mov rax, qword ptr [rbp-40]',
            '__dbase_cls_concat3_done:', '    mov rsp, rbp', '    pop rbp', '    ret',
        ]
    else:
        code += [
            '    push ebp', '    mov ebp, esp', '    push ebx',
            '    push esi', '    push edi',
            '    mov esi, dword ptr [ebp+8]',
            '    mov edi, dword ptr [ebp+12]',
            '    mov edx, dword ptr [ebp+16]',
            '    test esi, esi', '    jnz __dbase_cls_concat3_first',
            '    mov esi, __dbase_cls_empty',
            '__dbase_cls_concat3_first:',
            '    test edi, edi', '    jnz __dbase_cls_concat3_second',
            '    mov edi, __dbase_cls_empty',
            '__dbase_cls_concat3_second:',
            '    test edx, edx', '    jnz __dbase_cls_concat3_third',
            '    mov edx, __dbase_cls_empty',
            '__dbase_cls_concat3_third:',
            '    push edx',  # keep third part on stack through API calls
            '    push esi', '    call __dbase_cls_api_lstrlenA',
            '    mov ebx, eax',
            '    push edi', '    call __dbase_cls_api_lstrlenA',
            '    add ebx, eax',
            '    push dword ptr [esp]', '    call __dbase_cls_api_lstrlenA',
            '    add ebx, eax', '    add ebx, 1',
            '    push ebx', '    push 64', '    call __dbase_cls_api_LocalAlloc',
            '    mov ebx, eax', '    test eax, eax',
            '    jz __dbase_cls_concat3_done',
            '    push esi', '    push ebx', '    call __dbase_cls_api_lstrcpyA',
            '    push edi', '    push ebx', '    call __dbase_cls_api_lstrcatA',
            '    push dword ptr [esp]', '    push ebx',
            '    call __dbase_cls_api_lstrcatA',
            '__dbase_cls_concat3_done:',
            '    add esp, 4', '    mov eax, ebx',
            '    pop edi', '    pop esi', '    pop ebx',
            '    mov esp, ebp', '    pop ebp', '    ret',
        ]
    return code


class DerivedMethodEmitter(_NativeSourceEmitter):
    def __init__(self, cls, method, *, target, prototypes, filename,
                 classes, optimize_null_comparisons=False):
        super().__init__(method, target=target, prototypes=prototypes,
                         filename=filename, optimize_null_comparisons=optimize_null_comparisons)
        self.cls = cls
        self.classes = classes
        self.fields = {p.name.casefold(): (p, owner, offset, typ)
                       for p, owner, offset, typ in field_layout(cls.name, classes, 8 if self.is64 else 4)}
        self.label_prefix = method_label(cls.name, method.name)
        self.end_label = self.label_prefix + '_source_end'
        self.literal_data = []
        self.concat_needed = False

    def _load(self, name, line):
        field = self.fields.get(name.casefold())
        if field is not None:
            prop, owner, offset, _typ = field
            if owner.casefold() != self.cls.name.casefold() and prop.visibility == 'private':
                self.error(f'PRIVATE PROPERTY {owner}.{prop.name} ist in {self.cls.name} nicht sichtbar.', line)
            super()._load('Self', line)
            self.emit(f'    mov {self.reg}, {self.ptr} [{self.reg}+{offset}]')
        else:
            super()._load(name, line)

    def _emit_expr(self, expr, line):
        from .compiler import DBaseLiteralExpression, DBaseBinaryExpression
        if isinstance(expr, DBaseLiteralExpression) and expr.value_type in ('string', 'char', 'text'):
            label = self.label_prefix + f'_string_{len(self.literal_data)}'
            self.literal_data.extend(_literal_data(label, str(expr.value)))
            self.emit(f'    mov {self.reg}, {label}')
            return
        if isinstance(expr, DBaseBinaryExpression) and expr.operator == '+':
            parts = []
            def flatten(node):
                if isinstance(node, DBaseBinaryExpression) and node.operator == '+':
                    flatten(node.left)
                    flatten(node.right)
                else:
                    parts.append(node)
            flatten(expr)
            if not 2 <= len(parts) <= 3:
                self.error('String-Verkettung in nativen Klassen: zwei bis drei Teile erlaubt.', line)
            self.concat_needed = True
            if self.is64:
                # Native x64: hold prior argument pointers in preserved stack
                # slots while evaluating remaining expressions.
                self._emit_expr(parts[0], line)
                self._push()
                self._emit_expr(parts[1], line)
                self._push()
                if len(parts) == 3:
                    self._emit_expr(parts[2], line)
                else:
                    self.emit(f'    mov {self.reg}, __dbase_cls_empty')
                self.emit('    mov r8, rax')
                self.emit('    pop rdx', '    pop rcx')
                self.stack_words -= 2
                self.emit('    sub rsp, 32', '    call __dbase_cls_concat3', '    add rsp, 32')
            else:
                self._emit_expr(parts[0], line)
                self._push()
                self._emit_expr(parts[1], line)
                if len(parts) == 3:
                    self._push()
                    self._emit_expr(parts[2], line)
                    self.emit('    pop edx', '    pop ecx')
                    self.stack_words -= 2
                    self.emit('    push eax', '    push edx', '    push ecx')
                else:
                    self.emit('    pop edx')
                    self.stack_words -= 1
                    self.emit('    push __dbase_cls_empty', '    push eax', '    push edx')
                self.emit('    call __dbase_cls_concat3', '    add esp, 12')
            return
        super()._emit_expr(expr, line)

    def _emit_super_init(self, argument, line):
        parent = str(self.cls.parent or '')
        declared = self.classes.get(parent.casefold())
        parent_methods = {item.name.casefold(): item for item in getattr(declared, 'methods', ())}
        init = parent_methods.get('__ini__')
        expected = len(init.parameters) if init else 0
        argument = argument.strip()
        if expected == 0 and argument.casefold() == 'self':
            # The explicitly supplied Self is an ABI receiver, not an extra arg.
            argument = ''
        if expected == 0 and argument:
            self.error('SUPER().__ini__ erwartet keinen zusaetzlichen Parameter.', line)
        if expected == 1 and not argument:
            self.error('SUPER().__ini__ erwartet einen Parameter.', line)
        if expected:
            self._emit_expr(self._expression(argument, line), line)
            self._push()
        super()._load('Self', line)
        if self.is64:
            self.emit('    mov rcx, rax')
            if expected:
                self.emit('    pop rdx')
                self.stack_words -= 1
            self.emit('    sub rsp, 32',
                      f'    call {method_label(parent, "__ini__")}',
                      '    add rsp, 32')
        else:
            self._push()
            self.emit(f'    call {method_label(parent, "__ini__")}',
                      f'    add esp, {4 * (1 + expected)}')
            self.stack_words -= 1 + expected

    def _emit_assignment(self, name, expression, line):
        field = self.fields.get(name.casefold())
        if field is None:
            self.error('Nur Klassen-PROPERTY kann in einer nativen Methode zugewiesen werden: ' + name, line)
        prop, owner, offset, typ = field
        if owner.casefold() != self.cls.name.casefold() and prop.visibility == 'private':
            self.error(f'PRIVATE PROPERTY {owner}.{prop.name} kann nicht geerbt werden.', line)
        if typ == 'pointer':
            self.error(f'PROPERTY {name} hat keinen festen Typ; Initialwert angeben.', line)
        expression_ast = self._expression(expression, line)
        from .compiler import DBaseBinaryExpression
        allocate = isinstance(expression_ast, DBaseBinaryExpression) and expression_ast.operator == '+'
        if typ == 'string' and not allocate:
            # Native method arguments and string literals are borrowed. Copy
            # them into an owned allocation before replacing a member slot.
            self._emit_expr(expression_ast, line)
            if self.is64:
                self.emit('    mov rcx, rax',
                          '    mov rdx, __dbase_cls_empty',
                          '    mov r8, __dbase_cls_empty',
                          '    sub rsp, 32', '    call __dbase_cls_concat3', '    add rsp, 32')
            else:
                self.emit('    push __dbase_cls_empty', '    push __dbase_cls_empty',
                          '    push eax', '    call __dbase_cls_concat3', '    add esp, 12')
            self.concat_needed = True
            allocate = True
        else:
            self._emit_expr(expression_ast, line)
        self._push()  # preserve value while inspecting receiver
        super()._load('Self', line)
        self.emit(f'    mov {self.other}, {self.reg}',
                  f'    pop {self.reg}')
        self.stack_words -= 1
        # Existing ownership: do not overwrite a heap pointer without freeing
        # it. Retain caller-volatile registers across the Windows API call.
        if typ == 'string':
            self.emit(f'    cmp {self.ptr} [{self.other}+{offset + (8 if self.is64 else 4)}], 0')
            skip = self.label('skip_free')
            self.emit(f'    je {skip}')
            if self.is64:
                self.emit('    push rax', '    push rdx',
                          f'    mov rcx, qword ptr [rdx+{offset}]',
                          '    sub rsp, 32', '    call __dbase_cls_api_LocalFree',
                          '    add rsp, 32', '    pop rdx', '    pop rax')
            else:
                self.emit('    push eax', '    push edx',
                          f'    push dword ptr [edx+{offset}]',
                          '    call __dbase_cls_api_LocalFree',
                          '    pop edx', '    pop eax')
            self.emit(f'{skip}:')
        self.emit(f'    mov {self.ptr} [{self.other}+{offset}], {self.reg}')
        if typ == 'string':
            self.emit(f'    mov {self.ptr} [{self.other}+{offset + (8 if self.is64 else 4)}], {1 if allocate else 0}')

    def compile(self):
        self.emit(f'{self.label_prefix}:')
        if self.is64:
            self.emit('    push rbp', '    mov rbp, rsp', '    sub rsp, 32',
                      '    mov qword ptr [rbp-8], rcx',
                      '    mov qword ptr [rbp-16], rdx')
        else:
            self.emit('    push ebp', '    mov ebp, esp')
        for lineno, raw in self.method.body:
            statement = raw.strip()
            bits = statement.split(None, 1)
            op = bits[0].casefold()
            expr_text = bits[1].strip() if len(bits) > 1 else ''
            if op == 'if':
                if not expr_text:
                    self.error('IF benoetigt eine Bedingung.', lineno)
                condition = self._expression(expr_text, lineno)
                false_label = self.label('else')
                end_label = self.label('endif')
                self._emit_conditional_jump_false(condition, lineno, false_label)
                self.condition_stack.append((false_label, end_label, False))
            elif op == 'else':
                if expr_text or not self.condition_stack:
                    self.error('ELSE ohne IF oder mit unerwarteten Argumenten.', lineno)
                false_label, end_label, done = self.condition_stack.pop()
                if done:
                    self.error('Doppeltes ELSE in Klassenmethode.', lineno)
                self.emit(f'    jmp {end_label}', f'{false_label}:')
                self.condition_stack.append((false_label, end_label, True))
            elif op == 'endif':
                if expr_text or not self.condition_stack:
                    self.error('ENDIF ohne IF in Klassenmethode.', lineno)
                false_label, end_label, done = self.condition_stack.pop()
                self.emit(f'{end_label if done else false_label}:')
            elif op == 'return':
                if expr_text:
                    if self.method.kind != 'function' and self.method.name.casefold() != '__ini__':
                        self.error(f'PROCEDURE {self.method.name} darf keinen Wert zurueckgeben.', lineno)
                    self._emit_expr(self._expression(expr_text, lineno), lineno)
                elif self.method.kind == 'function':
                    self.error(f'FUNCTION {self.method.name} muss einen Wert zurueckgeben.', lineno)
                self.emit(f'    jmp {self.end_label}')
            elif re.fullmatch(r'super\s*\(\s*\)\s*\.\s*__ini__\s*\((.*)\)\s*', statement, re.I):
                match = re.fullmatch(r'super\s*\(\s*\)\s*\.\s*__ini__\s*\((.*)\)\s*', statement, re.I)
                self._emit_super_init(match.group(1), lineno)
            elif re.fullmatch(r'[A-Za-z_]\w*\s*=\s*.+', statement):
                name, rhs = statement.split('=', 1)
                self._emit_assignment(name.strip(), rhs.strip(), lineno)
            else:
                expression = self._expression(statement, lineno)
                from .compiler import DBaseCallExpression
                if not isinstance(expression, DBaseCallExpression):
                    self.error('Klassenmember: Funktionsaufruf, PROPERTY-Zuweisung oder RETURN erwartet.', lineno)
                self._call(expression.name, expression.arguments, lineno)
        if self.condition_stack:
            self.error('ENDIF fehlt in Klassenmethode.')
        if self.stack_words:
            self.error('Stackbilanz der Klassenmethode ist nicht ausgeglichen.')
        self.emit(f'{self.end_label}:')
        self.emit('    mov rsp, rbp' if self.is64 else '    mov esp, ebp',
                  '    pop rbp' if self.is64 else '    pop ebp', '    ret')
        return self.lines, self.literal_data, self.concat_needed


def emit_derived_class(cls, *, classes, target, prototypes, filename,
                       optimize_null_comparisons=False):
    """Emit method bodies, VMT property init/finalize, factory + public getters."""
    is64 = target == 'pe64'
    word = 8 if is64 else 4
    ptr = 'qword ptr' if is64 else 'dword ptr'
    reg = 'rax' if is64 else 'eax'
    slots = field_layout(cls.name, classes, word)
    own_fields = [(p, owner, off, typ) for p, owner, off, typ in slots
                  if owner.casefold() == cls.name.casefold()]
    imports = []
    code, data = [], []
    uses_strings = False
    methods = {method.name.casefold(): method for method in getattr(cls, 'methods', ())}
    for method in getattr(cls, 'methods', ()):
        emitter = DerivedMethodEmitter(cls, method, target=target,
            prototypes=prototypes, filename=filename, classes=classes,
            optimize_null_comparisons=optimize_null_comparisons)
        emitted, strings, concat = emitter.compile()
        code.extend(emitted)
        data.extend(strings)
        uses_strings |= concat

    parent = str(cls.parent or '')
    inherit_fields = bool(parent.casefold() in classes and
                          len(field_layout(parent, classes, word)) > 0)
    init = method_label(cls.name, 'fields_init')
    fini = method_label(cls.name, 'fields_done')
    label_prefix = method_label(cls.name, 'default')
    code += [f'{init}:']
    if is64:
        code += ['    push rbp', '    mov rbp, rsp', '    sub rsp, 32',
                 '    mov qword ptr [rbp-8], rcx']
        if inherit_fields:
            code += [f'    call {method_label(parent, "fields_init")}']
        code += ['    mov rax, qword ptr [rbp-8]']
    else:
        code += ['    push ebp', '    mov ebp, esp']
        if inherit_fields:
            code += ['    push dword ptr [ebp+8]',
                     f'    call {method_label(parent, "fields_init")}',
                     '    add esp, 4']
        code += ['    mov eax, dword ptr [ebp+8]']
    for prop, _owner, offset, typ in own_fields:
        field_type, default = property_default(prop)
        if field_type == 'string':
            uses_strings = True
            name = label_prefix + '_' + prop.name.casefold()
            data.extend(_literal_data(name, default))
            code += [f'    mov {"rdx" if is64 else "edx"}, {name}',
                     f'    mov {ptr} [{reg}+{offset}], {"rdx" if is64 else "edx"}']
        elif default:
            code += [f'    mov {ptr} [{reg}+{offset}], {default}']
        # calloc gives a zeroed ownership slot.
    code += ['    mov rsp, rbp' if is64 else '    mov esp, ebp',
             '    pop rbp' if is64 else '    pop ebp', '    ret']
    code += [f'{fini}:']
    if is64:
        code += ['    push rbp', '    mov rbp, rsp', '    sub rsp, 32',
                 '    mov qword ptr [rbp-8], rcx']
    else:
        code += ['    push ebp', '    mov ebp, esp']
    for prop, _owner, offset, typ in own_fields:
        if typ != 'string':
            continue
        skip = fini + '_' + prop.name.casefold() + '_skip'
        if is64:
            code += ['    mov rax, qword ptr [rbp-8]',
                     f'    cmp qword ptr [rax+{offset+word}], 0',
                     f'    je {skip}',
                     f'    mov rcx, qword ptr [rax+{offset}]',
                     '    call __dbase_cls_api_LocalFree', f'{skip}:']
        else:
            code += ['    mov eax, dword ptr [ebp+8]',
                     f'    cmp dword ptr [eax+{offset+word}], 0',
                     f'    je {skip}',
                     f'    push dword ptr [eax+{offset}]',
                     '    call __dbase_cls_api_LocalFree', f'{skip}:']
    if inherit_fields:
        if is64:
            code += ['    mov rcx, qword ptr [rbp-8]',
                     f'    call {method_label(parent, "fields_done")}']
        else:
            code += ['    push dword ptr [ebp+8]',
                     f'    call {method_label(parent, "fields_done")}', '    add esp, 4']
    code += ['    mov rsp, rbp' if is64 else '    mov esp, ebp',
             '    pop rbp' if is64 else '    pop ebp', '    ret']

    # Public members have ABI-safe getters and setters. PRIVATE fields get
    # no public accessor and are checked again at every source call site.
    for prop, _owner, offset, typ in own_fields:
        if prop.visibility != 'public':
            continue
        getter = method_label(cls.name, 'get_' + prop.name)
        setter = method_label(cls.name, 'set_' + prop.name)
        if is64:
            code += [f'{getter}:', f'    mov rax, qword ptr [rcx+{offset}]', '    ret']
        else:
            code += [f'{getter}:', '    mov eax, dword ptr [esp+4]',
                     f'    mov eax, dword ptr [eax+{offset}]', '    ret']
        code += [f'{setter}:']
        if typ == 'string':
            uses_strings = True
            # Copy borrowed input string before replacing an owned field.
            if is64:
                code += ['    push rbp', '    mov rbp, rsp', '    sub rsp, 64',
                         '    mov qword ptr [rbp-8], rcx',
                         '    mov rcx, rdx', '    mov rdx, __dbase_cls_empty',
                         '    mov r8, __dbase_cls_empty',
                         '    call __dbase_cls_concat3',
                         '    mov qword ptr [rbp-16], rax',
                         '    mov rax, qword ptr [rbp-8]',
                         f'    cmp qword ptr [rax+{offset + word}], 0',
                         f'    je {setter}_store',
                         f'    mov rcx, qword ptr [rax+{offset}]',
                         '    call __dbase_cls_api_LocalFree',
                         f'{setter}_store:',
                         '    mov rax, qword ptr [rbp-8]',
                         '    mov rdx, qword ptr [rbp-16]',
                         f'    mov qword ptr [rax+{offset}], rdx',
                         f'    mov qword ptr [rax+{offset + word}], 1',
                         '    mov rsp, rbp', '    pop rbp', '    ret']
            else:
                code += ['    push ebp', '    mov ebp, esp', '    push ebx',
                         '    push __dbase_cls_empty', '    push __dbase_cls_empty',
                         '    push dword ptr [ebp+12]',
                         '    call __dbase_cls_concat3', '    add esp, 12',
                         '    mov ebx, eax',
                         '    mov eax, dword ptr [ebp+8]',
                         f'    cmp dword ptr [eax+{offset + word}], 0',
                         f'    je {setter}_store',
                         f'    push dword ptr [eax+{offset}]',
                         '    call __dbase_cls_api_LocalFree',
                         f'{setter}_store:',
                         '    mov eax, dword ptr [ebp+8]',
                         f'    mov dword ptr [eax+{offset}], ebx',
                         f'    mov dword ptr [eax+{offset + word}], 1',
                         '    pop ebx', '    mov esp, ebp', '    pop ebp', '    ret']
        else:
            if is64:
                code += [f'    mov qword ptr [rcx+{offset}], rdx', '    ret']
            else:
                code += ['    mov eax, dword ptr [esp+4]',
                         '    mov edx, dword ptr [esp+8]',
                         f'    mov dword ptr [eax+{offset}], edx', '    ret']

    ctor = methods.get('__ini__')
    factory = method_label(cls.name, 'create')
    code += [f'global {factory}', f'{factory}:']
    if ctor is not None and ctor.parameters:
        if is64:
            code += ['    push rbp', '    mov rbp, rsp', '    sub rsp, 64',
                     '    mov qword ptr [rbp-8], rcx',
                     f'    mov rcx, {vmt_label(cls.name)}',
                     '    call __dbase_obj_jit_object_instance_new',
                     '    mov qword ptr [rbp-16], rax',
                     '    test rax, rax', f'    jz {factory}_done',
                     '    mov rcx, rax', '    mov rdx, qword ptr [rbp-8]',
                     f'    call {method_label(cls.name, "__ini__")}',
                     f'{factory}_done:', '    mov rax, qword ptr [rbp-16]',
                     '    mov rsp, rbp', '    pop rbp', '    ret']
        else:
            code += ['    push ebp', '    mov ebp, esp', '    push ebx',
                     f'    push {vmt_label(cls.name)}',
                     '    call __dbase_obj_jit_object_instance_new',
                     '    add esp, 4', '    mov ebx, eax',
                     '    test eax, eax', f'    jz {factory}_done',
                     '    push dword ptr [ebp+8]', '    push ebx',
                     f'    call {method_label(cls.name, "__ini__")}',
                     '    add esp, 8',
                     f'{factory}_done:', '    mov eax, ebx',
                     '    pop ebx', '    mov esp, ebp', '    pop ebp', '    ret']
    else:
        if is64:
            code += [f'    mov rcx, {vmt_label(cls.name)}',
                     '    sub rsp, 40', '    call __dbase_obj_jit_object_instance_new',
                     '    add rsp, 40', '    ret']
        else:
            code += [f'    push {vmt_label(cls.name)}',
                     '    call __dbase_obj_jit_object_instance_new',
                     '    add esp, 4', '    ret']

    return imports, code, data, slots, uses_strings


def runtime_string_support(is64):
    imports = [f'import __dbase_cls_api_{name}, "kernel32.dll", "{name}"'
               for name in ('lstrlenA', 'lstrcpyA', 'lstrcatA', 'LocalAlloc', 'LocalFree')]
    return imports, _concat3_assembly(is64), ['__dbase_cls_empty:', '    db 0']
