[Deutsch](STAGE505_RESOURCE_CODEPAGE_LIVE_REFRESH.md) | [English](STAGE505_RESOURCE_CODEPAGE_LIVE_REFRESH.en.md)

# Stage 505 – Immediate Codepage Refresh in the Resource Editor

When the codepage combo box changes, raw RC string resources (`RCDATA`/`DLGINCLUDE`) are recompiled in memory using Unicode (UTF-16LE), UTF-8, or ASCII. The Resource Tree updates byte lengths immediately; unchanged tree structure retains the active property combo and selection. When the resource structure changes, it is rebuilt safely **after the combo signal** rather than destroying a widget while its signal handler is running. New tree construction explicitly synchronizes the selected resource, avoiding stale hex data even when no item-selection signal occurs. Windows-native resource format constraints are retained. Tests cover rapid switching and re-entrancy.
