[Deutsch](STAGE476_WFM_COMPILER_ASSEMBLER_PROGRESS.md) | [English](STAGE476_WFM_COMPILER_ASSEMBLER_PROGRESS.en.md)

# Stage 476 – Progress Indicator above the WFM Assembly Tabs

A progress bar above the WFM assembly tabs is hidden before a build and becomes visible when compilation or assembly starts (initial/minimum value 1). The compile maximum is computed after dBASE preprocessing, including expanded `#include` files; the WFM parser reports actual processed source lines. Assembly uses the PE32/PE64 preprocessor to expand `%include` files and derives its maximum from `MacroResult.locations`. Progress should reflect real work rather than an artificial timer. The change preserves existing compiler and editor paths, with tests for lifecycle and counts.
