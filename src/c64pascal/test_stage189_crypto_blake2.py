from pathlib import Path

try:
    from . import compiler as c
except ImportError:
    import compiler as c


def main() -> int:
    root = Path(__file__).resolve().parent
    source_path = root / "samples" / "Crypto.blake2.pas"
    source = source_path.read_text(encoding="utf-8")
    processed = c.PascalPreprocessor().process(source, filename=str(source_path))
    transformed, unit_name, interface_uses, implementation_uses, interface_source, _ = (
        c._unit_program_source(processed.source, filename=str(source_path))
    )
    bridged, _, externals, _, _, markers = c._legacy_pascal_extension_bridge(transformed)
    assert unit_name == "Crypto.blake2"
    assert interface_uses == ("System.Types",)
    assert implementation_uses == ()
    assert [(x.name, x.symbol) for x in externals] == [("_jit_blake2", "__jit_blake2")]
    assert ("function", "crypt", 13, "cdecl") in markers
    assert "__D64GlobalRoutines.crypt" in bridged
    crypt_line = next(line for line in bridged.splitlines() if "__D64GlobalRoutines.crypt" in line)
    assert "cdecl" not in crypt_line.casefold()
    parser_source, routines = c._pui_routine_information(unit_name, interface_source)
    assert len(routines) == 1
    assert routines[0]["name"] == "crypt"
    assert routines[0]["calling_convention"] == "cdecl"
    assert routines[0]["symbol"] == "__pas_Crypto_blake2_crypt"
    assert "crypt" not in parser_source.casefold()
    print("Crypto.blake2 Stage189 bridge/PUI metadata: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
