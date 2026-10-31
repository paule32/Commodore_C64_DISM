[Deutsch](STAGE452_DBASE_NTFS_WINERROR1_KORREKTUR.md) | [English](STAGE452_DBASE_NTFS_WINERROR1_KORREKTUR.en.md)

# Stage 452 – dBASE Runtime DLL: Handling WinError 1 During Packing

Addresses the case where enabling NTFS DLL compression produces `WinError 1` or related Windows failures. `d64dbase/pe_dll_pack.py` recognizes errors **1, 5, 32, 50, and 87**, looks for `compact.exe` in `%SystemRoot%\System32` before PATH, and uses volume/path checks via `GetVolumePathNameW` if normal compression paths fail. The behavior distinguishes unsupported filesystems or access issues from an invalid DLL. Tests cover fallback behavior and diagnostic messages; a real Windows target must confirm the final compression attribute.

## Source code and command examples (unchanged)

```powershell
Get-Volume -DriveLetter T | Select-Object DriveLetter, FileSystem
fsutil fsinfo volumeinfo T:
```

