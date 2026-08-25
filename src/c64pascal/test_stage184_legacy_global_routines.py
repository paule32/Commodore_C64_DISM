from pathlib import Path
import importlib.util
import sys
import types

ROOT = Path(__file__).resolve().parent


def load_with_old_generated_parser():
    package_name = "_stage184_legacy_test"
    for name in list(sys.modules):
        if name.startswith(package_name):
            sys.modules.pop(name, None)

    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

    generated = types.ModuleType(package_name + ".generated")
    generated.__path__ = [str(ROOT / "generated")]
    sys.modules[generated.__name__] = generated

    class OldLexer:
        pass

    class OldParser:
        pass

    class DummyVisitor:
        pass

    for module_name, class_name, value in (
        ("C64PascalLexer", "C64PascalLexer", OldLexer),
        ("C64PascalParser", "C64PascalParser", OldParser),
        ("C64PascalParserVisitor", "C64PascalParserVisitor", DummyVisitor),
    ):
        module = types.ModuleType(package_name + ".generated." + module_name)
        setattr(module, class_name, value)
        sys.modules[module.__name__] = module

    spec = importlib.util.spec_from_file_location(
        package_name + ".compiler",
        ROOT / "compiler.py",
    )
    compiler = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = compiler
    spec.loader.exec_module(compiler)
    return compiler


def main() -> int:
    compiler = load_with_old_generated_parser()
    source_path = ROOT / "units" / "System" / "Strings.pas"
    source = source_path.read_text(encoding="utf-8")

    processed = compiler.PascalPreprocessor().process(
        source,
        filename=str(source_path),
    )
    transformed, unit_name, *_ = compiler._unit_program_source(
        processed.source,
        filename=str(source_path),
    )
    (
        parser_source,
        _extra_types,
        extra_externals,
        _extra_properties,
        _inherited,
        global_markers,
    ) = compiler._legacy_pascal_extension_bridge(transformed)

    assert unit_name == "System.Strings"
    assert [item.name for item in extra_externals] == [
        "jit_dynstring_from_cstr",
        "_IntToStr",
        "_StrToInt",
    ]
    assert [(kind, name) for kind, name, _line in global_markers] == [
        ("function", "IntToStr"),
        ("function", "StrToInt"),
    ]
    assert "__D64GlobalRoutines.IntToStr" in parser_source
    assert "__D64GlobalRoutines.StrToInt" in parser_source
    assert "cdecl; external;" not in parser_source.casefold()

    print("Stage184 legacy global-routine bridge: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
