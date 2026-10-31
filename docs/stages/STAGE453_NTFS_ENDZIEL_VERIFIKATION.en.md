[Deutsch](STAGE453_NTFS_ENDZIEL_VERIFIKATION.md) | [English](STAGE453_NTFS_ENDZIEL_VERIFIKATION.en.md)

# Stage 453 – Verify NTFS Status of the Final dBASE Runtime DLL

Stage 453 closes a gap between successfully requesting NTFS compression and verifying the file actually installed beside the application. `compression_report` queries the real compression state, while `replace_verified_runtime` validates the final replacement after copying. `d64dbase/runtime_builder.py` uses this verified installation path. A success message must reflect the **final DLL**, not merely a temporary file or a successful API call. Windows checks should compare the physical compression attribute and file integrity; regression tests exercise both success and failure branches.

## Source code and command examples (unchanged)

```powershell
$dll = 'C:\Pfad\zur\c64_dbase_runtime.dll'
(Get-Item -LiteralPath $dll).Attributes
((Get-Item -LiteralPath $dll).Attributes -band [System.IO.FileAttributes]::Compressed) -ne 0
compact /q "$dll"
```

