"""Stage 456: native WFM form's static visual properties as embedded JSON.

The Qt5 bridge owns widget construction and decoding.  Form event callbacks and
WFM methods deliberately remain native code, with their original object slots.
"""
from __future__ import annotations

import json
from pathlib import Path
import struct
import zlib

IGNORED_CLASSES = frozenset({"timer", "session", "database", "sql", "query", "datasource", "table"})


def _property_value(value):
    if isinstance(value, bool):
        return ".T." if value else ".F."
    return str(value)


def _properties(props):
    return {str(key): _property_value(value) for key, value in dict(props or {}).items()
            if str(key).casefold() not in {"left", "top", "width", "height"}}


def _geometry(props, defaults):
    values = {str(key).casefold(): value for key, value in dict(props or {}).items()}
    result = []
    for name, default in zip(("left", "top", "width", "height"), defaults):
        try:
            result.append(int(round(float(values.get(name, default)))))
        except (TypeError, ValueError):
            result.append(default)
    return result


def _font(font):
    if font is None:
        return None
    return {
        "family": str(font.family), "size": int(font.size),
        "bold": bool(font.bold), "italic": bool(font.italic),
        "underline": bool(font.underline), "strikeout": bool(font.strikeout),
    }


def form_ui_document(model):
    """Form and visual controls in the same order as the compiler handle table."""
    form_props = dict(getattr(model, "properties", {}) or {})
    elements = [{
        "path": "THIS", "geometry": _geometry(form_props, (200, 200, 400, 400)),
        "properties": _properties(form_props), "font": _font(getattr(model, "font", None)),
    }]
    controls = sorted(getattr(model, "controls", ()) or (), key=lambda c: int(c.order))
    for control in controls:
        if str(control.class_name).casefold() in IGNORED_CLASSES:
            continue
        props = dict(control.properties or {})
        # In external mode the native constructor receives empty caption; Text
        # is restored here together with the other static properties.
        values = _properties(props)
        elements.append({
            "path": str(control.path),
            "geometry": _geometry(props, (0, 0, 120, 30)),
            "properties": values, "font": _font(getattr(control, "font", None)),
        })
    return {"version": 1, "form": str(model.class_name), "elements": elements}


def encode_form_ui(model, *, compress=False):
    """Return embedded Qt-compatible bytes and the original JSON text.

    Qt's qUncompress expects a big-endian uncompressed length followed by a
    regular zlib stream (qCompress layout, not a raw DEFLATE stream).
    """
    json_text = json.dumps(form_ui_document(model), ensure_ascii=False,
                           separators=(",", ":"), sort_keys=True)
    raw = json_text.encode("utf-8")
    if not compress:
        return raw, json_text
    if len(raw) >= 0x100000000:
        raise ValueError("WFM JSON payload exceeds Qt's 32-bit length")
    return struct.pack(">I", len(raw)) + zlib.compress(raw, level=9), json_text



# Stage 461: compact, versioned, self-contained UI payload. String pooling
# removes repeated property names/values; ZigZag+LEB128 stores coordinates.
# A full JSON document can be reconstructed from each binary payload.
BINARY_MAGIC = b"WUIB\x01"
MAX_UI_BYTES = 64 * 1024 * 1024


def _varuint(value):
    value = int(value)
    if not 0 <= value <= 0xffffffff:
        raise ValueError("WFM binary integer outside uint32")
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)


def _signed(value):
    value = int(value)
    if not -(1 << 31) <= value < (1 << 31):
        raise ValueError("WFM coordinate outside int32")
    return _varuint((value << 1) ^ (value >> 31))


def binary_form_ui_from_json(json_source):
    """Serialize an existing .ui.json document, retaining every visual field."""
    doc = json.loads(json_source) if isinstance(json_source, (str, bytes, bytearray)) else json_source
    if not isinstance(doc, dict) or doc.get("version") != 1 or not isinstance(doc.get("elements"), list):
        raise ValueError("Invalid WFM UI JSON version or elements")
    pool = []
    indexes = {}

    def intern(value):
        value = str(value)
        if value not in indexes:
            indexes[value] = len(pool)
            pool.append(value)
        return indexes[value]

    form = intern(doc.get("form", ""))
    elements = []
    for element in doc["elements"]:
        geom = element["geometry"]
        if len(geom) != 4:
            raise ValueError("WFM UI geometry must have four coordinates")
        path = intern(element.get("path", ""))
        font = element.get("font")
        font_record = None
        if font is not None:
            flags = sum((1 << i) for i, flag in enumerate(
                ("bold", "italic", "underline", "strikeout")) if font.get(flag))
            font_record = (intern(font.get("family", "")), int(font.get("size", 9)), flags)
        props = sorted((str(k), str(v)) for k, v in element.get("properties", {}).items())
        prop_records = [(intern(k), intern(v)) for k, v in props]
        elements.append((path, [int(v) for v in geom], font_record, prop_records))
    out = bytearray(BINARY_MAGIC)
    out.extend(_varuint(len(pool)))
    for value in pool:
        raw = value.encode("utf-8")
        out.extend(_varuint(len(raw)))
        out.extend(raw)
    out.extend(_varuint(form))
    out.extend(_varuint(len(elements)))
    for path, geometry, font, props in elements:
        out.extend(_varuint(path))
        for coord in geometry:
            out.extend(_signed(coord))
        out.append(1 if font is not None else 0)
        if font is not None:
            out.extend(_varuint(font[0]))
            out.extend(_signed(font[1]))
            out.append(font[2])
        out.extend(_varuint(len(props)))
        for key, value in props:
            out.extend(_varuint(key))
            out.extend(_varuint(value))
    if len(out) > MAX_UI_BYTES:
        raise ValueError("WFM binary payload exceeds 64 MiB")
    return bytes(out)


def decode_form_ui_binary(data, *, _allow_trailing=False, _return_size=False):
    """Strict bounded decoder used by roundtrip tests and PE inspector."""
    data = bytes(data)
    if not data.startswith(BINARY_MAGIC) or len(data) > MAX_UI_BYTES:
        raise ValueError("Unknown or oversized WFM UI binary payload")
    cursor = len(BINARY_MAGIC)

    def read_bytes(count):
        nonlocal cursor
        if count < 0 or count > len(data) - cursor:
            raise ValueError("Truncated WFM UI binary payload")
        result = data[cursor:cursor+count]
        cursor += count
        return result

    def number():
        result = 0
        for shift in (0, 7, 14, 21, 28):
            b = read_bytes(1)[0]
            if shift == 28 and b > 15:
                raise ValueError("Invalid WFM varuint overflow")
            result |= (b & 127) << shift
            if not (b & 128):
                return result
        raise ValueError("Invalid WFM varuint")

    def signed():
        n = number()
        return (n >> 1) ^ -(n & 1)

    count = number()
    if count > 1_000_000:
        raise ValueError("Too many WFM strings")
    pool = [read_bytes(number()).decode("utf-8") for _ in range(count)]

    def string():
        index = number()
        if index >= len(pool):
            raise ValueError("Invalid WFM string index")
        return pool[index]

    form = string()
    item_count = number()
    if item_count > 100000:
        raise ValueError("Too many WFM UI elements")
    elements = []
    for _ in range(item_count):
        path = string()
        geometry = [signed() for i in range(4)]
        font_present = read_bytes(1)[0]
        if font_present not in (0, 1):
            raise ValueError("Invalid WFM font marker")
        font = None
        if font_present:
            family = string()
            size = signed()
            flags = read_bytes(1)[0]
            if flags & 0xf0:
                raise ValueError("Invalid WFM font flags")
            font = {"family": family, "size": size,
                    "bold": bool(flags & 1), "italic": bool(flags & 2),
                    "underline": bool(flags & 4), "strikeout": bool(flags & 8)}
        num_props = number()
        if num_props > 100000:
            raise ValueError("Too many WFM properties")
        props = {string(): string() for i in range(num_props)}
        elements.append({"path": path, "geometry": geometry,
                         "font": font, "properties": props})
    if cursor != len(data) and not _allow_trailing:
        raise ValueError("WFM binary payload contains trailing bytes")
    doc = {"version": 1, "form": form, "elements": elements}
    return (doc, cursor) if _return_size else doc


def select_form_ui_payload(json_text, *, store_binary=False, compress=False):
    """Return (payload, selected-format, raw-binary-or-None).

    With both options on, compare the actual *compressed* Qt-compatible blobs.
    In a tie the original JSON is preferred for backward compatibility.
    """
    raw = json_text.encode("utf-8")
    binary = binary_form_ui_from_json(json_text) if store_binary else None

    def qt_compress(block):
        if len(block) >= 0x100000000:
            raise ValueError("WFM UI payload exceeds Qt length limit")
        return struct.pack(">I", len(block)) + zlib.compress(block, level=9)

    if not store_binary:
        return (qt_compress(raw) if compress else raw), "json", None
    if not compress:
        return binary, "binary", binary
    json_packed, binary_packed = qt_compress(raw), qt_compress(binary)
    if len(binary_packed) < len(json_packed):
        return binary_packed, "binary", binary
    return json_packed, "json", binary


def encode_form_ui_smart(model, *, store_binary=False, compress=False):
    """Stage-461 wrapper preserving the Stage-456 JSON sidecar contract."""
    _unused, json_text = encode_form_ui(model, compress=False)
    payload, selected, binary = select_form_ui_payload(
        json_text, store_binary=store_binary, compress=compress)
    return payload, json_text, binary, selected


def write_form_ui_bin(filename, json_text):
    """Convert a .ui.json document into a .ui.bin alongside an existing WFM."""
    path = Path(str(filename or ""))
    if path.suffix.casefold() != ".wfm" or not path.is_file():
        return None
    binary_path = path.with_name(path.stem + ".ui.bin")
    binary_path.write_bytes(binary_form_ui_from_json(json_text))
    return binary_path


def convert_form_ui_json_file(source, destination=None):
    """Explicit offline conversion of an existing .ui.json file to .ui.bin."""
    source = Path(source)
    if not source.name.casefold().endswith(".ui.json"):
        raise ValueError("Expected a .ui.json source")
    target = Path(destination) if destination else source.with_name(source.name[:-5] + ".bin")
    target.write_bytes(binary_form_ui_from_json(source.read_text(encoding="utf-8")))
    return target

def write_form_ui_json(filename, json_text):
    """Persist a per-form readable JSON sidecar only for existing WFM source files."""
    path = Path(str(filename or ""))
    if path.suffix.casefold() != ".wfm" or not path.is_file():
        return None
    sidecar = path.with_name(path.stem + ".ui.json")
    sidecar.write_text(json.dumps(json.loads(json_text), ensure_ascii=False, indent=2)
                       + "\n", encoding="utf-8")
    return sidecar


def find_embedded_form_ui(image: bytes, *, max_size=16 * 1024 * 1024):
    """Inspect a linked (optionally .text-packed) PE image for Stage-456 UI JSON.

    This reads the bytes already embedded into the PE data section. The JSON
    sidecar is *not* a separate PE resource or a file inside the executable.
    Return dictionaries with file offset, compression and decoded document.
    No Qt libraries or program execution are required.
    """
    image = bytes(image)
    if not image.startswith(b'MZ'):
        raise ValueError('Expected a Windows PE image')
    found, seen = [], set()

    def add(offset, compressed, raw, *, trailing=False):
        if len(raw) > max_size:
            return
        if raw.startswith(BINARY_MAGIC):
            try:
                data, used = decode_form_ui_binary(
                    raw, _allow_trailing=trailing, _return_size=True)
            except (ValueError, UnicodeDecodeError):
                return
            fmt = 'binary'
            size = used
        else:
            try:
                data = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                return
            fmt = 'json'
            size = len(raw)
        if not isinstance(data, dict) or data.get('version') != 1 or \
                'elements' not in data or 'form' not in data:
            return
        key = (offset, compressed)
        if key not in seen:
            seen.add(key)
            found.append({'offset': offset, 'compressed': compressed,
                          'format': fmt, 'json_bytes': size, 'document': data})

    # Plain JSON: canonical Stage-456 sorting starts with "elements".
    marker = b'{"elements":'
    pos = 0
    while True:
        pos = image.find(marker, pos)
        if pos < 0:
            break
        try:
            text = image[pos:pos + max_size].decode('utf8', errors='replace')
            obj, end = json.JSONDecoder().raw_decode(text)
            if isinstance(obj, dict):
                add(pos, False, json.dumps(obj, ensure_ascii=False).encode('utf8'))
        except ValueError:
            pass
        pos += len(marker)

    # Uncompressed binary: parse the versioned record until its final property.
    pos = 0
    while True:
        pos = image.find(BINARY_MAGIC, pos)
        if pos < 0:
            break
        add(pos, False, image[pos:pos + max_size], trailing=True)
        pos += len(BINARY_MAGIC)

    # Compressed UI (JSON or WUIB) uses BE32 raw size + zlib stream.
    # zlib.compress(...,9) emits the stable 78 DA stream prefix.
    for prefix in (b'\x78\xda', b'\x78\x9c'):
        pos = 0
        while True:
            pos = image.find(prefix, pos)
            if pos < 0:
                break
            start = pos - 4
            if start >= 0:
                declared = struct.unpack('>I', image[start:pos])[0]
                if 0 < declared <= max_size:
                    try:
                        decoder = zlib.decompressobj()
                        raw = decoder.decompress(image[pos:pos + declared * 2 + 4096],
                                                 max_size + 1)
                        if decoder.eof and len(raw) == declared:
                            add(start, True, raw)
                    except zlib.error:
                        pass
            pos += 2
    return found


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Inspect embedded WFM UI JSON/BIN in PE images or convert .ui.json to .ui.bin')
    parser.add_argument('source', type=Path, help='PE32/PE32+ image or a .ui.json file')
    parser.add_argument('--to-bin', action='store_true',
                        help='Convert existing .ui.json to .ui.bin without compiling')
    args = parser.parse_args()
    if args.to_bin:
        target = convert_form_ui_json_file(args.source)
        print(f"Created {target} ({target.stat().st_size} bytes)")
    else:
        entries = find_embedded_form_ui(args.source.read_bytes())
        if not entries:
            print('No embedded WFM UI payload found')
        for entry in entries:
            print(f"WFM FORM={entry['document']['form']} offset=0x{entry['offset']:X} "
                  f"format={entry['format']} source={entry['json_bytes']} bytes "
                  f"compressed={'yes' if entry['compressed'] else 'no'}")
