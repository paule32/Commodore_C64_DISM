# -*- coding: utf-8 -*-
"""Stage 679 O3: share the unmodified TObject VMT with libd64_qt5.dll.

This is deliberately a guarded post-pass. It operates only on a class emitter
that explicitly confirms the TObject standard methods are built-ins and whose
nine-entry table matches the known ABI. User-redefined TObject methods, ABI
exports, and custom/inherited override tables are left intact. Replacements
preserve the number of ASM source lines to keep diagnostics stable.
"""
from __future__ import annotations

import re

_BUILTIN_MARKER = '; Stage 679: TObject builtin virtual methods; DLL fallback safe'
_EXPECTED = ('__del__', 'free', 'freeinstance', 'classtype', 'classparent',
             'classnameaddress', 'classname', 'instancesize', 'inheritsfrom')
_LABEL = re.compile(r'^\s*([a-z_.$?@][\w.$?@]*):\s*(?:;.*)?$', re.I)
_SECTION = re.compile(r'^\s*section\s+(\.\w+)', re.I)
_TABLE_ENTRY = re.compile(r'^\s*(dd|dq)\s+([a-z_.$?@][\w.$?@]*)\s*(?:;.*)?$', re.I)


def compact_dbase_tobject_method_tables(assembly: str) -> tuple[str, int]:
    """Remove duplicate base tables and provably unreferenced std method code.

    ``instance_size`` bit 31 already marks a compact VMT. For a default
    signature its existing final word becomes null, selecting the DLL's
    shared nine-entry table in jitObject.cc. A derived override retains its
    own table, and any inherited standard functions referenced by it remain.
    """
    if _BUILTIN_MARKER not in assembly:
        return assembly, 0
    lines = assembly.splitlines(keepends=True)
    stripped = [line.strip() for line in lines]
    table_indices = [i for i, line in enumerate(stripped)
                     if line.lower() == '__dbase_class_object:']
    if len(table_indices) != 1:
        return assembly, 0
    begin = table_indices[0]
    if begin + len(_EXPECTED) >= len(lines):
        return assembly, 0
    ptr = None
    for k, name in enumerate(_EXPECTED, start=1):
        item = _TABLE_ENTRY.fullmatch(stripped[begin + k])
        if not item or item.group(2).casefold() != '__dbase_cls_tobject_' + name:
            return assembly, 0
        if ptr is not None and item.group(1).lower() != ptr:
            return assembly, 0
        ptr = item.group(1).lower()

    # All references to the old table must be compact VMT last words; refuse
    # to erase the definition if a foreign part of the assembly uses it.
    replacements = []
    in_data = False
    for i, line in enumerate(stripped):
        section = _SECTION.match(line)
        if section:
            in_data = section.group(1).lower() == '.data'
        if i in range(begin, begin + len(_EXPECTED) + 1):
            continue
        code = line.split(';', 1)[0].strip()
        if not re.search(r'\b__dbase_class_object\b', code, re.I):
            continue
        if not in_data or not re.fullmatch(rf'{ptr}\s+__dbase_class_object', code, re.I):
            return assembly, 0
        # Ensure this is the 6th entry in a known six-word compact VMT.
        if i < 6 or not re.fullmatch(r'__dbase_vmt_[a-z_][\w]*:', stripped[i-6], re.I):
            return assembly, 0
        if not all(re.fullmatch(rf'{ptr}\s+(?:0x[0-9a-f]+|\d+|[a-z_.$?@][\w.$?@]*)', stripped[k], re.I) for k in range(i-5, i)):
            return assembly, 0
        replacements.append(i)
    if not replacements:
        return assembly, 0

    def hide(i: int, note: str) -> None:
        newline = '\r\n' if lines[i].endswith('\r\n') else '\n' if lines[i].endswith('\n') else ''
        lines[i] = f'    ; O3: {note}' + newline

    for i in replacements:
        lines[i] = re.sub(r'\b__dbase_class_object\b', '0', lines[i], count=1, flags=re.I)
    for i in range(begin, begin + len(_EXPECTED) + 1):
        hide(i, 'TObject Standardtabelle liegt in libd64_qt5.dll')

    # Drop built-in function bodies only when they truly have no references
    # anywhere else in this translation unit. Retaining needed thunks is
    # important for custom override tables, methods or external DLL exports.
    removed_instructions = 0
    code = [line.split(';', 1)[0] for line in lines]
    labels = {name: '__dbase_cls_tobject_' + name for name in _EXPECTED}
    for label in labels.values():
        declarations = [i for i, s in enumerate(code)
                        if s.strip().lower() == label + ':']
        if len(declarations) != 1:
            continue
        first = declarations[0]
        # Only scan routines emitted before section .data, never cross into
        # data or another procedure; standard bodies have no nested labels.
        block_end = first + 1
        while block_end < len(code):
            item = code[block_end].strip()
            if (_SECTION.match(item) or _LABEL.fullmatch(item) or
                    re.match(r"(?:global|export|import)\b", item, re.I)):
                break
            block_end += 1
        body = code[first + 1:block_end]
        if not body or not any(re.fullmatch(r'\s*ret\s*', item, re.I) for item in body):
            continue
        # Custom user bodies have dedicated internal labels/epilogues and
        # cannot satisfy the short, regular built-in method-body check.
        if block_end - first > 20:
            continue
        refs = 0
        for j, statement in enumerate(code):
            if j == first:
                continue
            if re.search(r'\b' + re.escape(label) + r'\b', statement, re.I):
                refs += 1
        if refs:
            continue
        # Cross-module export references are caught by `refs`. Preserve all
        # code blocks with complicated directives even when unreferenced.
        if any(re.match(r'^\s*(?:global|export|section|import)\b', x, re.I)
               for x in body):
            continue
        for j in range(first, block_end):
            if code[j].strip() and not code[j].strip().startswith(';') and j != first:
                removed_instructions += 1
            hide(j, 'unreferenzierte TObject Standardmethode')
            code[j] = ''

    # The existing null-table encoding would be misread by Stage-678 and
    # older runtime DLLs. This real (unreachable) call creates a PE import
    # that makes the Windows loader reject an incompatible old DLL early.
    # It also survives the Stage-668 Programme object/startup-stripping pass.
    output = ''.join(lines)
    capability_import = ('import __dbase_o3_default_vmt_abi, "libd64_qt5.dll", '
                         '"jit_default_tobject_vmt_abi"\n')
    first_text = re.search(r'^section \.text\s*$', output, re.I | re.M)
    first_data = re.search(r'^section \.data\s*$', output, re.I | re.M)
    if first_text and first_data and first_text.start() < first_data.start():
        output = output[:first_text.start()] + capability_import + output[first_text.start():]
        first_data = re.search(r'^section \.data\s*$', output, re.I | re.M)
        output = (output[:first_data.start()] +
                  '\n; Stage 679: O3 runtime ABI import guard\n'
                  '__dbase_o3_abi_guard:\n'
                  '    call __dbase_o3_default_vmt_abi\n'
                  '    ret\n\n' + output[first_data.start():])
    return output, removed_instructions
