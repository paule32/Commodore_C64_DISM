from c64c.compiler import compile_c_to_assembly


def _compile(source: str, target: str):
    return compile_c_to_assembly(
        source,
        filename=f"for_optional_{target}.c",
        target=target,
    )


def test_c64_accepts_endless_for():
    generated = _compile(
        "int main(void) { for (;;) { break; } return 0; }",
        "c64",
    )
    assert "c_for_condition" in generated.assembly
    assert "c_for_end" in generated.assembly


def test_amiga_accepts_endless_for():
    generated = _compile(
        "int main(void) { for (;;) { break; } return 0; }",
        "amiga",
    )
    assert "c_for_condition" in generated.assembly
    assert "c_for_end" in generated.assembly


def test_c64_accepts_missing_initializer_and_update():
    generated = _compile(
        "int main(void) { int i; i = 0; for (; i < 3;) { i++; } return i; }",
        "c64",
    )
    assert "c_for_update" in generated.assembly


def test_continue_uses_for_update_label():
    generated = _compile(
        "int main(void) { int i; for (i = 0; i < 3; i++) { continue; } return i; }",
        "c64",
    )
    assert "c_for_update" in generated.assembly
