[Deutsch](STAGE451_WFM_CONST_POOL_BRANCH_PROPERTY_NTFS_FIX.md) | [English](STAGE451_WFM_CONST_POOL_BRANCH_PROPERTY_NTFS_FIX.en.md)

# Stage 451 – WFM Code/Data Optimization and NTFS Compression Handling

Stage 451 addresses a reported NTFS `WinError 5` when **pack dll** is active and adds WFM size-optimization options. A **const pool** checkbox permits sharing repeated compile-time constants. Branch/Jump layout is optimized to avoid needlessly long sequences, and duplicate WFM property tables may be consolidated. All options must preserve the slot ABI and output correctness. The changes are tested through eight new Stage-451 cases, 107 earlier Stage-441–450 regressions, and 27 project-management tests according to the source notes. Native NTFS behavior depends on Windows filesystem support and permissions.
