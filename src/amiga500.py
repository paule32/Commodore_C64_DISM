"""Kleiner Motorola-68000-Assembler, Hunk-Writer und Boot-ADF-Writer.

Der Assembler ist bewusst auf den vom eingebauten Pascal-/C-Backend
erzeugten, A500-kompatiblen Befehlssatz begrenzt.  Alle internen Adressen
werden PC-relativ erzeugt, so dass das resultierende HUNK_CODE-Segment keine
Relokationstabelle benötigt. Standalone-Programme werden von einem kleinen
Bootblock über ``trackdisk.device`` aus den nachfolgenden ADF-Sektoren in das
Chip-RAM geladen; dadurch ist der Nutzcode nicht auf 1012 Byte begrenzt.
"""

from __future__ import annotations

import re
import struct

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


HUNK_HEADER = 0x000003F3
HUNK_CODE = 0x000003E9
HUNK_END = 0x000003F2

ADF_SIZE = 80 * 2 * 11 * 512
BOOT_BLOCK_SIZE = 1024
BOOT_CODE_OFFSET = 12
AMIGA_DD_ROOT_BLOCK = 880
BOOT_PAYLOAD_OFFSET = BOOT_BLOCK_SIZE
BOOT_PAYLOAD_ADDRESS = 0x00040000
BOOT_STACK_ADDRESS = 0x0007FFFC
MAX_BOOT_PAYLOAD_SIZE = 0x0003F000


class AmigaAssemblerError(Exception):
    """Assemblerfehler mit optionaler Quellzeile."""

    def __init__(self, message: str, line: int = 0) -> None:
        self.message = str(message)
        self.line = int(line or 0)
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.line:
            return f"Zeile {self.line}: {self.message}"
        return self.message


@dataclass(frozen=True)
class AmigaProgram:
    executable: bytes
    code: bytes
    entry_offset: int
    end_offset: int
    instruction_count: int
    hunk_count: int = 1


@dataclass(frozen=True)
class AmigaBootProgram:
    """Bootfähiges ADF mit Trackloader und direkt ausführbarem 68000-Code."""

    adf: bytes
    boot_block: bytes
    code: bytes
    entry_offset: int
    end_offset: int
    instruction_count: int
    hunk_count: int = 0
    load_address: int = BOOT_PAYLOAD_ADDRESS
    payload_offset: int = BOOT_PAYLOAD_OFFSET


@dataclass(frozen=True)
class _SourceItem:
    line: int
    offset: int
    text: str


@dataclass(frozen=True)
class _EffectiveAddress:
    mode: int
    register: int
    extension_kind: str = ""
    expression: str = ""

    @property
    def bits(self) -> int:
        return (self.mode << 3) | self.register

    def extension_words(
        self,
        labels: Dict[str, int],
        extension_offset: int,
        size: str,
        line: int,
        resolve: bool,
    ) -> List[int]:
        kind = self.extension_kind
        if not kind:
            return []
        if kind == "immediate":
            value = _parse_expression(self.expression, labels, line, resolve)
            if size == "l":
                value &= 0xFFFFFFFF
                return [(value >> 16) & 0xFFFF, value & 0xFFFF]
            return [value & 0xFFFF]
        if kind == "pc":
            target = _parse_expression(self.expression, labels, line, resolve)
            displacement = target - extension_offset if resolve else 0
            _require_signed_word(displacement, line, "PC-relativer Abstand")
            return [displacement & 0xFFFF]
        if kind == "displacement":
            value = _parse_expression(self.expression, labels, line, resolve)
            _require_signed_word(value, line, "Adressabstand")
            return [value & 0xFFFF]
        if kind == "absolute_word":
            value = _parse_expression(self.expression, labels, line, resolve)
            if resolve and not -32768 <= value <= 0xFFFF:
                raise AmigaAssemblerError(
                    f"Absolute Word-Adresse außerhalb des Bereichs: {value}.",
                    line,
                )
            return [value & 0xFFFF]
        raise AmigaAssemblerError(f"Interner EA-Fehler: {kind}.", line)


_LABEL_RE = re.compile(r"^[A-Za-z_.$][A-Za-z0-9_.$]*$")
_REGISTER_RE = re.compile(r"^(?P<kind>[dDaA])(?P<number>[0-7])$")
_INDIRECT_RE = re.compile(r"^\((?P<register>a[0-7]|sp)\)$", re.IGNORECASE)
_POSTINC_RE = re.compile(r"^\((?P<register>a[0-7]|sp)\)\+$", re.IGNORECASE)
_PREDEC_RE = re.compile(r"^-\((?P<register>a[0-7]|sp)\)$", re.IGNORECASE)
_INDEXED_RE = re.compile(
    r"^(?P<expression>.+?)\((?P<register>a[0-7]|sp|pc)\)$",
    re.IGNORECASE,
)


def _register_number(text: str, line: int) -> Tuple[str, int]:
    lowered = text.strip().lower()
    if lowered == "sp":
        return "a", 7
    match = _REGISTER_RE.fullmatch(lowered)
    if match is None:
        raise AmigaAssemblerError(f"Register erwartet: {text}.", line)
    return match.group("kind").lower(), int(match.group("number"))


def _parse_number(text: str) -> Optional[int]:
    value = text.strip()
    sign = 1
    if value.startswith(("+", "-")):
        if value[0] == "-":
            sign = -1
        value = value[1:].strip()
    try:
        if value.startswith("$"):
            return sign * int(value[1:], 16)
        if value.startswith("%"):
            return sign * int(value[1:], 2)
        if value.lower().startswith("0x"):
            return sign * int(value[2:], 16)
        if value.lower().startswith("0b"):
            return sign * int(value[2:], 2)
        if value.isdigit():
            return sign * int(value, 10)
    except ValueError:
        return None
    return None


def _parse_expression(
    text: str,
    labels: Dict[str, int],
    line: int,
    resolve: bool,
) -> int:
    expression = text.strip()
    numeric = _parse_number(expression)
    if numeric is not None:
        return numeric

    match = re.fullmatch(
        r"(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)"
        r"(?:\s*(?P<operator>[+-])\s*(?P<offset>.+))?",
        expression,
    )
    if match is None:
        raise AmigaAssemblerError(f"Ungültiger Ausdruck: {text}.", line)
    label = match.group("label").casefold()
    if label not in labels:
        if not resolve:
            base = 0
        else:
            raise AmigaAssemblerError(
                f"Symbol nicht definiert: {match.group('label')}.",
                line,
            )
    else:
        base = labels[label]
    offset_text = match.group("offset")
    if offset_text:
        offset = _parse_number(offset_text)
        if offset is None:
            raise AmigaAssemblerError(
                f"Numerischer Symbolabstand erwartet: {offset_text}.",
                line,
            )
        base = base + offset if match.group("operator") == "+" else base - offset
    return base


def _require_signed_word(value: int, line: int, description: str) -> None:
    if not -32768 <= int(value) <= 32767:
        raise AmigaAssemblerError(
            f"{description} liegt außerhalb -32768..32767: {value}.",
            line,
        )


def _parse_ea(text: str, line: int) -> _EffectiveAddress:
    operand = text.strip()
    if operand.startswith("#"):
        return _EffectiveAddress(7, 4, "immediate", operand[1:].strip())

    register_match = _REGISTER_RE.fullmatch(operand)
    if register_match is not None:
        kind = register_match.group("kind").lower()
        return _EffectiveAddress(
            0 if kind == "d" else 1,
            int(register_match.group("number")),
        )
    if operand.lower() == "sp":
        return _EffectiveAddress(1, 7)

    match = _INDIRECT_RE.fullmatch(operand)
    if match is not None:
        unused_kind, register = _register_number(match.group("register"), line)
        return _EffectiveAddress(2, register)
    match = _POSTINC_RE.fullmatch(operand)
    if match is not None:
        unused_kind, register = _register_number(match.group("register"), line)
        return _EffectiveAddress(3, register)
    match = _PREDEC_RE.fullmatch(operand)
    if match is not None:
        unused_kind, register = _register_number(match.group("register"), line)
        return _EffectiveAddress(4, register)
    match = _INDEXED_RE.fullmatch(operand)
    if match is not None:
        register_text = match.group("register").lower()
        if register_text == "pc":
            return _EffectiveAddress(7, 2, "pc", match.group("expression"))
        unused_kind, register = _register_number(register_text, line)
        return _EffectiveAddress(
            5,
            register,
            "displacement",
            match.group("expression"),
        )
    if operand.lower().endswith(".w"):
        return _EffectiveAddress(7, 0, "absolute_word", operand[:-2])
    raise AmigaAssemblerError(f"Adressierungsart nicht unterstützt: {text}.", line)


def _split_operands(text: str) -> List[str]:
    result: List[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(text):
        if character == "(":
            depth += 1
        elif character == ")":
            depth = max(0, depth - 1)
        elif character == "," and depth == 0:
            result.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        result.append(tail)
    return result


def _word_bytes(words: Sequence[int]) -> bytes:
    return b"".join(struct.pack(">H", word & 0xFFFF) for word in words)


def _ea_words(
    ea: _EffectiveAddress,
    labels: Dict[str, int],
    extension_offset: int,
    size: str,
    line: int,
    resolve: bool,
) -> List[int]:
    return ea.extension_words(
        labels,
        extension_offset,
        size,
        line,
        resolve,
    )


_SIZE_BITS = {"b": 0x0000, "w": 0x0040, "l": 0x0080}
_MOVE_BASE = {"b": 0x1000, "w": 0x3000, "l": 0x2000}
_BRANCH_CONDITION = {
    "bra": 0x0,
    "bsr": 0x1,
    "bhi": 0x2,
    "bls": 0x3,
    "bcc": 0x4,
    "bhs": 0x4,
    "bcs": 0x5,
    "blo": 0x5,
    "bne": 0x6,
    "beq": 0x7,
    "bvc": 0x8,
    "bvs": 0x9,
    "bpl": 0xA,
    "bmi": 0xB,
    "bge": 0xC,
    "blt": 0xD,
    "bgt": 0xE,
    "ble": 0xF,
}


def _encode_instruction(
    text: str,
    offset: int,
    labels: Dict[str, int],
    line: int,
    resolve: bool,
) -> bytes:
    parts = text.strip().split(None, 1)
    mnemonic_text = parts[0].lower()
    operands = _split_operands(parts[1] if len(parts) > 1 else "")
    if "." in mnemonic_text:
        mnemonic, size = mnemonic_text.split(".", 1)
    else:
        mnemonic, size = mnemonic_text, ""

    if mnemonic == "nop" and not operands:
        return _word_bytes([0x4E71])
    if mnemonic == "rts" and not operands:
        return _word_bytes([0x4E75])

    if mnemonic in _BRANCH_CONDITION:
        if len(operands) != 1:
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet ein Ziel.", line)
        target = _parse_expression(operands[0], labels, line, resolve)
        displacement = target - (offset + 2) if resolve else 0
        _require_signed_word(displacement, line, "Sprungabstand")
        opcode = 0x6000 | (_BRANCH_CONDITION[mnemonic] << 8)
        return _word_bytes([opcode, displacement])

    if mnemonic in {"jmp", "jsr"} and len(operands) == 1:
        if _LABEL_RE.fullmatch(operands[0]):
            pseudo = "bra" if mnemonic == "jmp" else "bsr"
            return _encode_instruction(
                f"{pseudo} {operands[0]}",
                offset,
                labels,
                line,
                resolve,
            )
        ea = _parse_ea(operands[0], line)
        extension = _ea_words(ea, labels, offset + 2, "l", line, resolve)
        return _word_bytes([(0x4EC0 if mnemonic == "jmp" else 0x4E80) | ea.bits] + extension)

    if mnemonic == "moveq":
        if len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError("MOVEQ erwartet #Wert,Dn.", line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError("MOVEQ benötigt ein Datenregister.", line)
        value = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not -128 <= value <= 255:
            raise AmigaAssemblerError("MOVEQ-Wert liegt außerhalb -128..255.", line)
        return _word_bytes([0x7000 | (register << 9) | (value & 0xFF)])

    if mnemonic == "move":
        if size not in _MOVE_BASE or len(operands) != 2:
            raise AmigaAssemblerError("MOVE benötigt .B, .W oder .L und zwei Operanden.", line)
        source = _parse_ea(operands[0], line)
        destination = _parse_ea(operands[1], line)
        if destination.mode == 7:
            raise AmigaAssemblerError("MOVE-Zieladressierung wird nicht unterstützt.", line)
        source_extension = _ea_words(source, labels, offset + 2, size, line, resolve)
        destination_extension_offset = offset + 2 + 2 * len(source_extension)
        destination_extension = _ea_words(
            destination,
            labels,
            destination_extension_offset,
            size,
            line,
            resolve,
        )
        opcode = (
            _MOVE_BASE[size]
            | (destination.register << 9)
            | (destination.mode << 6)
            | source.bits
        )
        return _word_bytes([opcode] + source_extension + destination_extension)

    if mnemonic == "lea":
        if len(operands) != 2:
            raise AmigaAssemblerError("LEA erwartet Quelle,An.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "a":
            raise AmigaAssemblerError("LEA benötigt ein Adressregister als Ziel.", line)
        extension = _ea_words(source, labels, offset + 2, "l", line, resolve)
        return _word_bytes([0x41C0 | (register << 9) | source.bits] + extension)

    if mnemonic in {"tst", "clr", "neg"}:
        if size not in _SIZE_BITS or len(operands) != 1:
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt eine Größe und einen Operanden.", line)
        ea = _parse_ea(operands[0], line)
        base = {"tst": 0x4A00, "clr": 0x4200, "neg": 0x4400}[mnemonic]
        extension = _ea_words(ea, labels, offset + 2, size, line, resolve)
        return _word_bytes([base | _SIZE_BITS[size] | ea.bits] + extension)

    if mnemonic == "swap":
        if len(operands) != 1:
            raise AmigaAssemblerError("SWAP erwartet Dn.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "d":
            raise AmigaAssemblerError("SWAP erwartet ein Datenregister.", line)
        return _word_bytes([0x4840 | register])

    if mnemonic == "ext":
        if size not in {"w", "l"} or len(operands) != 1:
            raise AmigaAssemblerError("EXT erwartet .W oder .L und Dn.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "d":
            raise AmigaAssemblerError("EXT erwartet ein Datenregister.", line)
        return _word_bytes([(0x4880 if size == "w" else 0x48C0) | register])

    if mnemonic in {"add", "sub", "and", "or", "cmp"}:
        if size not in _SIZE_BITS or len(operands) != 2:
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt Größe und zwei Operanden.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt Dn als Ziel.", line)
        base = {"add": 0xD000, "sub": 0x9000, "and": 0xC000, "or": 0x8000, "cmp": 0xB000}[mnemonic]
        extension = _ea_words(source, labels, offset + 2, size, line, resolve)
        return _word_bytes([base | (register << 9) | _SIZE_BITS[size] | source.bits] + extension)

    if mnemonic == "eor":
        if size not in _SIZE_BITS or len(operands) != 2:
            raise AmigaAssemblerError("EOR benötigt Größe und zwei Operanden.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "d":
            raise AmigaAssemblerError("EOR benötigt Dn als Quelle.", line)
        destination = _parse_ea(operands[1], line)
        extension = _ea_words(destination, labels, offset + 2, size, line, resolve)
        return _word_bytes([0xB100 | (register << 9) | _SIZE_BITS[size] | destination.bits] + extension)

    immediate_bases = {
        "addi": 0x0600,
        "subi": 0x0400,
        "andi": 0x0200,
        "ori": 0x0000,
        "eori": 0x0A00,
        "cmpi": 0x0C00,
    }
    if mnemonic in immediate_bases:
        if size not in _SIZE_BITS or len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet #Wert,Ziel.", line)
        destination = _parse_ea(operands[1], line)
        immediate = _EffectiveAddress(7, 4, "immediate", operands[0][1:])
        immediate_words = _ea_words(immediate, labels, offset + 2, size, line, resolve)
        destination_offset = offset + 2 + 2 * len(immediate_words)
        extension = _ea_words(destination, labels, destination_offset, size, line, resolve)
        opcode = immediate_bases[mnemonic] | _SIZE_BITS[size] | destination.bits
        return _word_bytes([opcode] + immediate_words + extension)

    if mnemonic in {"addq", "subq"}:
        if size not in _SIZE_BITS or len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet #1..8,Ziel.", line)
        count = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not 1 <= count <= 8:
            raise AmigaAssemblerError("Quick-Konstante muss 1..8 betragen.", line)
        destination = _parse_ea(operands[1], line)
        extension = _ea_words(destination, labels, offset + 2, size, line, resolve)
        encoded_count = 0 if count == 8 else count
        opcode = (0x5100 if mnemonic == "subq" else 0x5000)
        opcode |= (encoded_count << 9) | _SIZE_BITS[size] | destination.bits
        return _word_bytes([opcode] + extension)

    if mnemonic in {"adda", "suba"}:
        if size not in {"w", "l"} or len(operands) != 2:
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet .W/.L Quelle,An.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "a":
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt An als Ziel.", line)
        base = 0xD0C0 if mnemonic == "adda" else 0x90C0
        if size == "l":
            base |= 0x0100
        extension = _ea_words(source, labels, offset + 2, size, line, resolve)
        return _word_bytes([base | (register << 9) | source.bits] + extension)

    if mnemonic in {"mulu", "muls", "divu", "divs"}:
        if size not in {"", "w"} or len(operands) != 2:
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet Quelle,Dn.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt Dn als Ziel.", line)
        base = {"mulu": 0xC0C0, "muls": 0xC1C0, "divu": 0x80C0, "divs": 0x81C0}[mnemonic]
        extension = _ea_words(source, labels, offset + 2, "w", line, resolve)
        return _word_bytes([base | (register << 9) | source.bits] + extension)

    if mnemonic in {"lsl", "lsr"}:
        if size not in {"b", "w", "l"} or len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet #1..8,Dn.", line)
        count = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not 1 <= count <= 8:
            raise AmigaAssemblerError("Schiebeweite muss 1..8 betragen.", line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError("Register-Schiebebefehl benötigt Dn.", line)
        size_bits = {"b": 0x0000, "w": 0x0040, "l": 0x0080}[size]
        encoded_count = 0 if count == 8 else count
        opcode = 0xE008 | (encoded_count << 9) | size_bits | register
        if mnemonic == "lsl":
            opcode |= 0x0100
        return _word_bytes([opcode])

    raise AmigaAssemblerError(f"68000-Befehl nicht unterstützt: {text}.", line)


def _strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def _split_label(text: str) -> Tuple[Optional[str], str]:
    match = re.match(
        r"^(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*:\s*(?P<tail>.*)$",
        text,
    )
    if match is None:
        return None, text
    return match.group("label"), match.group("tail").strip()


def _directive_parts(text: str) -> Tuple[str, str]:
    parts = text.strip().split(None, 1)
    name = parts[0].lower().lstrip(".") if parts else ""
    arguments = parts[1].strip() if len(parts) > 1 else ""
    return name, arguments


def _data_values(arguments: str) -> List[str]:
    return [item.strip() for item in _split_operands(arguments) if item.strip()]


def _item_size(
    text: str,
    offset: int,
    labels: Dict[str, int],
    line: int,
) -> int:
    name, arguments = _directive_parts(text)
    if name in {"section", "xdef", "end", "bootable"}:
        return 0
    if name == "even":
        return offset & 1
    if name in {"dc.b", "dc.w", "dc.l"}:
        unit = {"dc.b": 1, "dc.w": 2, "dc.l": 4}[name]
        return unit * len(_data_values(arguments))
    if name in {"ds.b", "ds.w", "ds.l"}:
        unit = {"ds.b": 1, "ds.w": 2, "ds.l": 4}[name]
        count = _parse_expression(arguments, labels, line, False)
        if count < 0:
            raise AmigaAssemblerError("DS-Anzahl darf nicht negativ sein.", line)
        return unit * count
    return len(_encode_instruction(text, offset, labels, line, False))


def _encode_item(
    item: _SourceItem,
    labels: Dict[str, int],
) -> Tuple[bytes, int]:
    name, arguments = _directive_parts(item.text)
    if name in {"section", "xdef", "end", "bootable"}:
        return b"", 0
    if name == "even":
        return (b"\x00" if item.offset & 1 else b""), 0
    if name in {"dc.b", "dc.w", "dc.l"}:
        unit = {"dc.b": 1, "dc.w": 2, "dc.l": 4}[name]
        output = bytearray()
        for expression in _data_values(arguments):
            value = _parse_expression(expression, labels, item.line, True)
            if unit == 1:
                output.append(value & 0xFF)
            elif unit == 2:
                output.extend(struct.pack(">H", value & 0xFFFF))
            else:
                output.extend(struct.pack(">I", value & 0xFFFFFFFF))
        return bytes(output), 0
    if name in {"ds.b", "ds.w", "ds.l"}:
        unit = {"ds.b": 1, "ds.w": 2, "ds.l": 4}[name]
        count = _parse_expression(arguments, labels, item.line, True)
        return bytes(unit * count), 0
    return (
        _encode_instruction(
            item.text,
            item.offset,
            labels,
            item.line,
            True,
        ),
        1,
    )


def _hunk_executable(code: bytes) -> bytes:
    padded_size = (len(code) + 3) & ~3
    padded_code = code + bytes(padded_size - len(code))
    long_count = padded_size // 4
    header = struct.pack(
        ">6I",
        HUNK_HEADER,
        0,
        1,
        0,
        0,
        long_count,
    )
    return (
        header
        + struct.pack(">2I", HUNK_CODE, long_count)
        + padded_code
        + struct.pack(">I", HUNK_END)
    )


def is_amiga_boot_source(source: str) -> bool:
    """Erkennt die explizite ``.bootable``-Direktive."""
    for raw_line in str(source).splitlines():
        text = _strip_comment(raw_line)
        if not text:
            continue
        unused_label, tail = _split_label(text)
        if tail and _directive_parts(tail)[0] == "bootable":
            return True
    return False


def _boot_block_checksum(block: bytes) -> int:
    """Berechnet die Amiga-Bootblock-Prüfsumme mit End-Around-Carry."""
    if len(block) != BOOT_BLOCK_SIZE:
        raise ValueError("Ein Amiga-Bootblock muss genau 1024 Bytes groß sein.")
    total = 0
    for (value,) in struct.iter_unpack(">I", block):
        previous = total
        total = (total + value) & 0xFFFFFFFF
        if total < previous:
            total = (total + 1) & 0xFFFFFFFF
    return (~total) & 0xFFFFFFFF


def _boot_loader_source(payload_size: int) -> str:
    """Erzeugt den kleinen Bootblock-Trackloader für den Nutzcode."""
    return (
        "section code,code\n"
        "xdef _start\n"
        "_start:\n"
        f"    move.l #${BOOT_PAYLOAD_ADDRESS:08X},$28(a1)\n"
        f"    move.l #${payload_size:08X},$24(a1)\n"
        f"    move.l #${BOOT_PAYLOAD_OFFSET:08X},$2C(a1)\n"
        "    move.w #$0002,$1C(a1)\n"
        "    jsr -456(a6)\n"
        "    tst.b $1F(a1)\n"
        "    bne .load_error\n"
        f"    move.l #${BOOT_PAYLOAD_ADDRESS:08X},a0\n"
        "    jmp (a0)\n"
        ".load_error:\n"
        "    moveq #-1,d0\n"
        "    rts\n"
    )


def _bootable_adf(code: bytes) -> Tuple[bytes, bytes]:
    if len(code) > MAX_BOOT_PAYLOAD_SIZE:
        raise AmigaAssemblerError(
            "Der Standalone-Nutzcode ist zu groß: "
            f"{len(code)} Bytes; erlaubt sind höchstens "
            f"{MAX_BOOT_PAYLOAD_SIZE} Bytes."
        )

    padded_size = (len(code) + 511) & ~511
    if BOOT_PAYLOAD_OFFSET + padded_size > ADF_SIZE:
        raise AmigaAssemblerError(
            "Der Standalone-Nutzcode passt nicht auf eine Amiga-DD-Diskette."
        )

    loader = assemble_amiga_source(_boot_loader_source(padded_size))
    maximum_loader_size = BOOT_BLOCK_SIZE - BOOT_CODE_OFFSET
    if len(loader.code) > maximum_loader_size:
        raise AmigaAssemblerError(
            "Interner Fehler: Der Amiga-Trackloader überschreitet den Bootblock."
        )

    boot_block = bytearray(BOOT_BLOCK_SIZE)
    boot_block[0:4] = b"DOS\0"
    struct.pack_into(">I", boot_block, 8, AMIGA_DD_ROOT_BLOCK)
    boot_block[
        BOOT_CODE_OFFSET:BOOT_CODE_OFFSET + len(loader.code)
    ] = loader.code
    struct.pack_into(">I", boot_block, 4, _boot_block_checksum(boot_block))

    adf = bytearray(ADF_SIZE)
    adf[:BOOT_BLOCK_SIZE] = boot_block
    adf[
        BOOT_PAYLOAD_OFFSET:BOOT_PAYLOAD_OFFSET + len(code)
    ] = code
    return bytes(adf), bytes(boot_block)


def assemble_amiga_source(
    source: str,
    *,
    filename: str = "<Amiga-Assembler>",
) -> AmigaProgram:
    """Assembliert 68000-Quelltext in eine native Amiga-Hunk-Datei."""
    del filename
    labels: Dict[str, int] = {}
    items: List[_SourceItem] = []
    offset = 0

    for line_number, raw_line in enumerate(source.splitlines(), 1):
        text = _strip_comment(raw_line)
        if not text:
            continue
        label, text = _split_label(text)
        if label is not None:
            key = label.casefold()
            if key in labels:
                raise AmigaAssemblerError(f"Symbol mehrfach definiert: {label}.", line_number)
            labels[key] = offset
        if not text:
            continue
        size = _item_size(text, offset, labels, line_number)
        items.append(_SourceItem(line_number, offset, text))
        offset += size

    if "_start" not in labels:
        raise AmigaAssemblerError("Einsprungmarke _start fehlt.")
    if labels["_start"] != 0:
        raise AmigaAssemblerError("_start muss am Beginn des CODE-Hunks stehen.")

    output = bytearray()
    instruction_count = 0
    for item in items:
        if len(output) != item.offset:
            raise AmigaAssemblerError("Interner Layoutfehler.", item.line)
        encoded, instructions = _encode_item(item, labels)
        output.extend(encoded)
        instruction_count += instructions

    code = bytes(output)
    return AmigaProgram(
        executable=_hunk_executable(code),
        code=code,
        entry_offset=labels["_start"],
        end_offset=len(code),
        instruction_count=instruction_count,
    )


def assemble_amiga_boot_source(
    source: str,
    *,
    filename: str = "<Amiga-Standalone-Assembler>",
) -> AmigaBootProgram:
    """Erzeugt aus ``.bootable``-Quelltext ein direkt bootfähiges ADF."""
    if not is_amiga_boot_source(source):
        raise AmigaAssemblerError(
            "Für ein Standalone-ADF fehlt die Direktive .bootable."
        )
    program = assemble_amiga_source(source, filename=filename)
    adf, boot_block = _bootable_adf(program.code)
    return AmigaBootProgram(
        adf=adf,
        boot_block=boot_block,
        code=program.code,
        entry_offset=BOOT_PAYLOAD_ADDRESS + program.entry_offset,
        end_offset=BOOT_PAYLOAD_ADDRESS + program.end_offset,
        instruction_count=program.instruction_count,
    )


__all__ = [
    "AmigaAssemblerError",
    "AmigaBootProgram",
    "AmigaProgram",
    "ADF_SIZE",
    "BOOT_BLOCK_SIZE",
    "BOOT_CODE_OFFSET",
    "BOOT_PAYLOAD_ADDRESS",
    "BOOT_PAYLOAD_OFFSET",
    "BOOT_STACK_ADDRESS",
    "MAX_BOOT_PAYLOAD_SIZE",
    "assemble_amiga_boot_source",
    "assemble_amiga_source",
    "is_amiga_boot_source",
]
