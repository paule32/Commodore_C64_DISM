"""Stage 641: managed dBL exceptions in JitVmt CLASS method bodies.

The method backend shares the Stage-639/640 exception status and factory with
PRG routines.  A native Windows SEH frame is intentionally NOT synthesized.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .derived_class_abi import DerivedMethodEmitter
from .object_abi import method_label


@dataclass(frozen=True)
class _Catch:
    name: str
    class_name: str
    body: tuple
    line: int
    slot: int


@dataclass(frozen=True)
class _Try:
    body: tuple
    catches: tuple[_Catch, ...]
    cleanup: tuple
    line: int


def _word(line):
    return str(line).strip().split(None, 1)[0].casefold() if str(line).strip() else ''


def parse_method_exceptions(method, error):
    """Keep physical line numbers; require a correctly nested ENDTRY."""
    records = tuple(method.body)
    catch_serial = 0

    def sequence(i, stops=frozenset()):
        nonlocal catch_serial
        output = []
        while i < len(records):
            number, raw = records[i]
            key = _word(raw)
            if key in stops:
                return tuple(output), i
            if key in {'endtry', 'catch', 'finally'}:
                error(f'Unerwartetes {key.upper()} in Klassenmethode.', number)
            if key == 'try':
                if str(raw).strip().casefold() != 'try':
                    error('TRY darf keine Argumente enthalten.', number)
                inside, i = sequence(i + 1, frozenset({'catch', 'finally', 'endtry'}))
                handlers = []
                while i < len(records) and _word(records[i][1]) == 'catch':
                    at, line = records[i]
                    m = re.fullmatch(r'(?i)catch\s*\(\s*([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*\)', line.strip())
                    if m is None:
                        error('CATCH erwartet (ExceptionKlasse variable).', at)
                    body, i = sequence(i + 1, frozenset({'catch', 'finally', 'endtry'}))
                    handlers.append(_Catch(m.group(2), m.group(1), body, at, catch_serial))
                    catch_serial += 1
                cleanup = ()
                seen_finally = i < len(records) and _word(records[i][1]) == 'finally'
                if seen_finally:
                    at, line = records[i]
                    if line.strip().casefold() != 'finally':
                        error('FINALLY darf keine Argumente enthalten.', at)
                    cleanup, i = sequence(i + 1, frozenset({'endtry', 'catch', 'finally'}))
                if i >= len(records) or _word(records[i][1]) != 'endtry':
                    error('TRY erwartet ENDTRY.', number)
                at, line = records[i]
                if line.strip().casefold() != 'endtry':
                    error('ENDTRY darf keine Argumente enthalten.', at)
                if not handlers and not seen_finally:
                    error('TRY benoetigt CATCH oder FINALLY.', number)
                output.append(_Try(inside, tuple(handlers), tuple(cleanup), number))
                i += 1
            else:
                output.append((number, raw))
                i += 1
        return tuple(output), i

    nodes, end = sequence(0)
    assert end == len(records)
    return nodes, catch_serial


class NativeExceptionMethodEmitter(DerivedMethodEmitter):
    """Emit lexical TRY/CATCH/FINALLY in *every* native CLASS method.

    Catch bindings and the pending return value are frame-local, not BSS
    globals.  The existing Stage-640 pending-exception ABI is shared with PRG.
    """
    def __init__(self, cls, method, *, exception_types, **kwargs):
        super().__init__(cls, method, **kwargs)
        self.exception_types = exception_types
        self.nodes, catch_count = parse_method_exceptions(method, self.error)
        self._validate_catch_types(self.nodes)
        self._catch_count = catch_count
        self._catch_bindings = []
        self._exception_targets = []
        self._finalizers = []
        self._result_saved = False
        word = 8 if self.is64 else 4
        self._ret_offset = 24 if self.is64 else 4
        self._catch_base = 40 if self.is64 else 12
        self._catch_stride = 7 * word
        min_frame = self._catch_base + catch_count * self._catch_stride + 16
        # Keep the Windows x64 stack 16-aligned after RBP prologue.
        self._frame_size = ((min_frame + 15) // 16) * 16 if self.is64 else min_frame

    def _is_ancestor(self, ancestor: str, descendant: str) -> bool:
        current = descendant.casefold()
        visited = set()
        while current in self.exception_types and current not in visited:
            if current == ancestor.casefold():
                return True
            visited.add(current)
            current = self.exception_types[current][1].casefold()
        return False

    def _validate_catch_types(self, sequence):
        for node in sequence:
            if not isinstance(node, _Try):
                continue
            self._validate_catch_types(node.body)
            seen = []
            for clause in node.catches:
                key = clause.class_name.casefold()
                if key not in self.exception_types:
                    self.error(f'CATCH ({clause.class_name}) ist keine Exception-Unterklasse.', clause.line)
                if any(self._is_ancestor(previous, key) for previous in seen):
                    self.error(f'CATCH {clause.class_name} ist bereits durch einen vorherigen Handler abgedeckt.', clause.line)
                seen.append(key)
                self._validate_catch_types(clause.body)
            self._validate_catch_types(node.cleanup)

    def _slot(self, clause, item):
        return f'[rbp-{self._catch_base + clause.slot * self._catch_stride + item * (8 if self.is64 else 4)}]' if self.is64 else f'[ebp-{self._catch_base + clause.slot * self._catch_stride + item * 4}]'

    def _bound(self, name):
        for mapping in reversed(self._catch_bindings):
            if name.casefold() in mapping:
                return mapping[name.casefold()]
        return None

    def _load(self, name, line):
        # A catch variable denotes the *native* TObject instance.  Its text
        # fields are views, never a clone of the thrown object.
        pieces = name.casefold().split('.')
        if len(pieces) == 2 and pieces[0] in {'self', 'this'}:
            return super()._load(pieces[1], line)
        if len(pieces) == 2:
            clause = self._bound(pieces[0])
            if clause is not None:
                field = {'message': 2, 'error': 2, 'classname': 4, 'code': 6}.get(pieces[1])
                if field is None:
                    self.error('Unbekannte Exception-Property: ' + name, line)
                self.emit(f'    mov {self.reg}, {self.ptr} {self._slot(clause, field)}')
                return
        clause = self._bound(name)
        if clause is not None:
            self.emit(f'    mov {self.reg}, {self.ptr} {self._slot(clause, 1)}')
            return
        return super()._load(name, line)

    def _exception_destination(self):
        return self._exception_targets[-1] if self._exception_targets else self.end_label

    def _check_exception(self):
        good = self.label('exception_clear')
        self.emit('    cmp dword ptr [__dbase_exception_id], 0', f'    je {good}',
                  f'    jmp {self._exception_destination()}', f'{good}:')

    def _call_self_method(self, owner, method, args, line):
        # Like _NativeSourceEmitter._call, but methods can belong to the
        # declaring CLASS or a superclass, not just TObject/FFI.
        if len(args) != len(method.parameters):
            self.error(f'{method.name} erwartet {len(method.parameters)} Parameter.', line)
        values = [None, *args]
        for value in reversed(values):
            if value is None:
                super()._load('Self', line)
            else:
                self._emit_expr(value, line)
            self._push()
        count = len(values)
        if self.is64:
            if count > 4:
                self.error('Mehr als drei Methodenparameter sind nicht unterstuetzt.', line)
            pad = 8 if self.stack_words % 2 else 0
            if pad:
                self.emit('    sub rsp, 8')
            self.emit('    sub rsp, 32')
            for i, register in enumerate(('rcx', 'rdx', 'r8', 'r9')[:count]):
                self.emit(f'    mov {register}, qword ptr [rsp+{32 + pad + 8*i}]')
            self.emit(f'    call {method_label(owner, method.name)}',
                      f'    add rsp, {32 + pad + 8*count}')
        else:
            self.emit(f'    call {method_label(owner, method.name)}',
                      f'    add esp, {4*count}')
        self.stack_words -= count
        self._check_exception()
        return method.kind == 'procedure'

    def _call(self, name, arguments, line):
        key = name.casefold()
        if key.startswith('self.') or key.startswith('this.'):
            key = key.split('.', 1)[1]
        # Use the nearest (possibly inherited) source method.
        current = self.cls
        visited = set()
        while current is not None and current.name.casefold() not in visited:
            visited.add(current.name.casefold())
            candidate = next((m for m in getattr(current, 'methods', ())
                              if m.name.casefold() == key), None)
            if candidate is not None:
                return self._call_self_method(current.name, candidate, arguments, line)
            current = self.classes.get(str(current.parent or '').casefold())
        result = super()._call(name, arguments, line)
        self._check_exception()
        return result

    def _emit_super_init(self, argument, line):
        super()._emit_super_init(argument, line)
        self._check_exception()

    def _throw(self, text, line):
        value = text.strip()
        new = re.fullmatch(r'(?is)new\s+([A-Za-z_]\w*)\s*\((.*)\)', value)
        if new or (value and not self._bound(value)):
            name = new.group(1) if new else 'Exception'
            key = name.casefold()
            if key not in self.exception_types:
                self.error(f'{name} ist keine bekannte Exception-Klasse.', line)
            raw_msg = new.group(2).strip() if new else value
            if raw_msg:
                expression = self._expression(raw_msg, line)
                from .compiler import DBaseLiteralExpression, DBaseIdentifierExpression
                if isinstance(expression, DBaseLiteralExpression) and expression.value_type == 'number':
                    self.error('THROW erwartet eine Textmeldung.', line)
                self._emit_expr(expression, line)
            else:
                self.emit('    mov ' + self.reg + ', __dbase_cls_empty')
            if self.is64:
                self.emit('    mov rcx, rax', '    sub rsp, 32',
                          f'    call __dbase_raise_{key}', '    add rsp, 32')
            else:
                self.emit('    push eax', f'    call __dbase_raise_{key}', '    add esp, 4')
        else:
            clause = self._bound(value) if value else (
                list(self._catch_bindings[-1].values())[-1] if self._catch_bindings else None)
            if clause is None:
                self.error('THROW ohne Wert erwartet eine aktive CATCH-Variable.', line)
            # Restore the *same* instance and the original derived type.
            for src_idx, target, kind in ((0, '__dbase_exception_id', 'dword'),
                                          (1, '__dbase_exception_object_ptr', 'ptr'),
                                          (2, '__dbase_exception_message_ptr', 'ptr'),
                                          (3, '__dbase_exception_message_len', 'dword'),
                                          (4, '__dbase_exception_class_ptr', 'ptr'),
                                          (5, '__dbase_exception_class_len', 'dword'),
                                          (6, '__dbase_exception_code', 'dword')):
                reg = 'eax' if kind == 'dword' else self.reg
                self.emit(f'    mov {reg}, {"dword ptr" if kind == "dword" else self.ptr} {self._slot(clause, src_idx)}')
                self.emit(f'    mov {"dword ptr" if kind == "dword" else self.ptr} [{target}], {reg}')
        self.emit(f'    jmp {self._exception_destination()}')

    def _save_catch(self, clause):
        for idx, global_name, kind in ((0, '__dbase_exception_id', 'dword'),
                                       (1, '__dbase_exception_object_ptr', 'ptr'),
                                       (2, '__dbase_exception_message_ptr', 'ptr'),
                                       (3, '__dbase_exception_message_len', 'dword'),
                                       (4, '__dbase_exception_class_ptr', 'ptr'),
                                       (5, '__dbase_exception_class_len', 'dword'),
                                          (6, '__dbase_exception_code', 'dword')):
            reg = 'eax' if kind == 'dword' else self.reg
            self.emit(f'    mov {reg}, {"dword ptr" if kind == "dword" else self.ptr} [{global_name}]')
            self.emit(f'    mov {"dword ptr" if kind == "dword" else self.ptr} {self._slot(clause, idx)}, {reg}')
        self.emit('    mov dword ptr [__dbase_exception_id], 0',
                  f'    mov {self.ptr} [__dbase_exception_object_ptr], 0')

    def _compile_try(self, node):
        outer_targets = tuple(self._exception_targets)
        outer_finalizers = tuple(self._finalizers)
        dispatch = self.label('catch_dispatch')
        done = self.label('try_done')
        cleanup = self.label('try_finally')
        self._exception_targets = list(outer_targets) + [dispatch]
        if node.cleanup:
            self._finalizers = list(outer_finalizers) + [node.cleanup]
        try:
            self._compile_sequence(node.body)
        finally:
            self._exception_targets = list(outer_targets)
            self._finalizers = list(outer_finalizers)
        self.emit(f'    jmp {cleanup}', f'{dispatch}:')
        for clause in node.catches:
            key = clause.class_name.casefold()
            if key not in self.exception_types:
                self.error(f'{clause.class_name} ist keine Exception-Unterklasse.', clause.line)
            matches = []
            for candidate, (_name, parent, value_id) in self.exception_types.items():
                visited = set()
                current = candidate
                while current in self.exception_types and current not in visited:
                    visited.add(current)
                    if current == key:
                        matches.append(value_id)
                        break
                    current = self.exception_types[current][1].casefold()
            handler = self.label('catch_match')
            next_clause = self.label('catch_next')
            for value_id in matches:
                self.emit(f'    cmp dword ptr [__dbase_exception_id], {value_id}',
                          f'    je {handler}')
            self.emit(f'    jmp {next_clause}', f'{handler}:')
            self._save_catch(clause)
            self._catch_bindings.append({clause.name.casefold(): clause})
            self._exception_targets = list(outer_targets) + [cleanup]
            if node.cleanup:
                self._finalizers = list(outer_finalizers) + [node.cleanup]
            try:
                self._compile_sequence(clause.body)
            finally:
                self._exception_targets = list(outer_targets)
                self._finalizers = list(outer_finalizers)
                self._catch_bindings.pop()
            self.emit(f'    jmp {cleanup}', f'{next_clause}:')
        self.emit(f'{cleanup}:')
        # Exceptions thrown by FINALLY itself must bypass the same TRY block.
        self._compile_sequence(node.cleanup)
        self._check_exception()
        self.emit(f'{done}:')

    def _return(self, text, line):
        if text:
            if self.method.kind != 'function' and self.method.name.casefold() != '__ini__':
                self.error('PROCEDURE darf keinen Wert zurueckgeben.', line)
            self._emit_expr(self._expression(text, line), line)
        elif self.method.kind == 'function':
            self.error('FUNCTION erwartet RETURN <expr>.', line)
        # Preserve the function's value while invoking any FINALLY code.
        if text and self._finalizers:
            self.emit(f'    mov {self.ptr} [rbp-{self._ret_offset}], {self.reg}' if self.is64 else
                      f'    mov {self.ptr} [ebp-{self._ret_offset}], {self.reg}')
        saved_finalizers = list(self._finalizers)
        saved_targets = list(self._exception_targets)
        try:
            for depth in range(len(saved_finalizers) - 1, -1, -1):
                # A THROW (or a failing method call) inside an inner FINALLY
                # must still run all remaining *outer* FINALLY blocks.
                # Route to the next finalizer, not directly to the epilogue.
                advance = self.label('return_finalizer_advance')
                self._finalizers = saved_finalizers[:depth]
                self._exception_targets = [advance]
                self._compile_sequence(saved_finalizers[depth])
                self.emit(f'{advance}:')
        finally:
            self._finalizers = saved_finalizers
            self._exception_targets = saved_targets
        if saved_finalizers:
            # An exception raised by a FINALLY overrides the pending RETURN.
            pending_clear = self.label('return_pending_clear')
            self.emit('    cmp dword ptr [__dbase_exception_id], 0',
                      f'    je {pending_clear}', f'    jmp {self.end_label}',
                      f'{pending_clear}:')
        if text and saved_finalizers:
            self.emit(f'    mov {self.reg}, {self.ptr} [rbp-{self._ret_offset}]' if self.is64 else
                      f'    mov {self.reg}, {self.ptr} [ebp-{self._ret_offset}]')
        self.emit(f'    jmp {self.end_label}')

    def _emit_text(self, statement, line):
        expression = statement.strip()
        if expression:
            item = self._expression(expression, line)
            from .compiler import DBaseLiteralExpression, DBaseIdentifierExpression
            if isinstance(item, DBaseLiteralExpression) and item.value_type == 'number':
                self.error('Native CLASS-Ausgabe erwartet einen String, keine Zahl.', line)
            if isinstance(item, DBaseIdentifierExpression):
                key = item.name.casefold().split('.')[-1]
                field = self.fields.get(key)
                if (field is not None and field[3] == 'number' and
                    ('.' not in item.name or item.name.casefold().startswith(('self.','this.')))):
                    self.error('Native CLASS-Ausgabe erwartet einen String-Pointer.', line)
            self._emit_expr(item, line)
        else:
            label = self.label_prefix + f'_string_{len(self.literal_data)}'
            from .derived_class_abi import _literal_data
            self.literal_data.extend(_literal_data(label, ''))
            self.emit('    mov ' + self.reg + ', ' + label)
        # The C string pointer must survive lstrlenA and any Qt callback.
        if self.is64:
            self.emit('    sub rsp, 48', '    mov qword ptr [rsp+40], rax',
                      '    mov rcx, rax', '    call __dbase_exc_strlenA',
                      '    mov edx, eax', '    mov rcx, qword ptr [rsp+40]',
                      '    call DBaseQtAppendDebug', '    add rsp, 48')
        else:
            self.emit('    push eax', '    push eax', '    call __dbase_exc_strlenA',
                      '    add esp, 4', '    pop ecx', '    push eax', '    push ecx',
                      '    call DBaseQtAppendDebug', '    add esp, 8')

    def _compile_line(self, number, raw):
        statement = str(raw).strip()
        if not statement:
            return
        words = statement.split(None, 1)
        op = words[0].casefold()
        text = words[1].strip() if len(words) > 1 else ''
        if op == 'if':
            if not text:
                self.error('IF benoetigt eine Bedingung.', number)
            false_label = self.label('else')
            end_label = self.label('endif')
            self._emit_conditional_jump_false(self._expression(text, number), number, false_label)
            self.condition_stack.append((false_label, end_label, False))
        elif op == 'else':
            if text or not self.condition_stack:
                self.error('ELSE ohne IF.', number)
            false_label, end_label, done = self.condition_stack.pop()
            if done:
                self.error('Doppeltes ELSE.', number)
            self.emit(f'    jmp {end_label}', f'{false_label}:')
            self.condition_stack.append((false_label, end_label, True))
        elif op == 'endif':
            if text or not self.condition_stack:
                self.error('ENDIF ohne IF.', number)
            false_label, end_label, done = self.condition_stack.pop()
            self.emit(f'{end_label if done else false_label}:')
        elif op == 'throw':
            self._throw(text, number)
        elif op == 'return':
            self._return(text, number)
        elif statement.startswith('??') or statement.startswith('?'):
            newline = not statement.startswith('??')
            payload = statement[2:].strip() if not newline else statement[1:].strip()
            self._emit_text(payload, number)
            if newline:
                self._emit_text('"\\r\\n"', number)
        elif re.fullmatch(r'(?i)set\s+background\s+to\s+.+', statement):
            self._emit_set_background(re.sub(r'(?i)^set\s+background\s+to\s+', '', statement), number)
        elif re.fullmatch(r'(?i)super\s*\(\s*\)\s*\.\s*__ini__\s*\((.*)\)\s*', statement):
            match = re.fullmatch(r'(?i)super\s*\(\s*\)\s*\.\s*__ini__\s*\((.*)\)\s*', statement)
            self._emit_super_init(match.group(1), number)
        elif re.fullmatch(r'(?i)([A-Za-z_]\w*)\.(message|error)\s*=\s*(.+)', statement):
            match = re.fullmatch(r'(?i)([A-Za-z_]\w*)\.(message|error)\s*=\s*(.+)', statement)
            clause = self._bound(match.group(1))
            if clause is None:
                self.error('Exception-Zuweisung nur an sichtbare CATCH-Variable.', number)
            expression = self._expression(match.group(3), number)
            self._emit_expr(expression, number)
            # Call the inherited native setter, then refresh the bound view.
            if self.is64:
                self.emit('    mov rdx, rax', f'    mov rcx, qword ptr {self._slot(clause, 1)}',
                          '    sub rsp, 32', '    call __dbase_cls_exception_set_message',
                          f'    mov rcx, qword ptr {self._slot(clause, 1)}',
                          '    call __dbase_cls_exception_get_message', '    add rsp, 32',
                          f'    mov qword ptr {self._slot(clause, 2)}, rax')
            else:
                self.emit('    push eax', f'    push dword ptr {self._slot(clause, 1)}',
                          '    call __dbase_cls_exception_set_message', '    add esp, 8',
                          f'    push dword ptr {self._slot(clause, 1)}',
                          '    call __dbase_cls_exception_get_message', '    add esp, 4',
                          f'    mov dword ptr {self._slot(clause, 2)}, eax')
            # The derived text length must also be refreshed after mutation.
            if self.is64:
                self.emit('    mov rcx, rax', '    sub rsp, 32',
                          '    call __dbase_exc_strlenA', '    add rsp, 32',
                          f'    mov dword ptr {self._slot(clause, 3)}, eax')
            else:
                self.emit('    push eax', '    call __dbase_exc_strlenA',
                          '    add esp, 4', f'    mov dword ptr {self._slot(clause, 3)}, eax')
        elif re.fullmatch(r'(?i)(?:self\.|this\.)?[A-Za-z_]\w*\s*=\s*.+', statement):
            name, rhs = statement.split('=', 1)
            name = name.strip()
            if name.casefold().startswith(('self.', 'this.')):
                name = name.split('.', 1)[1]
            self._emit_assignment(name, rhs.strip(), number)
        else:
            expression = self._expression(statement, number)
            from .compiler import DBaseCallExpression
            if not isinstance(expression, DBaseCallExpression):
                self.error('Klassenmember: Aufruf, Zuweisung, RETURN oder TRY erwartet.', number)
            self._call(expression.name, expression.arguments, number)

    def _compile_sequence(self, sequence):
        depth = len(self.condition_stack)
        for item in sequence:
            if isinstance(item, _Try):
                self._compile_try(item)
            else:
                self._compile_line(*item)
        if len(self.condition_stack) != depth:
            self.error('ENDIF fehlt oder IF reicht ueber eine TRY-Grenze hinweg.')

    def compile(self):
        self.emit(f'{self.label_prefix}:')
        if self.is64:
            self.emit('    push rbp', '    mov rbp, rsp', f'    sub rsp, {self._frame_size}',
                      '    mov qword ptr [rbp-8], rcx',
                      '    mov qword ptr [rbp-16], rdx')
        else:
            self.emit('    push ebp', '    mov ebp, esp', f'    sub esp, {self._frame_size}')
        self._compile_sequence(self.nodes)
        if self.stack_words:
            self.error('Stackbilanz der Klassenmethode ist nicht ausgeglichen.')
        self.emit(f'{self.end_label}:',
                  '    mov rsp, rbp' if self.is64 else '    mov esp, ebp',
                  '    pop rbp' if self.is64 else '    pop ebp', '    ret')
        return self.lines, self.literal_data, self.concat_needed
