[Deutsch](STAGE442_MATHE_ROEMISCHE_ZAHLEN_QPLAINTEXT.md) | [English](STAGE442_MATHE_ROEMISCHE_ZAHLEN_QPLAINTEXT.en.md)

# Stage 442 – Mathematics: Roman Numerals in a Qt Text View

Adds **Roman Numerals** under Mathematics → Facts → Numbers. The right side uses a read-only, selectable Qt text widget rather than a painted diagram, with a centered blue heading, textual separator lines, `I V X L C D M` and values `1 5 10 50 100 500 1000`. A three-part table presents 1–20, 21–40, and further numbers. Text alignment and tab stops are handled through `QTextCharFormat` and `QTextBlockFormat`. Users can copy the displayed information but cannot edit it. The change includes structural tests and retains other mathematics pages.
