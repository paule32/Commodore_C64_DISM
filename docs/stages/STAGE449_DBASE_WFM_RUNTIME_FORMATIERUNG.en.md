[Deutsch](STAGE449_DBASE_WFM_RUNTIME_FORMATIERUNG.md) | [English](STAGE449_DBASE_WFM_RUNTIME_FORMATIERUNG.en.md)

# Stage 449 – Shared dBASE/WFM Runtime Value Formatting

Extends the unified `c64_dbase_runtime.dll` for both architectures with helpers such as `DBaseStringLengthN(const char*, uint32_t)` for bounded null-safe byte counts, `DBaseWfmClassifyType(uint32_t)` for NULL/string/object/numeric discrimination, and `DBaseWfmFormatValue(const ValueSlot*, char*, FormatResult*)`. The WFM event emitter uses the common type and formatting ABI instead of duplicating conversions. The existing 96-byte WFM numeric format buffer and value-slot layout are retained. Changes cover runtime builder, event code generation, and deployment; tests examine exports and data layouts, with real Windows loading treated separately.
