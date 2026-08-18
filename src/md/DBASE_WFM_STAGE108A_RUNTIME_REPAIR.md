# Stage 108a - d64qt5 Runtime Repair

Stage 108 accidentally used the older ~128 KB bridge source as its base. Stage 108a restores the complete Stage-85 `d64qt5_bridge.cpp` (269207 bytes) and adds the WFM/FORM-OOP runtime functions without deleting existing code.

The repaired bridge is 275629 bytes. All 36 Stage-85 `DBaseQt*` exports remain present. Ten WFM exports are added.

The package also contains the Stage-85 `d64_workstation.cpp` and `d64_workstation.h`, because the full `.pro` file builds both bridge and workstation sources.
