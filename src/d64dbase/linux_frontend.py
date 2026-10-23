"""Linux dBASE ELF frontend: Stage 487 console subset, Stage 488 Qt5 .so GUI.

Linux GUI targets emit native ELF32/ELF64 programs that call the exported
DBaseQtRunFormJson C ABI from a dynamically loaded libd64_qt5.so. No embedded
Python/PyQt process is used. The WFM expression/event subset is bounded and
unsupported source is rejected explicitly.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterable

from .compiler import DBaseCompileResult, DBaseCompilerError, _preprocess_dbase_macros, strip_dbase_comments
from .ffi import extract_ffi_prototypes
from .ffi_types import ffi_type_info
from .wfm import wfm_executable_preamble
from .wfm import parse_dbase_wfm, _wfm_value


class LinuxDBaseError(ValueError):
    def __init__(self, message, *, line=0, filename='<dBASE>'):
        self.message = str(message)
        self.line = int(line)
        self.filename = str(filename)
        super().__init__(f'{filename}:{line}: {message}' if line else f'{filename}: {message}')


def _literal_bytes(label: str, payload: bytes) -> str:
    # The source encoder accepts plain numeric byte declarations on all targets.
    chunks = [payload[i:i + 24] for i in range(0, len(payload), 24)] or [b'']
    return label + ':\n' + '\n'.join('    db ' + ', '.join(map(str, chunk)) for chunk in chunks if chunk)


def _linux_start(bits: int) -> tuple[str, str]:
    if bits == 64:
        return ('    mov rax, 60\n    mov rdi, 0\n    syscall',
                '    mov rax, 1\n    mov rdi, 1\n    mov rsi, {label}\n    mov rdx, {length}\n    syscall')
    return ('    mov eax, 1\n    xor ebx, ebx\n    int 0x80',
            '    mov eax, 4\n    mov ebx, 1\n    mov ecx, {label}\n    mov edx, {length}\n    int 0x80')


_UNDEFINED = object()


def _type_letter(value) -> str:
    if value is _UNDEFINED:
        return 'U'
    if isinstance(value, bool):
        return 'L'
    if isinstance(value, (int, float)):
        return 'N'
    if isinstance(value, str):
        return 'C'
    return 'U'


def _safe_constant(expression: str, variables: dict, *, line: int, filename: str):
    """Limited static dBASE expression evaluator. Never Python eval().

    TYPE("name") checks the variable by name; VARTYPE(value) checks a value.
    For undefined variables TYPE/VARTYPE return U as in the Windows backend.
    This Stage only evaluates the known constant subset, not arbitrary calls.
    """
    text = str(expression).strip()
    if re.fullmatch(r'(?is)\.t\.', text): return True
    if re.fullmatch(r'(?is)\.f\.', text): return False
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        return text[1:-1].replace(text[0] * 2, text[0])
    try:
        node = ast.parse(text, mode='eval').body
    except (SyntaxError, ValueError):
        raise LinuxDBaseError(f'Noch nicht unterstuetzter Linux-dBASE-Ausdruck: {text}', line=line, filename=filename) from None
    def walk(tree):
        if isinstance(tree, ast.Constant) and type(tree.value) in (int, float, str, bool):
            return tree.value
        if isinstance(tree, ast.Name):
            key = tree.id.casefold()
            if key in variables and variables[key] is not _UNDEFINED:
                return variables[key]
        if isinstance(tree, ast.Call) and isinstance(tree.func, ast.Name) and not tree.keywords:
            func = tree.func.id.casefold()
            if func in {'type', 'vartype'}:
                if len(tree.args) != 1:
                    raise LinuxDBaseError(f'{func.upper()}(...) erwartet genau einen Parameter.', line=line, filename=filename)
                arg = tree.args[0]
                if func == 'type':
                    if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str) or not re.fullmatch(r'[A-Za-z_]\w*', arg.value.strip()):
                        raise LinuxDBaseError('TYPE(...) erwartet einen Variablennamen als String, z.B. TYPE("xyz").', line=line, filename=filename)
                    return _type_letter(variables.get(arg.value.strip().casefold(), _UNDEFINED))
                if isinstance(arg, ast.Name) and arg.id.casefold() not in variables:
                    return 'U'
                if isinstance(arg, ast.Name) and variables.get(arg.id.casefold()) is _UNDEFINED:
                    return 'U'
                return _type_letter(walk(arg))
        if isinstance(tree, ast.UnaryOp):
            if isinstance(tree.op, ast.Not):
                val = walk(tree.operand)
                if type(val) == bool: return not val
            if isinstance(tree.op, (ast.UAdd, ast.USub)):
                val = walk(tree.operand)
                if type(val) in (int, float):
                    return val if isinstance(tree.op, ast.UAdd) else -val
        if isinstance(tree, ast.BinOp):
            left, right = walk(tree.left), walk(tree.right)
            if isinstance(tree.op, ast.Add) and type(left) == type(right) == str:
                return left + right
            if type(left) in (int, float) and type(right) in (int, float):
                if isinstance(tree.op, ast.Add): return left + right
                if isinstance(tree.op, ast.Sub): return left - right
                if isinstance(tree.op, ast.Mult): return left * right
                if isinstance(tree.op, ast.Div) and right != 0: return left / right
        if isinstance(tree, ast.Compare) and len(tree.ops) == len(tree.comparators):
            previous = walk(tree.left)
            for operator, comparator in zip(tree.ops, tree.comparators):
                current = walk(comparator)
                if not (type(previous) == type(current) or
                        (type(previous) in (int, float) and type(current) in (int, float))):
                    raise LinuxDBaseError(f'Unvertraegliche dBASE-Vergleichstypen: {text}', line=line, filename=filename)
                if isinstance(operator, ast.Eq): result = previous == current
                elif isinstance(operator, ast.NotEq): result = previous != current
                elif isinstance(operator, ast.Lt): result = previous < current
                elif isinstance(operator, ast.LtE): result = previous <= current
                elif isinstance(operator, ast.Gt): result = previous > current
                elif isinstance(operator, ast.GtE): result = previous >= current
                else: break
                if not result: return False
                previous = current
            else:
                return True
        if isinstance(tree, ast.BoolOp) and isinstance(tree.op, (ast.And, ast.Or)):
            values = [walk(part) for part in tree.values]
            if all(type(value) == bool for value in values):
                return all(values) if isinstance(tree.op, ast.And) else any(values)
        raise LinuxDBaseError(f'Nicht unterstuetzter dynamischer Linux-Ausdruck: {text}', line=line, filename=filename)
    return walk(node)


# Only known Win32 APIs with an explicit native Qt5 implementation may run
# under Linux. Type aliases alone must never cause shell32.dll to be imported.
_LINUX_QT_COMPAT = {
    ('shell32.dll', 'shellexecutea'): ('shell_execute', 'ansi'),
    ('shell32.so', 'shellexecutea'): ('shell_execute', 'ansi'),
    ('shell32.dll', 'shellexecutew'): ('shell_execute', 'wide'),
    ('shell32.so', 'shellexecutew'): ('shell_execute', 'wide'),
    ('user32.dll', 'messageboxa'): ('message_box', 'ansi'),
    ('user32.so', 'messageboxa'): ('message_box', 'ansi'),
    ('libd64_qt5.so', 'messageboxa'): ('message_box', 'ansi'),
    ('shell32.so', 'messageboxa'): ('message_box', 'ansi'),
    ('user32.dll', 'messageboxw'): ('message_box', 'wide'),
    ('user32.so', 'messageboxw'): ('message_box', 'wide'),
    ('libd64_qt5.so', 'messageboxw'): ('message_box', 'wide'),
    ('shell32.so', 'messageboxw'): ('message_box', 'wide'),
}


def _linux_ffi_signature(proto, *, filename):
    kind, encoding = _LINUX_QT_COMPAT[(proto.dll.casefold(), proto.entry.casefold())]
    arguments = tuple(ffi_type_info(name) for name in proto.argument_types)
    result = ffi_type_info(proto.return_type)
    if kind == 'shell_execute':
        if (len(arguments) != 6 or arguments[0].name != 'HWND'
                or not all(item.category == ('ansi_string' if encoding == 'ansi' else 'wide_string') for item in arguments[1:5])
                or arguments[5].category != 'integer' or result.category not in ('pointer', 'integer')):
            raise LinuxDBaseError(
                f'{proto.name}: ungueltige ShellExecute-Prototypen-Signatur fuer Linux-Qt5.',
                line=proto.line, filename=filename)
    elif kind == 'message_box':
        if (len(arguments) != 4 or arguments[0].name != 'HWND'
                or not all(item.category == ('ansi_string' if encoding == 'ansi' else 'wide_string') for item in arguments[1:3])
                or arguments[3].category != 'integer' or result.category != 'integer'):
            raise LinuxDBaseError(
                f'{proto.name}: ungueltige MessageBox-Prototypen-Signatur fuer Linux-Qt5.',
                line=proto.line, filename=filename)
    return kind


def _linux_source_without_unused_ffi(source: str, *, filename: str):
    """Accept Win32 type aliases on Linux, but map *only* known Qt replacements.

    The existing extern/header grammar is retained to avoid breaking shared
    Windows/Linux dBASE sources. All actual unimplemented DLL calls fail with
    source line diagnostics, while unused declarations remain harmless.
    """
    try:
        code, prototypes = extract_ffi_prototypes(source, filename=filename, allow_so=True)
    except ValueError as exc:
        raise LinuxDBaseError("Ungueltige Windows-DLL-/Linux-SO-Deklaration: " + str(exc), filename=filename) from exc
    visible = strip_dbase_comments(code)
    visible = re.sub(r'"(?:""|[^"\n])*"|\'(?:\'\'|[^\'\n])*\'',
                     lambda match: ' ' * len(match.group(0)), visible)
    mapped = {}
    notes = []
    for prototype in prototypes:
        matched = re.search(r'(?i)\b' + re.escape(prototype.name) + r'\s*\(', visible)
        mapping = (prototype.dll.casefold(), prototype.entry.casefold())
        if mapping in _LINUX_QT_COMPAT:
            _linux_ffi_signature(prototype, filename=filename)
            mapped[prototype.name.casefold()] = (prototype, _LINUX_QT_COMPAT[mapping][0])
            if matched:
                notes.append(f'Linux-Qt5: {prototype.name} wird auf native Qt5-Funktion abgebildet.')
            else:
                notes.append(f'Linux: ungenutzte Windows-DLL-Deklaration {prototype.name} ({prototype.dll}) ausgelassen.')
        elif matched:
            number = visible.count('\n', 0, matched.start()) + 1
            raise LinuxDBaseError(
                f'Windows-DLL-Aufruf {prototype.name} aus {prototype.dll} ist unter Linux nicht verfuegbar. '
                'Verwende eine Linux-.so-Schnittstelle oder einen nativen Linux-Ersatz.',
                line=number, filename=filename)
        else:
            notes.append(f'Linux: ungenutzte Windows-DLL-Deklaration {prototype.name} ({prototype.dll}) ausgelassen.')
    return code, tuple(notes), mapped


def _linux_split_call_args(body: str, *, line: int, filename: str):
    items=[]; current=[]; quote=None; depth=0; i=0
    for ch in body:
        if quote:
            current.append(ch)
            if ch==quote: quote=None
        elif ch in ('"', "'"):
            quote=ch; current.append(ch)
        elif ch=='(':
            depth+=1; current.append(ch)
        elif ch==')':
            depth-=1; current.append(ch)
        elif ch==',' and depth==0:
            items.append(''.join(current).strip()); current=[]
        else:
            current.append(ch)
    if quote or depth!=0:
        raise LinuxDBaseError('Unvollstaendiger WinAPI-Aufruf.',line=line,filename=filename)
    if current or items: items.append(''.join(current).strip())
    return items


def _linux_compat_call(expression: str, mapped: dict, variables: dict, *, line: int, filename: str):
    match=re.fullmatch(r'(?is)([A-Za-z_]\w*)\s*\((.*)\)',expression.strip())
    if not match or match.group(1).casefold() not in mapped:
        return None
    prototype, kind = mapped[match.group(1).casefold()]
    args=_linux_split_call_args(match.group(2),line=line,filename=filename)
    if len(args) != len(prototype.argument_types):
        raise LinuxDBaseError(
            f'{prototype.name} erwartet {len(prototype.argument_types)} Argumente, erhalten: {len(args)}.',
            line=line,filename=filename)
    prepared=[]
    for index,(arg,type_name) in enumerate(zip(args,prototype.argument_types),1):
        typ=ffi_type_info(type_name)
        value=arg.strip()
        if typ.name == 'HWND' and re.fullmatch(r'(?i)(?:this|form1)\.(?:hwnd|handle)',value):
            prepared.append({'x11_window': True})
            continue
        if value.upper() in ('NULL','NIL'):
            prepared.append(None)
            continue
        if re.fullmatch(r'[A-Za-z_]\w*',value) and value.casefold() in variables and variables[value.casefold()] is _RUNTIME:
            prepared.append({'variable':value.casefold()})
            continue
        constant = _safe_constant(value,variables,line=line,filename=filename)
        if typ.category in ('ansi_string','wide_string'):
            if not isinstance(constant,str):
                if constant == 0: prepared.append(None); continue
                raise LinuxDBaseError(f'{prototype.name}: Argument {index} ({type_name}) erwartet Text oder NULL.',line=line,filename=filename)
        elif typ.category in ('pointer','integer'):
            if not isinstance(constant,int) or isinstance(constant,bool):
                raise LinuxDBaseError(f'{prototype.name}: Argument {index} ({type_name}) erwartet einen Integer-/Handle-Wert.',line=line,filename=filename)
            if typ.name == 'HWND' and constant != 0:
                raise LinuxDBaseError('Ein Windows-HWND-Wert kann nicht als X11-XID benutzt werden. Verwende 0 oder THIS.HWND.',line=line,filename=filename)
        prepared.append(constant)
    return ['ffi_call',prototype.entry,prepared,'']


_RUNTIME = object()

def _dbase_static_condition(expression: str, variables: dict, *, line: int, filename: str) -> bool:
    expression = re.sub(r'(?i)\.AND\.', ' and ', expression)
    expression = re.sub(r'(?i)\.OR\.', ' or ', expression)
    expression = re.sub(r'(?i)\.NOT\.', ' not ', expression)
    expression = expression.replace('<>', '!=').replace('=>', '>=')
    # Single '=' in dBASE conditions means comparison, not assignment.
    expression = re.sub(r'(?<![<>=!])=(?!=)', '==', expression)
    value = _safe_constant(expression, variables, line=line, filename=filename)
    if type(value) != bool:
        raise LinuxDBaseError(f'Linux-IF erwartet einen logischen Ausdruck: {expression}', line=line, filename=filename)
    return value


def _linux_print_value(value) -> str:
    if value is True: return '.T.'
    if value is False: return '.F.'
    return str(value)


def _linux_static_statements(statements, *, filename: str, mapped=None, as_actions=False):
    """Compile constant dBASE statements into ordered console output bytes.

    This is intentionally a *bounded* subset. Unknown statements fail with
    original source line numbers instead of being ignored by the WFM GUI path.
    """
    variables, messages, conditions = {}, [], []
    mapped = mapped or {}
    active = True
    for number, raw in statements:
        stripped = str(raw).strip()
        if not stripped or stripped.startswith(('//', '&&', '**', '*', ';')):
            continue
        first = re.match(r'(?i)^IF\s+(.+)$', stripped)
        if first:
            parent = active
            selected = parent and _dbase_static_condition(first.group(1), variables, line=number, filename=filename)
            conditions.append({'parent': parent, 'taken': selected, 'else': False})
            active = selected
            continue
        elif_match = re.match(r'(?i)^(?:ELSEIF|ELIF)\s+(.+)$', stripped)
        if elif_match:
            if not conditions or conditions[-1]['else']:
                raise LinuxDBaseError('ELSEIF ohne passendes IF', line=number, filename=filename)
            state = conditions[-1]
            active = state['parent'] and not state['taken'] and _dbase_static_condition(elif_match.group(1), variables, line=number, filename=filename)
            state['taken'] = state['taken'] or active
            continue
        if stripped.upper() == 'ELSE':
            if not conditions or conditions[-1]['else']:
                raise LinuxDBaseError('ELSE ohne passendes IF', line=number, filename=filename)
            state = conditions[-1]
            active = state['parent'] and not state['taken']
            state['taken'] = True
            state['else'] = True
            continue
        if stripped.upper() == 'ENDIF':
            if not conditions:
                raise LinuxDBaseError('ENDIF ohne IF', line=number, filename=filename)
            active = conditions.pop()['parent']
            continue
        if not active:
            continue
        if re.fullmatch(r'(?i)SET\s+DEBUG\s+(?:ON|OFF)', stripped):
            continue  # Linux runner does not use the Windows debugger window.
        match = re.match(r'^\?\?(.*)$|^\?(.*)$', stripped)
        if match:
            expr = (match.group(1) if match.group(1) is not None else match.group(2)).strip()
            ffi_call = _linux_compat_call(expr, mapped, variables, line=number, filename=filename)
            newline = match.group(1) is None
            if ffi_call is not None:
                if not as_actions:
                    raise LinuxDBaseError('WinAPI-Aufruf erfordert das Linux-Qt5-Terminal.',line=number,filename=filename)
                messages.append(['ffi_print', ffi_call[1], ffi_call[2], newline])
                continue
            if re.fullmatch(r'[A-Za-z_]\w*',expr) and variables.get(expr.casefold()) is _RUNTIME:
                messages.append(['print_var',expr.casefold(),newline])
                continue
            value = _safe_constant(expr, variables, line=number, filename=filename)
            payload = _linux_print_value(value)
            messages.append(['print',payload,newline] if as_actions else payload.encode('utf-8')+(b'\n' if newline else b''))
            continue
        match = re.fullmatch(r'(?i)LOCAL\s+([A-Za-z_]\w*)\s*', stripped)
        if match:
            variables[match.group(1).casefold()] = _UNDEFINED
            continue
        match = re.fullmatch(r'(?i)(?:LOCAL\s+)?([A-Za-z_]\w*)\s*=\s*(.+)', stripped)
        if match:
            ffi_call = _linux_compat_call(match.group(2),mapped,variables,line=number,filename=filename)
            if ffi_call is not None:
                if not as_actions:
                    raise LinuxDBaseError('WinAPI-Aufruf erfordert das Linux-Qt5-Terminal.',line=number,filename=filename)
                name=match.group(1).casefold()
                ffi_call[3]=name
                messages.append(ffi_call)
                variables[name] = _RUNTIME
            else:
                variables[match.group(1).casefold()] = _safe_constant(
                    match.group(2), variables, line=number, filename=filename)
            continue
        match = re.fullmatch(r'(?i)STORE\s+(.+?)\s+TO\s+([A-Za-z_]\w*)', stripped)
        if match:
            variables[match.group(2).casefold()] = _safe_constant(
                match.group(1), variables, line=number, filename=filename)
            continue
        ffi_call = _linux_compat_call(stripped,mapped,variables,line=number,filename=filename)
        if ffi_call is not None:
            if not as_actions:
                raise LinuxDBaseError('WinAPI-Aufruf erfordert das Linux-Qt5-Terminal.',line=number,filename=filename)
            messages.append(ffi_call)
            continue
        raise LinuxDBaseError(
            f'Linux-dBASE-Compiler: Anweisung noch nicht unterstuetzt: {stripped}',
            line=number, filename=filename,
        )
    if conditions:
        raise LinuxDBaseError('IF-Block ohne ENDIF', filename=filename)
    return messages


def _linux_emit_messages(messages: list[bytes], bits: int):
    """Return machine instructions plus data for Linux SYS_write stdout."""
    _exit_code, write_code = _linux_start(bits)
    text, data = [], []
    for idx, message in enumerate(messages, 1):
        if message:
            label = f'__linux_dbase_msg_{idx}'
            text.append(write_code.format(label=label, length=len(message)))
            data.append(_literal_bytes(label, message))
    return text, data

def _linux_qt_call_json(payload: bytes, *, bits: int, entry: str, label: str) -> str:
    """Emit a native ELF entry stub invoking an imported Qt5 C-ABI function."""
    lines = ['section .text', 'entry _start', '_start:']
    if bits == 64:
        lines += [f'    mov rdi, {label}',
                  '    mov rax, [__linux_qt5_function]',
                  '    call rax',
                  '    mov rdi, rax',
                  '    mov rax, 60', '    syscall']
    else:
        lines += [f'    push {label}',
                  '    mov eax, [__linux_qt5_function]',
                  '    call eax', '    add esp, 4',
                  '    mov ebx, eax', '    mov eax, 1', '    int 0x80']
    lines += ['section .data', '__linux_qt5_function:',
              '    ' + ('dq' if bits == 64 else 'dd') + f' {entry}',
              _literal_bytes(label, payload + b'\0')]
    return '\n'.join(lines) + '\n'


def compile_linux_prg(source: str, *, bits: int, filename: str, include_paths=(), qt_terminal: bool = False) -> DBaseCompileResult:
    """Compile the supported dBASE subset to a native Qt5-terminal ELF program.

    No Python bridge is used. The Qt terminal waits for the user to close the
    window and is supplied by libd64_qt5.so on Linux. Unknown statements fail
    at compile time; this is not a full native WFM/dBASE interpreter.
    """
    processed, _macros, _links, warnings, infos = _preprocess_dbase_macros(
        str(source), filename=filename, include_paths=include_paths,
        target='linux64' if bits == 64 else 'linux32',
    )
    processed, unused_ffi, ffi_map = _linux_source_without_unused_ffi(processed, filename=filename)
    statements = strip_dbase_comments(processed)
    messages = _linux_static_statements(enumerate(statements.splitlines(), 1), filename=filename, mapped=ffi_map, as_actions=qt_terminal)
    if not qt_terminal:
        # Keep the existing freestanding console API for CLI/tool callers;
        # the IDE opts into Qt5 explicitly so users see the QDialog terminal.
        exit_code, _write = _linux_start(bits)
        stdout_code, stdout_data = _linux_emit_messages(messages, bits)
        source_lines = ['section .text', 'entry _start', '_start:'] + stdout_code + [exit_code, 'section .data'] + stdout_data
        return DBaseCompileResult(
            assembly='\n'.join(source_lines) + '\n',
            target='linux64' if bits == 64 else 'linux32',
            windows_application_mode='Console', source_kind='program',
            notes=('Linux Stage 490: freestanding console compatibility; qt_terminal=True for native Qt5 dialog.',) + tuple(infos),
            warnings=tuple(warnings) + unused_ffi,
        )
    payload = json.dumps({'title': 'dBASE Terminal – ' + Path(filename).name,
                          'output': [str(act[1])+('\n' if act[2] else '') for act in messages if act[0]=='print'],
                          'actions': messages},
                         ensure_ascii=False).encode('utf-8')
    return DBaseCompileResult(
        assembly=_linux_qt_call_json(payload, bits=bits, entry='DBaseQtRunConsoleJson', label='__linux_console_json'),
        target='linux64' if bits == 64 else 'linux32',
        windows_application_mode='GUI', source_kind='program',
        notes=('Linux Stage 490: Qt5 Terminal via native libd64_qt5.so.',
               'TYPE/VARTYPE, Zuweisungen und einfache IF-Anweisungen: begrenzter statischer Teilumfang.',) + tuple(infos),
        warnings=tuple(warnings) + unused_ffi,
    )

def _linux_event_value(expression: str, variables: dict, *, line: int, filename: str):
    """Translate a WFM-event expression without evaluating live event arguments.

    Runtime variables are references, not constants. Only known literal and
    variable expressions are accepted; unsupported dynamic operations fail
    during compilation rather than changing semantics silently.
    """
    value = str(expression).strip()
    if re.fullmatch(r'(?i)THIS\.HWND', value):
        return {'x11_window': True}
    if re.fullmatch(r'[A-Za-z_]\w*', value) and value.casefold() in variables:
        if variables[value.casefold()] is _RUNTIME:
            return {'variable': value.casefold()}
        if variables[value.casefold()] is _UNDEFINED:
            return None
    return _safe_constant(value, variables, line=line, filename=filename)


def compile_linux_wfm(source: str, *, bits: int, filename: str, include_paths=()) -> DBaseCompileResult:
    """Qt5 GUI in a self-contained ELF launcher; validates unsupported WFM syntax."""
    preprocessed, _macros, _links, warnings, infos = _preprocess_dbase_macros(
        str(source), filename=filename, include_paths=include_paths,
        target='linux64' if bits == 64 else 'linux32',
    )
    # Stage 490: Windows headers may declare unused extern prototypes even
    # when the Linux WFM uses only built-ins. Drop unused declarations, but
    # refuse *actual* Windows calls with the call-site line in the diagnostic.
    preprocessed, unused_ffi, ffi_map = _linux_source_without_unused_ffi(preprocessed, filename=filename)
    model = parse_dbase_wfm(preprocessed, filename=filename)
    preamble = wfm_executable_preamble(preprocessed, class_name=model.class_name)
    startup_actions = _linux_static_statements(enumerate(preamble, 1), filename=filename, mapped=ffi_map, as_actions=True)
    controls = []
    for control in model.controls:
        controls.append({'path':control.path, 'parent':control.parent_path,
                         'class':control.class_name, 'properties':control.properties,
                         'events':control.events})
    # Never silently claim to have compiled native dBASE methods that this
    # restricted GUI bridge cannot execute. Reject unsupported event semantics.
    supported_controls = {
        'button','pushbutton','commandbutton','label','statictext','edit',
        'lineedit','textbox','memo','textedit','checkbox','radiobutton',
        'combobox','listbox','groupbox','progressbar',
    }
    for control in model.controls:
        if control.class_name.casefold() not in supported_controls:
            raise LinuxDBaseError(
                f'Linux-Qt5-Steuerelement noch nicht implementiert: {control.class_name}',
                filename=filename,
            )
        for key in control.events:
            if key.casefold() != 'onclick':
                raise LinuxDBaseError(
                    f'Linux-Qt5-Ereignis {key} noch nicht implementiert: {control.path}',
                    filename=filename,
                )
    methods = {method.name.casefold(): method for method in model.methods}
    method_map = {}
    for control in model.controls:
        for key, value in control.events.items():
            name = str(value).split('::')[-1].strip().casefold()
            method = methods.get(name)
            if method is None:
                raise LinuxDBaseError(
                    f'Linux-Qt5-Ereignisprozedur nicht gefunden: {value}',
                    filename=filename,
                )
            if name in method_map:
                continue
            # QAbstractButton::clicked(bool) supplies one sender and one checked
            # state. Parameter names are declared in dBASE, not injected as
            # compile-time constants; the native Qt5 runtime binds them when
            # the event is delivered. In particular, Sender is a native X11
            # WId on xcb, never a Windows HWND nor a fabricated XID on Wayland.
            if len(method.parameters) > 2 or any(param.startswith('**') for param in method.parameters):
                raise LinuxDBaseError(
                    f'Linux-Qt5-onClick {method.name}: erwartet hoechstens zwei '
                    'Ereignisparameter (Sender, Checked); variadische Parameter sind nicht verfuegbar.',
                    line=method.source_start_line, filename=filename,
                )
            runtime_vars = {param.casefold(): _RUNTIME for param in method.parameters}
            actions = []
            saw_return = False
            for number, raw in enumerate(method.body, method.source_start_line + 1):
                statement = strip_dbase_comments(raw).strip()
                if not statement or statement.startswith(('//', '**', '&&')):
                    continue
                return_match = re.fullmatch(r'(?i)RETURN(?:\s+(.+))?', statement)
                if return_match:
                    expression = (return_match.group(1) or '').strip()
                    if method.kind == 'function' and not expression:
                        raise LinuxDBaseError(
                            f'FUNCTION {method.name} erwartet RETURN <Ausdruck>.',
                            line=number, filename=filename,
                        )
                    if method.kind != 'function' and expression:
                        raise LinuxDBaseError(
                            f'PROCEDURE {method.name} darf keinen RETURN-Wert angeben.',
                            line=number, filename=filename,
                        )
                    ffi_return = (_linux_compat_call(expression, ffi_map, runtime_vars,
                                                      line=number, filename=filename)
                                  if expression else None)
                    if ffi_return is not None:
                        actions.append(['ffi_return', ffi_return[1], ffi_return[2]])
                    else:
                        value_spec = (_linux_event_value(expression, runtime_vars,
                                                         line=number, filename=filename)
                                      if expression else None)
                        actions.append(['return', value_spec])
                    saw_return = True
                    continue
                write_match = re.fullmatch(r'(\?\??)\s*(.+)', statement)
                if write_match:
                    value_text = write_match.group(2).strip()
                    ffi_call = _linux_compat_call(value_text, ffi_map, runtime_vars, line=number, filename=filename)
                    newline = write_match.group(1) == '?'
                    if ffi_call is not None:
                        actions.append(['ffi_print', ffi_call[1], ffi_call[2], newline])
                    else:
                        value_spec = _linux_event_value(value_text, runtime_vars, line=number, filename=filename)
                        if isinstance(value_spec, dict):
                            actions.append(['print_value', value_spec, newline])
                        else:
                            actions.append(['print', _linux_print_value(value_spec), newline])
                    continue
                ffi_call = _linux_compat_call(statement, ffi_map, runtime_vars, line=number, filename=filename)
                if ffi_call is not None:
                    actions.append(ffi_call)
                    continue
                set_text = re.fullmatch(
                    r'(?i)(THIS(?:\.\w+)*)\.(Text|Caption)\s*=\s*(.+)', statement)
                if set_text:
                    value_spec = _linux_event_value(set_text.group(3), runtime_vars, line=number, filename=filename)
                    if isinstance(value_spec, dict):
                        actions.append(['settext_value', set_text.group(1), value_spec])
                    else:
                        actions.append(['settext', set_text.group(1), str(value_spec)])
                    continue
                local_match = re.fullmatch(r'(?i)LOCAL\s+([A-Za-z_]\w*)\s*', statement)
                if local_match:
                    runtime_vars[local_match.group(1).casefold()] = _UNDEFINED
                    continue
                assign_match = re.fullmatch(r'(?i)(?:LOCAL\s+)?([A-Za-z_]\w*)\s*=\s*(.+)', statement)
                if assign_match:
                    variable = assign_match.group(1).casefold()
                    ffi_call = _linux_compat_call(assign_match.group(2), ffi_map, runtime_vars,
                                                  line=number, filename=filename)
                    if ffi_call is not None:
                        ffi_call[3] = variable
                        actions.append(ffi_call)
                        runtime_vars[variable] = _RUNTIME
                    else:
                        value_spec = _linux_event_value(assign_match.group(2), runtime_vars,
                                                        line=number, filename=filename)
                        actions.append(['set_var', variable, value_spec])
                        runtime_vars[variable] = (_RUNTIME if isinstance(value_spec, dict) else value_spec)
                    continue
                raise LinuxDBaseError(
                    f'Linux-Qt5-Ereigniscode noch nicht implementiert: {statement}',
                    line=number, filename=filename,
                )
            # A trailing bare RETURN in a PROCEDURE is a no-op. Preserve
            # the Stage-487 JSON action shape so older Qt runtimes/tests
            # continue to accept parameterless procedures unchanged.
            if method.kind != 'function' and actions and actions[-1] == ['return', None]:
                actions.pop()
            if method.kind == 'function' and not saw_return:
                raise LinuxDBaseError(
                    f'FUNCTION {method.name} muss RETURN <Ausdruck> enthalten.',
                    line=method.source_start_line, filename=filename,
                )
            if method.kind == 'function':
                warnings = tuple(warnings) + (
                    f'Linux-Qt5: FUNCTION {method.name} liefert einen Wert; Qt clicked(bool) '
                    'wertet den Rueckgabewert nicht aus.',)
            if method.parameters or method.kind == 'function':
                method_map[name] = {'parameters': list(method.parameters),
                                    'kind': method.kind, 'actions': actions}
            else:
                # Preserve the compact Stage-487/490 JSON for old procedures.
                method_map[name] = actions
    payload = json.dumps({'name':model.class_name, 'properties':model.properties,
                          'controls': controls, 'methods':method_map,
                          'startup_output': [str(action[1])+('\n' if action[2] else '') for action in startup_actions if action[0]=='print'],
                          'startup_actions': startup_actions},
                         ensure_ascii=False, default=str).encode('utf-8')
    # WFM top-level ? / ?? output uses the SAME Qt terminal as event handlers.
    assembly = _linux_qt_call_json(payload, bits=bits, entry='DBaseQtRunFormJson', label='__linux_wfm_json')
    return DBaseCompileResult(
        assembly=assembly, target='linux64' if bits == 64 else 'linux32',
        windows_application_mode='GUI', source_kind='form',
        notes=('Linux Stage 490: native Qt5-Form und Qt5-Terminal via ELF DT_NEEDED.',
               'WFM-Basiskomponenten, statischer Top-Level-dBASE-Code inklusive TYPE/VARTYPE und einfache onClick/?-Methoden.',
               'Komplexe native WFM-Methoden noch nicht implementiert.',) + tuple(infos),
        warnings=tuple(warnings) + unused_ffi,
    )
