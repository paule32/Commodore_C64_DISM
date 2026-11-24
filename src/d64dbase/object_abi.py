"""Stage 600: native TObject/VMT bridge for dBASE PE32 and PE64.

The JitVmt layout is defined by runtime/jitObject.h, not by Pascal's
source representation.  Methods use the native C ABI: Self is the first
argument; PE32 is cdecl, PE64 is Microsoft x64.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


METHODS = (
    ('Free', 'procedure', (), ''),
    ('FreeInstance', 'procedure', (), ''),
    ('ClassType', 'function', (), 'PVOID'),
    ('ClassParent', 'function', (), 'PVOID'),
    ('ClassNameAddress', 'function', (), 'PVOID'),
    ('ClassName', 'function', (), 'LPCSTR'),
    ('InstanceSize', 'function', (), 'CINT'),
    ('InheritsFrom', 'function', ('TClass',), 'BOOL'),
)
METHOD_BY_NAME = {name.casefold(): (i, kind, args, result) for i, (name,kind,args,result) in enumerate(METHODS)}
LIFECYCLE = {'__ini__': 'procedure', '__del__': 'procedure'}
# High bit of JitVmt.instance_size marks the shared method table ABI.
# The native runtime masks it off for allocation / InstanceSize().
JIT_VMT_SHARED_METHOD_FLAG = 0x80000000

RUNTIME_EXPORTS = (
    'jit_object_instance_new', 'jit_object_instance_free', 'jit_object_free',
    'jit_object_class_type', 'jit_class_parent', 'jit_class_name',
    'jit_class_instance_size', 'jit_inherits_from_object',
    'jit_get_virtual_object',
)


@dataclass(frozen=True)
class NativeClassProperty:
    name: str
    visibility: str = 'public'
    initial_value: str = ''
    line: int = 0


@dataclass(frozen=True)
class NativeClassMethod:
    kind: str
    name: str
    parameters: tuple[str, ...]
    result_type: str
    line: int
    # (physical_source_line, dBASE_statement), empty = legacy Stage-600 stub.
    body: tuple[tuple[int, str], ...] = ()


# Stage 681: System.Objects.prg supplies the very same methods that the
# native Qt5 DLL already exposes.  Stage 679 treated any method *source* as
# a custom override, which disabled O3 for every program including that unit.
# Match the known default implementations by their complete statement bodies;
# arbitrary user overrides must still use a local table.
_NATIVE_TOBJECT_DEFAULT_BODIES = {
    'free': (
        'if Self <> NULL', 'jit_object_free(Self)', 'endif', 'return',
    ),
    'freeinstance': (
        'if Self <> NULL', 'jit_object_instance_free(Self)', 'endif', 'return',
    ),
    'classtype': ('return jit_object_class_type(Self)',),
    'classparent': ('return jit_class_parent(jit_object_class_type(Self))',),
    'classnameaddress': ('return jit_class_name(jit_object_class_type(Self))',),
    'classname': ('return ClassNameAddress()',),
    'instancesize': ('return jit_class_instance_size(jit_object_class_type(Self))',),
    'inheritsfrom': ('return jit_inherits_from_object(Self, TClass) <> 0',),
}


def _is_native_tobject_default_source(method: NativeClassMethod) -> bool:
    """True only for a known, ABI-equivalent System.Objects method body.

    Match entire statements and keep method signatures validated separately;
    no heuristic based on class or file names is used. A modified Free,
    destructor, or any other virtual method disables native table sharing.
    """
    name = method.name.casefold()
    expected = _NATIVE_TOBJECT_DEFAULT_BODIES.get(name)
    if expected is None or not method.body:
        return False
    canon = lambda line: re.sub(r'\s+', '', line).casefold()
    return tuple(canon(statement) for _, statement in method.body) == tuple(
        canon(statement) for statement in expected)

def validate_methods(class_name: str, methods: tuple[NativeClassMethod, ...]) -> None:
    """Protect against emitting an unimplemented method body as a no-op."""
    names = set()
    for item in methods:
        name = item.name.casefold()
        if name in names:
            raise ValueError(f'Methode mehrfach deklariert: {class_name}.{item.name}')
        names.add(name)
        if class_name.casefold() != 'tobject':
            # Keep Stage-600's deliberate protection against silently dropping
            # unimplemented signature-only methods in derived classes.
            if not item.body and name not in LIFECYCLE:
                raise ValueError('Benutzerdefinierte Methoden anderer Klassen '
                                 'brauchen einen ausfuehrbaren Methodentext: ' +
                                 class_name + '.' + item.name)
            if len(item.parameters) > 1:
                raise ValueError(f'Maximal ein Parameter in {class_name}.{item.name} unterstuetzt.')
            continue
        if name in LIFECYCLE:
            expected_kind = LIFECYCLE[name]
            expected_args, expected_result = (), ''
        elif name in METHOD_BY_NAME:
            _, expected_kind, expected_args, expected_result = METHOD_BY_NAME[name]
        else:
            raise ValueError(f'Nicht implementierte Klassenmethode: {class_name}.{item.name}')
        if item.kind != expected_kind or len(item.parameters) != len(expected_args):
            raise ValueError(f'Ungueltige Signatur fuer {class_name}.{item.name}')
        if item.result_type and item.result_type.casefold() not in {expected_result.casefold(), 'bool' if expected_result == 'BOOL' else expected_result.casefold()}:
            raise ValueError(f'Unpassender Rueckgabetyp fuer {class_name}.{item.name}: {item.result_type}')


def vmt_label(class_name: str) -> str:
    if not re.fullmatch(r'[A-Za-z_]\w*', class_name):
        raise ValueError('Ungueltiger Klassenname')
    return '__dbase_vmt_' + class_name.casefold()


def method_label(class_name: str, method_name: str) -> str:
    return '__dbase_cls_' + class_name.casefold() + '_' + method_name.casefold()


def native_class_definitions(classes):
    """Exclude legacy Qt FORM/TurboVision hierarchies from JitVmt codegen.

    Stage 599 supported metadata for CLASS ... OF FORM/TV_Object; those
    classes must keep their existing Qt/TurboVision ABI, not a new JitVmt.
    """
    all_classes = {cls.name.casefold(): cls for cls in classes}
    legacy = {'form', 'tv_object', 'tv_application'}

    def eligible(cls, visited=None):
        key = cls.name.casefold()
        if key in legacy:
            return False
        visited = set(visited or ())
        if key in visited:
            return False
        visited.add(key)
        parent = str(getattr(cls, 'parent', '') or '').casefold()
        if parent in legacy:
            return False
        if parent in {'', 'tobject'}:
            return True
        return parent in all_classes and eligible(all_classes[parent], visited)

    return tuple(cls for cls in classes if eligible(cls))



class _NativeSourceEmitter:
    """Compile the *actual* dBASE CLASS method source to the JitVmt C ABI.

    This is a deliberately typed native subset: pointer/integer expressions,
    FFI calls, local TObject method calls, IF/ELSE/ENDIF and RETURN. It does
    not route pointer values through the numeric/double-based PRG evaluator.
    """
    def __init__(self, method, *, target, prototypes, filename,
                 optimize_null_comparisons=False):
        self.method = method
        self.optimize_null_comparisons = bool(optimize_null_comparisons)
        self.is64 = target == 'pe64'
        self.reg = 'rax' if self.is64 else 'eax'
        self.other = 'rdx' if self.is64 else 'edx'
        self.ptr = 'qword ptr' if self.is64 else 'dword ptr'
        self.sp = 'rsp' if self.is64 else 'esp'
        self.prototypes = prototypes
        self.filename = filename
        self.lines = []
        self.stack_words = 0
        self.serial = 0
        self.end_label = method_label('TObject', method.name) + '_source_end'
        self.params = {name.casefold(): index + 1 for index, name in enumerate(method.parameters)}
        self.label_prefix = method_label('TObject', method.name)
        self.condition_stack = []

    def error(self, message, line=None):
        from .compiler import DBaseCompilerError
        raise DBaseCompilerError(message, line=line or self.method.line,
                                 column=1, filename=self.filename)

    def label(self, category):
        self.serial += 1
        return f'{self.label_prefix}_{category}_{self.serial}'

    def emit(self, *code):
        self.lines.extend(code)

    def _push(self):
        self.emit('    push ' + self.reg)
        self.stack_words += 1

    def _pop_other(self):
        self.emit('    pop ' + self.other)
        self.stack_words -= 1

    def _expression(self, text, line):
        from .compiler import _tokenize_dbase_statement, _DBaseExpressionParser
        source = '\n' * (line - 1) + text
        tokens = _tokenize_dbase_statement(text, filename=self.filename,
                                          base_offset=line - 1, source=source)
        parser = _DBaseExpressionParser(tokens, filename=self.filename)
        result = parser.parse_expression()
        parser._expect_eof()
        return result

    def _load(self, name, line):
        key = name.casefold()
        if key == 'self':
            index = 0
        elif key in self.params:
            index = self.params[key]
        else:
            self.error(f'Unbekannter Bezeichner in Klassenmethode: {name}', line)
        if self.is64:
            self.emit(f'    mov rax, qword ptr [rbp-{8 * (index + 1)}]')
        else:
            self.emit(f'    mov eax, dword ptr [ebp+{8 + 4 * index}]')

    def _call(self, name, arguments, line):
        key = name.casefold()
        internal = key not in self.prototypes and key in METHOD_BY_NAME
        if internal:
            _, kind, params, _ = METHOD_BY_NAME[key]
            if len(arguments) != len(params):
                self.error(f'{name} erwartet {len(params)} Parameter.', line)
            if kind == 'procedure':
                kind_void = True
            else:
                kind_void = False
            label = method_label('TObject', name)
            args = [None, *arguments]  # implicit Self comes first
        else:
            prototype = self.prototypes.get(key)
            if prototype is None:
                self.error(f'Nicht deklarierte externe Klassenfunktion: {name}', line)
            if len(arguments) != len(prototype.argument_types):
                self.error(f'{name}: {len(prototype.argument_types)} Parameter erwartet.', line)
            from .ffi_types import ffi_type_info
            for arg_type in prototype.argument_types:
                typ = ffi_type_info(arg_type)
                if typ.bits('pe32') > 32 and not self.is64:
                    self.error(f'{name}: 64-Bit-Argument in nativer Klassenmethode noch nicht unterstuetzt.', line)
                if typ.category in ('wide_string', 'ansi_string'):
                    # A pointer to C text is allowed, but this method subset
                    # must not implicitly marshal managed dBASE strings.
                    pass
            kind_void = prototype.return_type in ('CVOID', 'VOID')
            label = prototype.label
            args = list(arguments)
        # Push arguments backwards so nested calls do not destroy preceding
        # results; all source arguments are evaluated from typed AST nodes.
        for argument in reversed(args):
            if argument is None:
                self._load('Self', line)
            else:
                self._emit_expr(argument, line)
            self._push()
        count = len(args)
        if self.is64:
            if count > 4:
                self.error(f'{name}: Mehr als vier native Parameter nicht unterstuetzt.', line)
            # Entry RSP is 16-aligned after the RBP prologue. Nested calls
            # may have left argument words on stack: align the *current* RSP.
            pad = 8 if self.stack_words % 2 else 0
            if pad:
                self.emit('    sub rsp, 8')
            self.emit('    sub rsp, 32')
            for index, register in enumerate(('rcx','rdx','r8','r9')[:count]):
                self.emit(f'    mov {register}, qword ptr [rsp+{32 + pad + index*8}]')
            self.emit(f'    call {label}')
            self.emit(f'    add rsp, {32 + pad + 8 * count}')
        else:
            self.emit(f'    call {label}')
            if internal or self.prototypes[key].calling_convention == 'cdecl':
                if count:
                    self.emit(f'    add esp, {4 * count}')
            else:
                # STDCALL already removed the outgoing args.
                pass
        self.stack_words -= count
        return kind_void

    @staticmethod
    def _is_zero_operand(expr):
        """A literal NULL/0 is side-effect free and has the native pointer width."""
        from .compiler import DBaseIdentifierExpression, DBaseLiteralExpression
        if isinstance(expr, DBaseIdentifierExpression):
            return expr.name.casefold() == 'null'
        if isinstance(expr, DBaseLiteralExpression) and expr.value_type == 'number':
            return expr.value == 0
        return False

    def _zero_comparison(self, expr):
        """Return the nonzero operand and equality operator, if optimizable.

        Only equality/inequality can replace CMP with TEST without changing
        the meaning for pointers and unsigned values. A NULL on either side
        is safe: neither literal has side effects.
        """
        from .compiler import DBaseCondition
        if not self.optimize_null_comparisons or not isinstance(expr, DBaseCondition):
            return None
        if expr.operator not in ('<>', '!=', '#', '=', '=='):
            return None
        left_zero = self._is_zero_operand(expr.left)
        right_zero = self._is_zero_operand(expr.right)
        if left_zero == right_zero:
            return None
        return (expr.right if left_zero else expr.left,
                expr.operator in ('=', '=='))

    def _emit_conditional_jump_false(self, expr, line, false_label):
        """IF x <> NULL / IF x = NULL: branch directly on the zero flag.

        No 0/1 boolean temporary is required for a branch-only expression.
        Other comparisons retain the general result-producing code path.
        """
        zero_test = self._zero_comparison(expr)
        if zero_test is not None:
            other, equals = zero_test
            self._emit_expr(other, line)
            self.emit(f'    test {self.reg}, {self.reg}',
                      f'    {"jnz" if equals else "jz"} {false_label}')
        else:
            self._emit_expr(expr, line)
            self.emit(f'    test {self.reg}, {self.reg}',
                      f'    jz {false_label}')

    def _emit_expr(self, expr, line):
        from .compiler import (DBaseIdentifierExpression, DBaseCallExpression,
                               DBaseLiteralExpression, DBaseCondition,
                               DBaseUnaryExpression)
        if isinstance(expr, DBaseIdentifierExpression):
            if expr.name.casefold() == 'null':
                self.emit(f'    xor {self.reg}, {self.reg}')
            elif expr.name.casefold() in METHOD_BY_NAME and not METHOD_BY_NAME[expr.name.casefold()][2]:
                if self._call(expr.name, (), line):
                    self.error(f'PROCEDURE {expr.name} besitzt keinen Rueckgabewert.', line)
            else:
                self._load(expr.name, line)
        elif isinstance(expr, DBaseLiteralExpression) and expr.value_type == 'number':
            try:
                value = int(expr.value)
                if value != expr.value:
                    raise ValueError
            except (ValueError, TypeError):
                self.error('Native Klassenmethoden erwarten ganzzahlige Literale.', line)
            self.emit(f'    mov {self.reg}, {value}' if value else f'    xor {self.reg}, {self.reg}')
        elif isinstance(expr, DBaseCallExpression):
            if self._call(expr.name, expr.arguments, line):
                self.error(f'PROCEDURE {expr.name} besitzt keinen Rueckgabewert.', line)
        elif isinstance(expr, DBaseCondition):
            zero_test = self._zero_comparison(expr)
            if zero_test is not None:
                # RETURN (Self <> NULL) must produce a canonical 0/1 value;
                # only an IF-only comparison may omit SETcc/MOVZX entirely.
                other, equals = zero_test
                self._emit_expr(other, line)
                self.emit(f'    test {self.reg}, {self.reg}',
                          f'    set{"e" if equals else "ne"} al',
                          '    movzx eax, al')
                return
            self._emit_expr(expr.right, line)
            self._push()
            self._emit_expr(expr.left, line)
            self._pop_other()
            self.emit(f'    cmp {self.reg}, {self.other}')
            mapping = {'<>':'ne','!=':'ne','#':'ne','=':'e','==':'e',
                       '>':'g','<':'l','>=':'ge','<=':'le'}
            op = mapping.get(expr.operator)
            if op is None:
                self.error(f'Unbekannter Vergleich: {expr.operator}', line)
            self.emit(f'    set{op} al', '    movzx eax, al')
        elif isinstance(expr, DBaseUnaryExpression) and expr.operator in ('+', '-'):
            self._emit_expr(expr.operand, line)
            if expr.operator == '-':
                self.emit(f'    neg {self.reg}')
        else:
            self.error('Nicht unterstuetzter nativer Klassenausdruck.', line)

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
                if self.method.kind == 'function':
                    if not expr_text:
                        self.error(f'FUNCTION {self.method.name} muss einen Wert zurueckgeben.', lineno)
                    self._emit_expr(self._expression(expr_text, lineno), lineno)
                elif expr_text:
                    self.error(f'PROCEDURE {self.method.name} darf keinen Wert zurueckgeben.', lineno)
                self.emit(f'    jmp {self.end_label}')
            else:
                expression = self._expression(statement, lineno)
                from .compiler import DBaseCallExpression
                if not isinstance(expression, DBaseCallExpression):
                    self.error('Klassenmember: nur externe Funktionsaufrufe, IF und RETURN erlaubt.', lineno)
                self._call(expression.name, expression.arguments, lineno)
        if self.condition_stack:
            self.error('ENDIF fehlt in Klassenmethode.')
        if self.stack_words:
            self.error('Stackbilanz der Klassenmethode ist nicht ausgeglichen.')
        self.emit(f'{self.end_label}:')
        if self.is64:
            self.emit('    mov rsp, rbp', '    pop rbp', '    ret')
        else:
            self.emit('    mov esp, ebp', '    pop ebp', '    ret')
        return self.lines

def emit_classes(classes, *, target: str, ffi_prototypes=(), filename="<dBase>",
                 optimize_null_comparisons=False):
    """Return (imports, text, data) for class VMTs and native TObject members."""
    classes = native_class_definitions(classes)
    if not classes:
        return [], [], []
    is64 = str(target).lower() == 'pe64'
    ptr = 'dq' if is64 else 'dd'
    ptr_size = 8 if is64 else 4
    present = {item.name.casefold(): item for item in classes}
    if 'tobject' not in present:
        # Needed to give a valid parent VMT to existing CLASS Foo OF TObject.
        from types import SimpleNamespace
        present = {'tobject': SimpleNamespace(name='TObject', parent='', methods=())} | present
    for cls in present.values():
        validate_methods(cls.name, getattr(cls, 'methods', ()))

    from .derived_class_abi import emit_derived_class, runtime_string_support
    custom_codegen = {}
    custom_strings = False
    # User class source methods, typed PROPERTY slots and a class-specific
    # VMT initialize/finalize pair are compiled without altering TObject's ABI.
    derived_text, derived_data = [], []
    derived_imports = []
    for cls in present.values():
        if cls.name.casefold() == 'tobject':
            continue
        # Stage 640: a field-less subclass still has its parent's instance
        # fields and must run inherited field initializers/finalizers.  The
        # old one-pointer instance_size corrupted the heap when an inherited
        # property (e.g. Exception.Message) was accessed.
        from .derived_class_abi import field_layout
        if not (getattr(cls, 'methods', ()) or getattr(cls, 'properties', ())
                or field_layout(cls.name, present, ptr_size)):
            continue
        imports_part, text_part, data_part, fields_part, strings_part = emit_derived_class(
            cls, classes=present, target=target,
            prototypes={p.name.casefold(): p for p in (
                ffi_prototypes.values() if isinstance(ffi_prototypes, dict) else ffi_prototypes)},
            filename=filename, optimize_null_comparisons=optimize_null_comparisons,
        )
        custom_codegen[cls.name.casefold()] = fields_part
        derived_imports.extend(imports_part)
        derived_text.extend(text_part)
        derived_data.extend(data_part)
        custom_strings |= strings_part
    if custom_strings:
        string_imports, string_code, string_data = runtime_string_support(is64)
        derived_imports.extend(string_imports)
        derived_text.extend(string_code)
        derived_data.extend(string_data)

    imports = [f'import __dbase_obj_{name}, "libd64_qt5.dll", "{name}"' for name in RUNTIME_EXPORTS]
    text = ['; Stage 602: dBASE source methods / JitVmt C ABI']
    data = ['; Stage 600: JitVmt headers: parent, name, instance_size, init, finalize, destroy']

    def call(symbol, arg=None, arg2=None):
        if is64:
            ins = []
            if arg is not None and arg != 'rcx':
                ins.append(f'    mov rcx, {arg}')
            if arg2 is not None:
                ins.append(f'    mov rdx, {arg2}')
            ins.extend(['    sub rsp, 40', f'    call __dbase_obj_{symbol}', '    add rsp, 40'])
            return ins
        ins = []
        if arg2 is not None: ins.append(f'    push {arg2}')
        if arg is not None: ins.append(f'    push {arg}')
        ins.append(f'    call __dbase_obj_{symbol}')
        size = 4 * int(arg is not None) + 4 * int(arg2 is not None)
        if size: ins.append(f'    add esp, {size}')
        return ins

    # Classes can now supply actual method bodies. The original Stage-600
    # intrinsic implementations remain only for old signature-only projects.
    tobj = present['tobject']
    declared = {item.name.casefold(): item for item in getattr(tobj, 'methods', ())}
    declared_ffi = {p.name.casefold(): p for p in (
        ffi_prototypes.values() if isinstance(ffi_prototypes, dict) else ffi_prototypes)}
    for name in ('__ini__', '__del__'):
        method = declared.get(name)
        if method and method.body:
            text.extend(_NativeSourceEmitter(method, target=target, prototypes=declared_ffi,
                                            filename=filename,
                                            optimize_null_comparisons=optimize_null_comparisons).compile())
        else:
            text += [f'{method_label("TObject", name)}:', '    ret']
    for name, kind, args, result_type in METHODS:
        key = name.casefold()
        method = declared.get(key)
        if method and method.body:
            text.extend(_NativeSourceEmitter(method, target=target, prototypes=declared_ffi,
                                            filename=filename,
                                            optimize_null_comparisons=optimize_null_comparisons).compile())
            continue
        text.append(f'{method_label("TObject", name)}:')
        if is64:
            self_arg = 'rcx'
            additional = 'rdx'
        else:
            self_arg = 'dword ptr [esp+4]'
            additional = 'dword ptr [esp+8]'
        if key == 'free':
            text.extend(call('jit_object_free', self_arg))
        elif key == 'freeinstance':
            text.extend(call('jit_object_instance_free', self_arg))
        elif key == 'classtype':
            text.extend(call('jit_object_class_type', self_arg))
        elif key in ('classparent', 'classnameaddress', 'classname', 'instancesize'):
            text.extend(call('jit_object_class_type', self_arg))
            next_name = {'classparent': 'jit_class_parent',
                         'classnameaddress': 'jit_class_name',
                         'classname': 'jit_class_name',
                         'instancesize': 'jit_class_instance_size'}[key]
            text.extend(call(next_name, 'rax' if is64 else 'eax'))
        elif key == 'inheritsfrom':
            # PE32: before pushes, [esp+4]=Self, [esp+8]=TClass.
            if is64:
                text.extend(call('jit_inherits_from_object'))  # RCX / RDX already hold parameters
            else:
                text += ['    push dword ptr [esp+8]', '    push dword ptr [esp+8]',
                         '    call __dbase_obj_jit_inherits_from_object', '    add esp, 8']
        text.append('    ret')

    text.extend(derived_text)
    data.extend(derived_data)
    imports.extend(derived_imports)

    # Stage 670: pool identical virtual method tables once per assembly unit.
    # The compact VMT has the five regular header fields followed by a pointer
    # to a shared nine-entry table (destroy + the eight native TObject methods).
    # Keep the old JitVmt C struct ABI: the high bit in instance_size tells the
    # runtime to interpret the last header word as a method-table pointer.
    base_methods = (method_label('TObject', '__del__'),) + tuple(
        method_label('TObject', method_name) for method_name, _, _, _ in METHODS)
    method_tables = {base_methods: '__dbase_class_object'}
    # Stage 681: the shipped System.Objects.prg contains explicit method
    # bodies which are equivalent to the DLL's native default methods. O3 may
    # share those too, but never silently discard a real user override.
    native_tobject_overrides = any(
        member.body and
        (member.name.casefold() == '__del__' or
         (member.name.casefold() in METHOD_BY_NAME and
          not _is_native_tobject_default_source(member)))
        for member in getattr(tobj, 'methods', ())
    )
    o3_marker = ('; Stage 679: TObject custom virtual methods; no DLL fallback'
                 if native_tobject_overrides else
                 '; Stage 679: TObject builtin virtual methods; DLL fallback safe')
    data.extend([o3_marker, '; Stage 670: shared VMT method tables', '__dbase_class_object:'])
    data.extend(f'    {ptr} {name}' for name in base_methods)

    resolved = {}
    def virtual_methods(name, active=frozenset()):
        key = name.casefold()
        if key in resolved:
            return resolved[key]
        if key in active:
            raise ValueError(f'Zyklische dBASE-Klassenhierarchie: {name}')
        cls = present[key]
        parent = str(getattr(cls, 'parent', '') or '').casefold()
        inherited = (virtual_methods(parent, active | {key}) if parent in present
                     else base_methods)
        methods = list(inherited)
        for member in getattr(cls, 'methods', ()):
            index = METHOD_BY_NAME.get(member.name.casefold())
            if (index is not None and member.body
                    and member.kind == index[1]
                    and len(member.parameters) == len(index[2])):
                # An overload with a different signature is *not* a virtual
                # override and must not be installed in an incompatible slot.
                methods[index[0] + 1] = method_label(cls.name, member.name)
            elif (member.name.casefold() == '__del__' and member.body
                  and member.kind == 'procedure' and not member.parameters):
                methods[0] = method_label(cls.name, '__del__')
        resolved[key] = tuple(methods)
        return resolved[key]

    for cls in present.values():
        name = cls.name
        label = vmt_label(name)
        parent = getattr(cls, 'parent', '')
        parent_label = vmt_label(parent) if parent else '0'
        classname_label = label + '_name'
        # Factory is explicit so callers can request a valid JitVmt pointer.
        factory = method_label(name, 'create')
        if name.casefold() not in custom_codegen:
            text.extend([f'global {factory}', f'{factory}:'])
            text.extend(call('jit_object_instance_new', label))
            text.append('    ret')
        slots = custom_codegen.get(name.casefold())
        size = ptr_size * (1 + 2 * len(slots)) if slots is not None else ptr_size
        has_custom = name.casefold() in custom_codegen
        signature = virtual_methods(name)
        shared = method_tables.get(signature)
        if shared is None:
            shared = f'__dbase_class_methods_{len(method_tables)}'
            method_tables[signature] = shared
            data.append(f'{shared}:')
            data.extend(f'    {ptr} {member}' for member in signature)
        if size >= JIT_VMT_SHARED_METHOD_FLAG:
            raise ValueError(f'dBASE-Klasse {name}: Instanzgroesse zu gross fuer kompakte VMT.')
        data += [f'global {label}', f'{label}:',
                 f'    {ptr} {parent_label}', f'    {ptr} {classname_label}',
                 f'    {ptr} 0x{(size | JIT_VMT_SHARED_METHOD_FLAG):08X}',
                 f'    {ptr} {method_label(name, "fields_init") if has_custom else method_label("TObject", "__ini__")}',
                 f'    {ptr} {method_label(name, "fields_done") if has_custom else 0}',
                 f'    {ptr} {shared}']
        encoded = ', '.join(map(str, name.encode('cp1252'))) or '0'
        data += [f'{classname_label}:', f'    db {encoded}, 0']
    # Only keep the two structural imports (allocation / VMT dispatch) and
    # imports referenced by *legacy* hard-coded members. Real dBASE methods
    # call their own FFI declarations (__dbase_ffi_*), not __dbase_obj_*.
    structural = {'jit_object_instance_new', 'jit_get_virtual_object'}
    used = set(structural)
    for name in RUNTIME_EXPORTS:
        if any(line.strip() == f'call __dbase_obj_{name}' for line in text):
            used.add(name)
    imports = [f'import __dbase_obj_{name}, "libd64_qt5.dll", "{name}"'
               for name in RUNTIME_EXPORTS if name in used] + derived_imports
    return imports, text, data


def inject_class_assembly(assembly: str, classes, *, target: str, ffi_prototypes=(), filename="<dBase>") -> str:
    imports, code, data = emit_classes(classes, target=target, ffi_prototypes=ffi_prototypes, filename=filename)
    if not imports:
        return assembly
    if 'section .text\n' not in assembly or 'section .data\n' not in assembly or 'section .bss\n' not in assembly:
        raise ValueError('dBASE-Assemblerabschnitte fehlen fuer VMT-Ausgabe')
    if not re.search(r'^import\s+__dbase_ffi_lstrlenA\s*,', assembly, re.M | re.I):
        imports.append('import __dbase_ffi_lstrlenA, "kernel32.dll", "lstrlenA"')
    assembly = assembly.replace('section .text\n', '\n'.join(imports) + '\nsection .text\n', 1)
    # Append code at the end of .text, leaving _start and existing routines unchanged.
    assembly = assembly.replace('section .data\n', '\n'.join(code) + '\n\nsection .data\n' + '\n'.join(data) + '\n', 1)
    return assembly
