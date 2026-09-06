"""Stage 52 C64 self-extracting PRG packer.

The packer is deliberately independent from the BASIC compiler.  It receives
an already assembled C64 PRG, compresses only the actually loaded bytes and
builds a tiny self-extracting wrapper.  C64-CBSS is therefore not part of the
compressed stream.

Modes:
    none  - return the original image
    rle   - force RLE, even when the wrapper becomes larger
    lz    - force LZ, even when the wrapper becomes larger
    auto  - build RLE and LZ candidates and keep a packed image only if it is
            smaller than the original image

LZ search modes affect only compiler-side match search.  The 6510 decruncher
is identical for fast/balanced/maximum.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

PACKER_MODES = ("none", "rle", "lz", "auto")
PACKER_SEARCH_MODES = ("fast", "balanced", "maximum")


class C64PackerError(RuntimeError):
    pass


def normalize_packer_mode(value: str) -> str:
    text = str(value or "none").strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        "off": "none",
        "disabled": "none",
        "false": "none",
        "0": "none",
        "run_length": "rle",
        "runlength": "rle",
        "lz77": "lz",
        "lzss": "lz",
        "automatic": "auto",
    }
    text = aliases.get(text, text)
    return text if text in PACKER_MODES else "none"


def normalize_search_mode(value: str) -> str:
    text = str(value or "balanced").strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        "normal": "balanced",
        "default": "balanced",
        "max": "maximum",
        "best": "maximum",
    }
    text = aliases.get(text, text)
    return text if text in PACKER_SEARCH_MODES else "balanced"


@dataclass(frozen=True)
class C64PackerStats:
    requested_mode: str
    selected_mode: str
    search_mode: str
    original_size: int
    result_size: int
    compressed_stream_size: int = 0
    bootstrap_size: int = 0
    decruncher_size: int = 0
    temp_start: int = 0
    temp_end: int = 0
    auto_kept_original: bool = False
    message: str = ""
    # Stage 51: exact, reassemblierbarer Wrapper-Quelltext fuer den separaten
    # D64PACK-ASM-Editor.  Der Hochspeicher-Decruncher wird darin physisch als
    # .byte-Bundle gespeichert; seine symbolische Quelle folgt nur kommentiert.
    asm_source: str = ""
    # Stage 55: whether the symbolic, commented De-Cruncher source was
    # requested for the Packed-ASM editor. Runtime bytes are unaffected.
    include_decruncher_source: bool = True

    @property
    def saved_bytes(self) -> int:
        return self.original_size - self.result_size

    @property
    def ratio(self) -> float:
        if not self.original_size:
            return 1.0
        return self.result_size / self.original_size


@dataclass(frozen=True)
class _Token:
    kind: str
    literal: bytes = b""
    length: int = 0
    value: int = 0
    distance: int = 0


# ---------------------------------------------------------------------------
# Reverse-stream formats
# ---------------------------------------------------------------------------
# The decruncher reads from the end of the packed stream towards its start and
# writes the destination from high to low.  0x80 is an explicit end marker.
# 00..7f: literal run, len = control + 1
# 81..ff: RLE/LZ run/match, len = (control & 0x7f) + 2  => 3..129

_END_MARKER = 0x80
_MAX_LITERAL = 128
_MAX_MATCH = 129


def _serialize_tokens(tokens: Sequence[_Token], mode: str) -> bytes:
    serialized: List[bytes] = []
    for token in tokens:
        if token.kind == "literal":
            if not 1 <= len(token.literal) <= _MAX_LITERAL:
                raise C64PackerError("Interner Packerfehler: ungültige Literal-Länge.")
            # Decoder reads bytes backwards, therefore store the reverse of the
            # decoder order before the control byte.
            serialized.append(token.literal[::-1] + bytes((len(token.literal) - 1,)))
        elif mode == "rle" and token.kind == "run":
            if not 3 <= token.length <= _MAX_MATCH:
                raise C64PackerError("Interner Packerfehler: ungültige RLE-Länge.")
            ctrl = 0x80 | (token.length - 2)
            serialized.append(bytes((token.value & 0xFF, ctrl)))
        elif mode == "lz" and token.kind == "match":
            if not 3 <= token.length <= _MAX_MATCH:
                raise C64PackerError("Interner Packerfehler: ungültige LZ-Länge.")
            if not 1 <= token.distance <= 0xFFFF:
                raise C64PackerError("Interner Packerfehler: ungültige LZ-Distanz.")
            ctrl = 0x80 | (token.length - 2)
            serialized.append(bytes((token.distance & 0xFF, token.distance >> 8, ctrl)))
        else:
            raise C64PackerError("Interner Packerfehler: unbekannter Token-Typ.")
    # First decoded token must be physically last in the stream.  The marker is
    # physically first and is therefore read after the last token.
    return bytes((_END_MARKER,)) + b"".join(reversed(serialized))


def _compress_rle(data: bytes) -> bytes:
    rev = data[::-1]
    tokens: List[_Token] = []
    literals = bytearray()

    def flush_literals() -> None:
        nonlocal literals
        while literals:
            chunk = bytes(literals[:_MAX_LITERAL])
            del literals[:_MAX_LITERAL]
            tokens.append(_Token("literal", literal=chunk))

    i = 0
    n = len(rev)
    while i < n:
        run = 1
        while i + run < n and run < _MAX_MATCH and rev[i + run] == rev[i]:
            run += 1
        if run >= 3:
            flush_literals()
            tokens.append(_Token("run", length=run, value=rev[i]))
            i += run
            continue
        literals.append(rev[i])
        i += 1
        if len(literals) >= _MAX_LITERAL:
            flush_literals()
    flush_literals()
    return _serialize_tokens(tokens, "rle")


def _candidate_limit(search_mode: str) -> int:
    return {"fast": 12, "balanced": 48, "maximum": 128}[normalize_search_mode(search_mode)]


def _best_lz_matches(rev: bytes, search_mode: str) -> Tuple[List[int], List[int]]:
    """Return best match length and distance at every position in reversed data."""
    n = len(rev)
    best_len = [0] * n
    best_dist = [0] * n
    positions: Dict[bytes, List[int]] = {}
    limit = _candidate_limit(search_mode)

    for i in range(n):
        if i + 2 >= n:
            continue
        key = rev[i:i + 3]
        candidates = positions.get(key, ())
        longest = 0
        distance = 0
        # Recent matches tend to have smaller distances and are usually better
        # for generated 6502 code.  The stream still carries a full 16-bit
        # distance, so this is a search-speed choice, not a format restriction.
        for j in reversed(candidates[-limit:]):
            dist = i - j
            if dist <= 0 or dist > 0xFFFF:
                continue
            max_len = min(_MAX_MATCH, n - i)
            length = 3
            while length < max_len and rev[i + length] == rev[j + length]:
                length += 1
            if length > longest:
                longest = length
                distance = dist
                if longest == max_len:
                    break
        if longest >= 3:
            best_len[i] = longest
            best_dist[i] = distance
        bucket = positions.setdefault(key, [])
        bucket.append(i)
        # Bound retained history as well; an old position farther than 65535
        # can never be encoded by this format.
        while bucket and i - bucket[0] > 0xFFFF:
            del bucket[0]
    return best_len, best_dist


def _lz_tokens_greedy(rev: bytes, search_mode: str) -> List[_Token]:
    best_len, best_dist = _best_lz_matches(rev, search_mode)
    n = len(rev)
    tokens: List[_Token] = []
    literals = bytearray()

    def flush() -> None:
        nonlocal literals
        while literals:
            chunk = bytes(literals[:_MAX_LITERAL])
            del literals[:_MAX_LITERAL]
            tokens.append(_Token("literal", literal=chunk))

    i = 0
    lazy = normalize_search_mode(search_mode) == "balanced"
    while i < n:
        length = best_len[i]
        # One-byte lazy parsing in balanced mode.  It can trade a short current
        # match for a significantly longer match after one literal byte.
        if lazy and length >= 3 and i + 1 < n and best_len[i + 1] > length + 1:
            length = 0
        if length >= 3:
            flush()
            tokens.append(_Token("match", length=length, distance=best_dist[i]))
            i += length
        else:
            literals.append(rev[i])
            i += 1
            if len(literals) >= _MAX_LITERAL:
                flush()
    flush()
    return tokens


def _lz_tokens_maximum(rev: bytes) -> List[_Token]:
    """Dynamic-programming parser minimizing packed-stream bytes."""
    best_len, best_dist = _best_lz_matches(rev, "maximum")
    n = len(rev)
    inf = 1 << 60
    dp = [inf] * (n + 1)
    choice: List[Tuple[str, int]] = [("", 0)] * (n + 1)
    dp[n] = 0

    for i in range(n - 1, -1, -1):
        # Literal token: N data bytes + one control byte.
        max_lit = min(_MAX_LITERAL, n - i)
        best_cost = inf
        best_choice = ("literal", 1)
        for length in range(1, max_lit + 1):
            cost = length + 1 + dp[i + length]
            if cost < best_cost:
                best_cost = cost
                best_choice = ("literal", length)
        # LZ match token always costs three bytes.
        max_match = best_len[i]
        if max_match >= 3:
            for length in range(3, max_match + 1):
                cost = 3 + dp[i + length]
                if cost < best_cost or (cost == best_cost and best_choice[0] == "literal"):
                    best_cost = cost
                    best_choice = ("match", length)
        dp[i] = best_cost
        choice[i] = best_choice

    tokens: List[_Token] = []
    i = 0
    while i < n:
        kind, length = choice[i]
        if kind == "match":
            tokens.append(_Token("match", length=length, distance=best_dist[i]))
        else:
            tokens.append(_Token("literal", literal=rev[i:i + length]))
        i += length
    return tokens


def _compress_lz(data: bytes, search_mode: str) -> bytes:
    rev = data[::-1]
    mode = normalize_search_mode(search_mode)
    if mode == "maximum":
        tokens = _lz_tokens_maximum(rev)
    else:
        tokens = _lz_tokens_greedy(rev, mode)
    return _serialize_tokens(tokens, "lz")


def decompress_stream_for_test(packed: bytes, mode: str, expected_size: int) -> bytes:
    """Pure-Python reference decoder used by regression tests."""
    mode = normalize_packer_mode(mode)
    if mode not in {"rle", "lz"}:
        raise C64PackerError("Referenzdecoder erwartet RLE oder LZ.")
    src = len(packed) - 1
    out_rev = bytearray()
    while src >= 0:
        ctrl = packed[src]
        src -= 1
        if ctrl == _END_MARKER:
            break
        if ctrl < 0x80:
            length = ctrl + 1
            for _ in range(length):
                if src < 0:
                    raise C64PackerError("Beschädigter Literal-Stream.")
                out_rev.append(packed[src])
                src -= 1
            continue
        length = (ctrl & 0x7F) + 2
        if mode == "rle":
            if src < 0:
                raise C64PackerError("Beschädigter RLE-Stream.")
            value = packed[src]
            src -= 1
            out_rev.extend(bytes((value,)) * length)
        else:
            if src < 1:
                raise C64PackerError("Beschädigter LZ-Stream.")
            hi = packed[src]
            src -= 1
            lo = packed[src]
            src -= 1
            distance = lo | (hi << 8)
            if distance <= 0 or distance > len(out_rev):
                raise C64PackerError("Ungültige LZ-Distanz im Stream.")
            for _ in range(length):
                out_rev.append(out_rev[-distance])
    result = bytes(out_rev[::-1])
    if len(result) != expected_size:
        raise C64PackerError(
            f"Decompression ergab {len(result)} statt {expected_size} Bytes."
        )
    return result


# ---------------------------------------------------------------------------
# 6510 self-extracting wrapper
# ---------------------------------------------------------------------------

_ZP_SRC_LO = 0xF7
_ZP_SRC_HI = 0xF8
_ZP_DST_LO = 0xF9
_ZP_DST_HI = 0xFA
_ZP_AUX_LO = 0xFB
_ZP_AUX_HI = 0xFC
_ZP_MATCH_LO = 0xFD
_ZP_MATCH_HI = 0xFE
_ZP_TEMP = 0xFF
_HIGH_END = 0xFFF9  # leave the six hardware-vector bytes untouched
_RETURN_RAM_START = 0xC000
_RETURN_RAM_END = 0xCFFF


def _return_stub_bytes(entry: int) -> bytes:
    """Banking-safe final trampoline executed from always-visible $Cxxx RAM.

    Stack on entry (top first): original $01, Y, X, A, P.  Restoring $01
    here is safe because $C000-$CFFF remains RAM for every normal C64 bank
    configuration.
    """
    entry &= 0xFFFF
    return bytes((
        0x68,             # PLA          original $01
        0x85, 0x01,       # STA $01
        0x68,             # PLA          original Y
        0xA8,             # TAY
        0x68,             # PLA          original X
        0xAA,             # TAX
        0x68,             # PLA          original A
        0x28,             # PLP          original status
        0x4C, entry & 0xFF, (entry >> 8) & 0xFF,  # JMP entry
    ))


def _choose_return_stub_address(occupied_end: int, entry: int) -> int:
    size = len(_return_stub_bytes(entry))
    occupied_end = int(occupied_end) & 0xFFFF
    if occupied_end < _RETURN_RAM_START:
        return _RETURN_RAM_START
    candidate = occupied_end + 1
    if _RETURN_RAM_START <= candidate and candidate + size - 1 <= _RETURN_RAM_END:
        return candidate
    raise C64PackerError(
        "D64PACK benötigt einen kleinen banking-sicheren Rücksprungbereich in "
        f"$C000-$CFFF ({size} Bytes); Programm/CBSS endet bei ${occupied_end:04X}."
    )


def _hex16(value: int) -> str:
    return f"${int(value) & 0xFFFF:04X}"


def _decrunch_source(mode: str, org: int, packed_end: int, destination_end: int, entry: int, return_stub: int) -> str:
    common_header = f"""
.nostub
.org {_hex16(org)}
.entry __d64pack_high_start
__d64pack_high_start:
    ; Stage 52: install the final return trampoline in always-visible RAM.
{chr(10).join(f"    lda #${b:02X}{chr(10)}    sta {_hex16(return_stub + i)}" for i, b in enumerate(_return_stub_bytes(entry)))}

    lda #<{_hex16(packed_end)}
    sta ${_ZP_SRC_LO:02X}
    lda #>{_hex16(packed_end)}
    sta ${_ZP_SRC_HI:02X}
    lda #<{_hex16(destination_end)}
    sta ${_ZP_DST_LO:02X}
    lda #>{_hex16(destination_end)}
    sta ${_ZP_DST_HI:02X}
__d64pack_next:
    ldy #$00
    lda (${_ZP_SRC_LO:02X}),y
    cmp #$80
    beq __d64pack_done
    bcs __d64pack_encoded
    tax
    inx
    jsr __d64pack_dec_src
__d64pack_literal_loop:
    ldy #$00
    lda (${_ZP_SRC_LO:02X}),y
    sta (${_ZP_DST_LO:02X}),y
    jsr __d64pack_dec_src
    jsr __d64pack_dec_dst
    dex
    bne __d64pack_literal_loop
    jmp __d64pack_next
__d64pack_encoded:
    and #$7F
    clc
    adc #$02
    tax
"""
    if mode == "rle":
        encoded = f"""
    jsr __d64pack_dec_src
    ldy #$00
    lda (${_ZP_SRC_LO:02X}),y
    sta ${_ZP_TEMP:02X}
    jsr __d64pack_dec_src
__d64pack_run_loop:
    lda ${_ZP_TEMP:02X}
    ldy #$00
    sta (${_ZP_DST_LO:02X}),y
    jsr __d64pack_dec_dst
    dex
    bne __d64pack_run_loop
    jmp __d64pack_next
"""
    else:
        encoded = f"""
    jsr __d64pack_dec_src
    ldy #$00
    lda (${_ZP_SRC_LO:02X}),y
    sta ${_ZP_MATCH_HI:02X}
    jsr __d64pack_dec_src
    ldy #$00
    lda (${_ZP_SRC_LO:02X}),y
    sta ${_ZP_MATCH_LO:02X}
    jsr __d64pack_dec_src
    clc
    lda ${_ZP_MATCH_LO:02X}
    adc ${_ZP_DST_LO:02X}
    sta ${_ZP_MATCH_LO:02X}
    lda ${_ZP_MATCH_HI:02X}
    adc ${_ZP_DST_HI:02X}
    sta ${_ZP_MATCH_HI:02X}
__d64pack_match_loop:
    ldy #$00
    lda (${_ZP_MATCH_LO:02X}),y
    sta (${_ZP_DST_LO:02X}),y
    jsr __d64pack_dec_match
    jsr __d64pack_dec_dst
    dex
    bne __d64pack_match_loop
    jmp __d64pack_next
"""
    common_tail = f"""
__d64pack_done:
    pla
    sta $FF
    pla
    sta $FE
    pla
    sta $FD
    pla
    sta $FC
    pla
    sta $FB
    pla
    sta $FA
    pla
    sta $F9
    pla
    sta $F8
    pla
    sta $F7
    jmp {_hex16(return_stub)}

__d64pack_dec_src:
    lda ${_ZP_SRC_LO:02X}
    bne __d64pack_dec_src_low
    dec ${_ZP_SRC_HI:02X}
__d64pack_dec_src_low:
    dec ${_ZP_SRC_LO:02X}
    rts

__d64pack_dec_dst:
    lda ${_ZP_DST_LO:02X}
    bne __d64pack_dec_dst_low
    dec ${_ZP_DST_HI:02X}
__d64pack_dec_dst_low:
    dec ${_ZP_DST_LO:02X}
    rts
"""
    if mode == "lz":
        common_tail += f"""
__d64pack_dec_match:
    lda ${_ZP_MATCH_LO:02X}
    bne __d64pack_dec_match_low
    dec ${_ZP_MATCH_HI:02X}
__d64pack_dec_match_low:
    dec ${_ZP_MATCH_LO:02X}
    rts
"""
    return common_header + encoded + common_tail + "\n"


def _byte_lines(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        lines.append("    .byte " + ", ".join(f"${value:02X}" for value in chunk))
    return "\n".join(lines)


def _bootstrap_source(
    bundle: bytes,
    temp_start: int,
    *,
    mode: str,
    search_mode: str,
    original_load: int,
    original_size: int,
    original_entry: int,
    packed_size: int,
) -> str:
    size = len(bundle)
    mode_id = {"rle": 1, "lz": 2}.get(mode, 0)
    search_id = {"fast": 1, "balanced": 2, "maximum": 3}.get(normalize_search_mode(search_mode), 0)
    return f"""
; ---------------------------------------------------------------------------
; D64PACK v1 self-extracting C64 PRG
; Stage 52: bootstrap -> high-RAM decruncher -> banking-safe return trampoline
; ---------------------------------------------------------------------------
.org $080D
.entry __d64pack_boot
__d64pack_boot:
    ; Preserve the machine state seen by the original SYS entry.
    php
    pha
    txa
    pha
    tya
    pha
    sei
    lda $01
    pha
    lda $F7
    pha
    lda $F8
    pha
    lda $F9
    pha
    lda $FA
    pha
    lda $FB
    pha
    lda $FC
    pha
    lda $FD
    pha
    lda $FE
    pha
    lda $FF
    pha
    lda #$34
    sta $01

    lda #<__d64pack_bundle
    sta ${_ZP_SRC_LO:02X}
    lda #>__d64pack_bundle
    sta ${_ZP_SRC_HI:02X}
    lda #<{_hex16(temp_start)}
    sta ${_ZP_DST_LO:02X}
    lda #>{_hex16(temp_start)}
    sta ${_ZP_DST_HI:02X}
    lda #<${size:04X}
    sta ${_ZP_AUX_LO:02X}
    lda #>${size:04X}
    sta ${_ZP_AUX_HI:02X}

__d64pack_copy_loop:
    lda ${_ZP_AUX_LO:02X}
    ora ${_ZP_AUX_HI:02X}
    beq __d64pack_copy_done
    ldy #$00
    lda (${_ZP_SRC_LO:02X}),y
    sta (${_ZP_DST_LO:02X}),y
    inc ${_ZP_SRC_LO:02X}
    bne __d64pack_src_inc_done
    inc ${_ZP_SRC_HI:02X}
__d64pack_src_inc_done:
    inc ${_ZP_DST_LO:02X}
    bne __d64pack_dst_inc_done
    inc ${_ZP_DST_HI:02X}
__d64pack_dst_inc_done:
    lda ${_ZP_AUX_LO:02X}
    bne __d64pack_count_low
    dec ${_ZP_AUX_HI:02X}
__d64pack_count_low:
    dec ${_ZP_AUX_LO:02X}
    jmp __d64pack_copy_loop

__d64pack_copy_done:
    jmp {_hex16(temp_start)}

; D64PACK v1 inspectable header (not needed by the decrunch loop itself).
__d64pack_header:
    .byte $44, $36, $34, $50
    .byte $01, ${mode_id:02X}, ${search_id:02X}, $00
    .word {_hex16(original_load)}
    .word {_hex16(original_size)}
    .word {_hex16(original_entry)}
    .word {_hex16(packed_size)}

__d64pack_bundle:
{_byte_lines(bundle)}
"""


def _inspection_source(
    wrapper_source: str,
    high_source: str,
    *,
    mode: str,
    search_mode: str,
    temp_start: int,
    temp_end: int,
    include_decruncher_source: bool = True,
) -> str:
    """Create the ASM text shown by the Stage-51 packed-code editor.

    ``wrapper_source`` is intentionally left byte-for-byte assemblable.  The
    high-RAM decruncher is already part of ``__d64pack_bundle`` as bytes; its
    symbolic source is appended *as comments only*, so assembling this editor
    produces exactly the same self-extracting PRG instead of a huge sparse
    image reaching into high RAM.
    """
    if not bool(include_decruncher_source):
        return str(wrapper_source).rstrip() + "\n"

    commented_high = "\n".join(
        "; " + line if line else ";"
        for line in str(high_source).strip("\n").splitlines()
    )
    return (
        str(wrapper_source).rstrip()
        + "\n\n"
        + "; ===========================================================================\n"
        + "; D64PACK Stage 52 - lesbare Decruncher-Quelle (NUR KOMMENTAR)\n"
        + f"; Modus       : {str(mode).upper()}\n"
        + f"; Packsuche   : {normalize_search_mode(search_mode)}\n"
        + f"; Hochspeicher: ${int(temp_start) & 0xFFFF:04X}-${int(temp_end) & 0xFFFF:04X}\n"
        + "; Der oben eingebettete __d64pack_bundle enthaelt genau diesen\n"
        + "; Decruncher bereits als Maschinencode plus den gepackten Stream.\n"
        + "; Die folgenden Zeilen sind deshalb ausnahmslos Kommentare und\n"
        + "; veraendern beim erneuten Assemblieren das PRG nicht.\n"
        + "; ===========================================================================\n"
        + commented_high
        + "\n"
    )


def _safe_assemble(assemble_func: Callable[..., object], source: str, filename: str):
    try:
        return assemble_func(source, filename=filename)
    except Exception as exc:
        raise C64PackerError(f"Interner D64PACK-Assemblerfehler ({filename}): {exc}") from exc


def _assemble_payload_bytes(assembled) -> bytes:
    prg = bytes(getattr(assembled, "prg"))
    if len(prg) < 2:
        raise C64PackerError("Assembler lieferte kein gültiges PRG.")
    return prg[2:]


def _make_candidate(
    program,
    packed: bytes,
    mode: str,
    search_mode: str,
    assemble_func: Callable[[str], object],
    *,
    include_decruncher_source: bool = True,
):
    original_prg = bytes(program.prg)
    original_payload = original_prg[2:]
    load = int(program.load_address)
    original_end = int(program.end_address)
    entry = int(program.entry_address)
    cbss_end = int(getattr(program, "symbols", {}).get("__basic_cbss_end", original_end + 1))
    occupied_end = max(original_end, cbss_end - 1)
    return_stub = _choose_return_stub_address(occupied_end, entry)

    # First pass determines the exact decruncher size.  Its instruction sizes do
    # not depend on the final high-memory address.
    probe_org = 0xC000
    probe_source = _decrunch_source(mode, probe_org, probe_org + 0x300, original_end, entry, return_stub)
    probe = _safe_assemble(assemble_func, probe_source, "<d64pack-high-probe>")
    decrunch_size = len(_assemble_payload_bytes(probe))

    bundle_size = decrunch_size + len(packed)
    temp_start = _HIGH_END - bundle_size + 1
    if temp_start <= occupied_end:
        raise C64PackerError(
            "D64PACK benötigt oberhalb des Programm-/CBSS-Bereichs temporären RAM: "
            f"benötigt ${temp_start:04X}-${_HIGH_END:04X}, Programm/CBSS endet bei ${occupied_end:04X}."
        )
    if temp_start < 0x1000:
        raise C64PackerError("D64PACK-Temporärbereich würde in kritischen Niedrig-RAM fallen.")

    packed_start = temp_start + decrunch_size
    packed_end = packed_start + len(packed) - 1
    high_source = _decrunch_source(mode, temp_start, packed_end, original_end, entry, return_stub)
    high_program = _safe_assemble(assemble_func, high_source, f"<d64pack-{mode}-high>")
    high_bytes = _assemble_payload_bytes(high_program)
    if len(high_bytes) != decrunch_size:
        # Recalculate once if assembler layout changed unexpectedly.
        decrunch_size = len(high_bytes)
        bundle_size = decrunch_size + len(packed)
        temp_start = _HIGH_END - bundle_size + 1
        packed_start = temp_start + decrunch_size
        packed_end = packed_start + len(packed) - 1
        if temp_start <= occupied_end:
            raise C64PackerError("D64PACK-Hochspeicher reicht nach finalem Layout nicht aus.")
        high_source = _decrunch_source(mode, temp_start, packed_end, original_end, entry, return_stub)
        high_program = _safe_assemble(assemble_func, high_source, f"<d64pack-{mode}-high-final>")
        high_bytes = _assemble_payload_bytes(high_program)

    bundle = high_bytes + packed
    wrapper_source = _bootstrap_source(
        bundle, temp_start,
        mode=mode,
        search_mode=search_mode,
        original_load=load,
        original_size=len(original_payload),
        original_entry=entry,
        packed_size=len(packed),
    )
    wrapper = _safe_assemble(assemble_func, wrapper_source, f"<d64pack-{mode}-wrapper>")

    # Bootstrap and source bundle must not overlap the high destination while
    # copying forward.  If they did, an explicit pack request gets a clear
    # diagnostic; auto can simply reject this candidate.
    wrapper_end = int(wrapper.end_address)
    if wrapper_end >= temp_start:
        raise C64PackerError(
            "D64PACK-Wrapper und Hochspeicher-Bundle würden sich beim Kopieren überschneiden: "
            f"Wrapper endet ${wrapper_end:04X}, Ziel beginnt ${temp_start:04X}."
        )

    bootstrap_size = len(wrapper.prg) - 2 - len(bundle)
    inspection_source = _inspection_source(
        wrapper_source,
        high_source,
        mode=mode,
        search_mode=search_mode,
        temp_start=temp_start,
        temp_end=_HIGH_END,
        include_decruncher_source=include_decruncher_source,
    )
    # Stage 51 invariant: what the user sees in the new ASM editor must really
    # reproduce the packed PRG byte-for-byte.
    inspection_program = _safe_assemble(
        assemble_func, inspection_source, f"<d64pack-{mode}-inspection>"
    )
    if bytes(inspection_program.prg) != bytes(wrapper.prg):
        raise C64PackerError(
            "Interner D64PACK-Fehler: ASM-Editor-Quelle reproduziert das gepackte PRG nicht."
        )
    return wrapper, C64PackerStats(
        requested_mode=mode,
        selected_mode=mode,
        search_mode="",
        original_size=len(original_prg),
        result_size=len(wrapper.prg),
        compressed_stream_size=len(packed),
        bootstrap_size=max(0, bootstrap_size),
        decruncher_size=len(high_bytes),
        temp_start=temp_start,
        temp_end=_HIGH_END,
        message=(
            f"D64PACK {mode.upper()}: {len(original_prg)} -> {len(wrapper.prg)} Bytes; "
            f"Stream {len(packed)} Bytes; Decruncher {len(high_bytes)} Bytes."
        ),
        asm_source=inspection_source,
        include_decruncher_source=bool(include_decruncher_source),
    )


def pack_c64_program(
    program,
    *,
    assemble_func: Callable[..., object],
    mode: str = "none",
    search_mode: str = "balanced",
    include_decruncher_source: bool = True,
):
    """Return ``(assembled_program, stats)``.

    Explicit RLE/LZ requests are never silently disabled based on size.  Auto is
    the only mode allowed to keep the original image when packing has no size
    benefit or cannot satisfy the temporary-RAM safety constraints.
    """
    requested = normalize_packer_mode(mode)
    search = normalize_search_mode(search_mode)
    original = bytes(program.prg)

    if requested == "none":
        return program, C64PackerStats(
            requested_mode="none",
            selected_mode="none",
            search_mode=search,
            original_size=len(original),
            result_size=len(original),
            message="D64PACK deaktiviert.",
        )

    payload = original[2:]
    if not payload:
        raise C64PackerError("Leeres C64-PRG kann nicht gepackt werden.")

    def candidate(kind: str):
        stream = _compress_rle(payload) if kind == "rle" else _compress_lz(payload, search)
        # Validate the compressor independently of the 6510 implementation.
        if decompress_stream_for_test(stream, kind, len(payload)) != payload:
            raise C64PackerError(f"Interne {kind.upper()}-Verifikation fehlgeschlagen.")
        wrapper, stats = _make_candidate(
            program,
            stream,
            kind,
            search,
            assemble_func,
            include_decruncher_source=include_decruncher_source,
        )
        stats = C64PackerStats(
            **{**stats.__dict__, "requested_mode": requested, "search_mode": search}
        )
        return wrapper, stats

    if requested in {"rle", "lz"}:
        return candidate(requested)

    candidates = []
    errors = []
    for kind in ("rle", "lz"):
        try:
            candidates.append(candidate(kind))
        except C64PackerError as exc:
            errors.append(f"{kind.upper()}: {exc}")
    if not candidates:
        return program, C64PackerStats(
            requested_mode="auto",
            selected_mode="none",
            search_mode=search,
            original_size=len(original),
            result_size=len(original),
            auto_kept_original=True,
            message="D64PACK Auto: kein sicherer Pack-Kandidat; Original beibehalten. " + " | ".join(errors),
        )

    wrapper, stats = min(candidates, key=lambda pair: len(pair[0].prg))
    if len(wrapper.prg) >= len(original):
        return program, C64PackerStats(
            requested_mode="auto",
            selected_mode="none",
            search_mode=search,
            original_size=len(original),
            result_size=len(original),
            auto_kept_original=True,
            message=(
                "D64PACK Auto: Packen wäre nicht kleiner "
                f"(beste Variante {stats.selected_mode.upper()} {len(wrapper.prg)} >= {len(original)} Bytes); "
                "Original beibehalten."
            ),
        )
    return wrapper, stats


__all__ = [
    "C64PackerError",
    "C64PackerStats",
    "PACKER_MODES",
    "PACKER_SEARCH_MODES",
    "decompress_stream_for_test",
    "normalize_packer_mode",
    "normalize_search_mode",
    "pack_c64_program",
]
