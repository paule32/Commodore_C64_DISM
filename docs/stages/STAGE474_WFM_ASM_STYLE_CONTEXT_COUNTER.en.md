[Deutsch](STAGE474_WFM_ASM_STYLE_CONTEXT_COUNTER.md) | [English](STAGE474_WFM_ASM_STYLE_CONTEXT_COUNTER.en.md)

# Stage 474 – WFM Assembly Tabs: Theme, Context Menu, Close Icon, Counter

Additional ASM editors now inherit the generated assembler's `QPalette`, keep their own `AssemblerSyntaxHighlighter`, and refresh styling when the application switches dark/light themes. Context menu actions are made consistent with the normal editor. Unsaved tabs display a red close marker and a per-tab naming counter to distinguish independent documents. Closing, saving, and tab switching preserve the right editor state. Tests validate appearance-related state and keyboard/menu routing.
