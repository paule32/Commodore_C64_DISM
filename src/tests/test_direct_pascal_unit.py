from pathlib import Path


def test_direct_unit_creates_pui_and_unit_assembly(tmp_path: Path) -> None:
    from c64pascal import compile_pascal_to_assembly

    source_path = tmp_path / "Example.pas"
    source_path.write_text(
        """unit Example;
interface
const Answer = 42;
procedure Test;
implementation
end.
""",
        encoding="utf-8",
    )

    generated = compile_pascal_to_assembly(
        source_path.read_text(encoding="utf-8"),
        filename=str(source_path),
        include_paths=[tmp_path],
        target="amiga",
    )

    assert generated.source_kind == "unit"
    assert generated.unit_name == "Example"
    assert source_path.with_suffix(".pui").is_file()
    assert "xdef __unit_Example" in generated.assembly
    assert ".bootable" not in generated.assembly
