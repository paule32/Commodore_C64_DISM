"""dBASE native CLASS DLL backend (PE32 / PE64).

This backend deliberately does *not* recycle the normal Qt console EXE _start.
Only declarations and native CLASS methods are legal in this first DLL
module mode.  Unexpected top-level statements are rejected rather than
silently compiled to an unreachable EXE entry point.
"""
from __future__ import annotations


def compile_dbase_class_library(
    source: str, *, filename: str, target: str, include_paths=(),
    peephole_options=None,
):
    from .compiler import (
        DBaseClassDefinition, DBaseCompilerError, DBaseCompileResult,
        parse_dbase_statements, preprocess_dbase_source,
        remap_dbase_source_error,
    )
    from .object_abi import emit_classes, native_class_definitions, vmt_label, method_label, METHODS

    if target not in ("pe32", "pe64"):
        raise DBaseCompilerError(
            "dBASE-Klassen-DLLs werden derzeit nur für Windows PE32/PE64 erzeugt.",
            filename=filename,
        )
    frontend = preprocess_dbase_source(
        source, filename=filename, target=target, include_paths=include_paths,
    )
    try:
        statements = parse_dbase_statements(
            frontend.preprocessed_source or frontend.source,
            filename=filename, target=target,
        )
    except DBaseCompilerError as exc:
        raise remap_dbase_source_error(exc, frontend.source_locations) from None
    classes = tuple(item for item in statements if isinstance(item, DBaseClassDefinition))
    unsupported = tuple(item for item in statements if not isinstance(item, DBaseClassDefinition))
    native_classes = native_class_definitions(classes)
    if not native_classes:
        raise DBaseCompilerError(
            "dBASE-Runtime-DLL: Keine native CLASS-Deklaration gefunden. "
            "Für reine PROCEDURE/FUNCTION-DLLs ist noch ein separates Backend erforderlich.",
            filename=filename,
        )
    # The managed exception status is currently part of the linked dBASE
    # executable. A CLASS DLL needs a process-wide exception ABI before its
    # THROW/CATCH may interoperate with the caller; never emit unresolved
    # executable-global status references into an independent DLL.
    for definition in native_classes:
        for method in getattr(definition, 'methods', ()):
            for number, raw in getattr(method, 'body', ()):
                if str(raw).strip().split(None, 1)[0].casefold() in {'try', 'throw'}:
                    raise DBaseCompilerError(
                        'TRY/THROW in einer eigenstaendigen Klassen-DLL benoetigt eine '
                        'gemeinsame Exception-Runtime-ABI; derzeit nur in dBASE-EXE-Klassenmethoden.',
                        line=number, filename=filename)
    if unsupported:
        item = unsupported[0]
        raise DBaseCompilerError(
            "In einem dBASE-Runtime-DLL-Klassenmodul sind bislang nur EXTERN-, "
            "Präprozessor- und CLASS/ENDCLASS-Deklarationen erlaubt; "
            "ausführbare Anweisungen außerhalb von CLASS benötigen ein eigenes DLL-Backend.",
            line=getattr(item, 'line', 0), filename=filename,
        )
    # Stage 611: native CLASS IF comparisons can bypass the generic
    # zero/stack/boolean materialization only with all three controls on.
    from windows_peephole import normalize_peephole_options
    peephole = normalize_peephole_options(peephole_options)
    optimized_null_tests = all(peephole.values())
    try:
        imports, code, data = emit_classes(
            native_classes, target=target, ffi_prototypes=frontend.ffi_prototypes,
            filename=filename, optimize_null_comparisons=optimized_null_tests,
        )
    except DBaseCompilerError as exc:
        raise remap_dbase_source_error(exc, frontend.source_locations) from None
    except ValueError as exc:
        raise DBaseCompilerError(str(exc), filename=filename) from None
    ffi_imports = [prototype.import_line for prototype in frontend.ffi_prototypes]
    # The native class emitter uses only symbols it references. Keeping extra
    # explicit imports in the assembly does not force an unused Windows IAT.
    import_lines = list(dict.fromkeys([*imports, *ffi_imports]))
    is64 = target == 'pe64'
    # Publish the VMT through a pointer-returning code export (the PE64 linker
    # does not export .data labels). Keep method names stable for clients.
    export_specs = []
    vmt_getters = []
    for cls in native_classes:
        # The PE64 COFF linker exports only .text symbols, not raw .data
        # addresses. Expose an ABI-safe pointer-returning getter instead.
        getter = method_label(cls.name, 'vmt')
        export_specs += [(getter, getter),
                         (method_label(cls.name, 'create'), method_label(cls.name, 'create'))]
        vmt_getters.extend([
            f'global {getter}',
            f'{getter}:',
            f'    mov {"rax" if is64 else "eax"}, {vmt_label(cls.name)}',
            '    ret',
        ])
    # Native child members are ABI-callable symbols. Private fields do not
    # receive a publicly exported getter; their access is class-local.
    for cls in native_classes:
        if cls.name.casefold() == 'tobject':
            continue
        for method in getattr(cls, 'methods', ()):
            symbol = method_label(cls.name, method.name)
            export_specs.append((symbol, symbol))
        for prop in getattr(cls, 'properties', ()):
            if prop.visibility == 'public':
                symbol = method_label(cls.name, 'get_' + prop.name)
                export_specs.append((symbol, symbol))
                setter = method_label(cls.name, 'set_' + prop.name)
                export_specs.append((setter, setter))
    # TObject methods are emitted even for a derived-only native class.
    for lifecycle in ('__ini__', '__del__'):
        symbol = method_label('TObject', lifecycle)
        export_specs.append((symbol, symbol))
    for name, _kind, _args, _ret in METHODS:
        symbol = method_label('TObject', name)
        export_specs.append((symbol, symbol))
    exports = [f'export "{public}", {symbol}' for public, symbol in dict(export_specs).items()]

    lines = [
        f'bits {64 if is64 else 32}',
        '; dBASE Runtime CLASS DLL – no Qt GUI / no EXE startup',
        *import_lines,
        'global __d64_dll_entry',
        'entry __d64_dll_entry',
        *exports,
        '', 'section .text', '',
        '__d64_dll_entry:',
        '    mov eax, 1',
        '    ret' if is64 else '    ret 12',
        '',
        *code,
        *vmt_getters,
        '', 'section .data', '',
        *data,
        '', 'section .bss', '',
    ]
    return DBaseCompileResult(
        assembly='\n'.join(lines), target=target,
        windows_application_mode='GUI', source_kind='library',
        notes=("dBASE-Runtime-DLL mit nativen JitVmt-Klassen, "
               "DLL-Einstiegspunkt und exportierten VMT-/Methodenadressen.",),
        warnings=tuple(frontend.preprocessor_warnings),
        frontend=frontend, statements=statements,
    )
