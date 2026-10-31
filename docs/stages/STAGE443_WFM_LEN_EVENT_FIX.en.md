[Deutsch](STAGE443_WFM_LEN_EVENT_FIX.md) | [English](STAGE443_WFM_LEN_EVENT_FIX.en.md)

# Stage 443 – WFM Event Assembler: LEN as a Runtime Expression

A reported WFM event compilation problem showed that `LEN()` was not handled as a true typed runtime expression in this path. Stage 443 adds a dedicated WFM expression generator and implements string-length computation for UTF-8-backed WFM strings. It supports uses such as `STORE LEN(Text) TO N` and compositions in event code rather than only compile-time literals. Stage-441 trimming helpers (`LTRIM`, `RTRIM`, `TRIM`) are also connected to this WFM expression path. Unsupported expressions continue to report errors. The source and tests distinguish the confirmed code change from validation still requiring the real Qt/Windows runtime.
