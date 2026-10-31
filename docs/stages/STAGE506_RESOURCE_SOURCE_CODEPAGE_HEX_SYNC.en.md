[Deutsch](STAGE506_RESOURCE_SOURCE_CODEPAGE_HEX_SYNC.md) | [English](STAGE506_RESOURCE_SOURCE_CODEPAGE_HEX_SYNC.en.md)

# Stage 506 – Synchronize RC Source Codepage with Hex Preview

A 180 ms debounced `textChanged` timer refreshes the preview when a user edits the **current unsaved RC source**. `_refresh_source_preview()` compiles that text in memory, reselects a resource by type, ID, and language, and updates hex bytes, readable characters, and length fields for the effective codepage. `_sync_codepage_combo()` mirrors the source's `#pragma code_page(...)` in Properties while blocking combo signals to avoid feedback loops. No forced disk save is required. Existing tree selection is preserved when possible; tests cover source changes and live preview behavior.
