# Run in an elevated PowerShell. This rule affects ALL pythonw.exe processes!
param([string]$Executable = 'pythonw.exe', [int]$DumpType = 1)
$Root = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps'
$Key = Join-Path $Root $Executable
New-Item -Path $Key -Force | Out-Null
New-ItemProperty -Path $Key -Name DumpType -Value $DumpType -PropertyType DWord -Force | Out-Null
New-ItemProperty -Path $Key -Name DumpCount -Value 10 -PropertyType DWord -Force | Out-Null
Write-Host "WER LocalDumps configured for $Executable; protect dumps containing sensitive information."
