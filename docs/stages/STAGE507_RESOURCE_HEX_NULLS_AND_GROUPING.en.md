[Deutsch](STAGE507_RESOURCE_HEX_NULLS_AND_GROUPING.md) | [English](STAGE507_RESOURCE_HEX_NULLS_AND_GROUPING.en.md)

# Stage 507 – Resource Hex Viewer: Zero Bytes and 8+8 Groups

The resource hex viewer always displays the full **16 original bytes per line**, with ` | ` between bytes 8 and 9. In the Unicode/UTF-16LE byte-as-character column every original byte has a position: `00` appears as `.` rather than being removed or combined with adjacent bytes. A separate **Unicode text (decoded)** column presents readable UTF-16LE text, including non-ASCII characters. This maintains the distinction between byte-accurate inspection and decoded interpretation. Tests include the 0x140 example, grouping, alignment, and unchanged underlying data.

## Source code and command examples (unchanged)

```text
00000140  64 00 72 00 FC 00 63 00 | 6B 00 74 00 20 00 68 00   d.r.ü.c.k.t. .h.  drückt h
```

