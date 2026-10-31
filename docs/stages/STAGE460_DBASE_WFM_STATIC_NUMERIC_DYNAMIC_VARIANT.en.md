[Deutsch](STAGE460_DBASE_WFM_STATIC_NUMERIC_DYNAMIC_VARIANT.md) | [English](STAGE460_DBASE_WFM_STATIC_NUMERIC_DYNAMIC_VARIANT.en.md)

# Stage 460 – dBASE/WFM Memory Optimization for PE32 and PE32+

Adds optional WFM memory-reduction settings: **static numeric internal slots** keeps compiler-generated permanent numeric temporaries in compact numeric form, while **dynamic typed variables** lets repeated type/null assignments and full variant copies use shared helpers. Both default off. The existing WFM slot ABI remains unchanged for interoperability. The source notes compare sizes of event-form test executables and verify both PE32/PE32+ output routes. Compiler optimization must preserve observable types and values; syntax and regression tests are included.
