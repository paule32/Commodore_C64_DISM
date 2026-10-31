[Deutsch](STAGE508_RESOURCE_STRINGTABLE_CODEPAGE_HEX_VIEW.md) | [English](STAGE508_RESOURCE_STRINGTABLE_CODEPAGE_HEX_VIEW.en.md)

# Stage 508 – STRINGTABLE Hex Preview Reflects the Selected Codepage

Adds `_resource_stringtable_text_preview()` so the Resource Editor's STRINGTABLE preview reflects the selected codepage. **Unicode** shows the unchanged native resource bytes including UTF-16LE zeros; **ASCII** presents single-byte text, and **UTF-8** presents real UTF-8 sequences, for example `ü` as `C3 BC`. This is a **preview representation**—it must not silently corrupt native Windows STRINGTABLE data. Other resource types keep their own binary conventions. Tests check the supplied 346-byte STRINGTABLE sample and codepage changes.

## Source code and command examples (unchanged)

```text
Unicode:
00000150  61 00 62 00 65 00 6E 00 | 2E 00   a.b.e.n...  aben.

ASCII:
00000150  61 62 65 6E 2E                    aben.

UTF-8:
00000150  61 62 65 6E 2E                    aben.
```


```text
00000140  64 72 C3 BC 63 6B 74 20 | 68   drückt h
```

