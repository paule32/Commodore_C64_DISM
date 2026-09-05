# d64_dism ODBC bitness bridge - Stage 41
# Reads a JSON request from stdin and writes exactly one UTF-8 JSON response.
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

function Write-BridgeJson($Object, [int]$ExitCode = 0) {
    $json = $Object | ConvertTo-Json -Compress -Depth 16
    [Console]::Out.Write($json)
    exit $ExitCode
}

function Write-BridgeStage([string]$Text) {
    # stderr ist nur fuer Diagnose. Niemals Connection-Strings/Passwoerter hier ausgeben.
    [Console]::Error.WriteLine('D64ODBC_STAGE:' + $Text)
}

function Get-RegistryView {
    if ([IntPtr]::Size -eq 4) {
        return [Microsoft.Win32.RegistryView]::Registry32
    }
    return [Microsoft.Win32.RegistryView]::Registry64
}

function Get-VisibleOdbcSources {
    $items = @()
    $platform = if ([IntPtr]::Size -eq 4) { '32-bit' } else { '64-bit' }
    try {
        Import-Module Wdac -ErrorAction Stop
        foreach ($dsn in @(Get-OdbcDsn -Platform $platform -ErrorAction Stop)) {
            $name = [string]$dsn.Name
            if (-not [string]::IsNullOrWhiteSpace($name)) {
                $items += [PSCustomObject]@{
                    name = $name
                    driver = [string]$dsn.DriverName
                    type = [string]$dsn.DsnType
                }
            }
        }
        return @($items)
    }
    catch {
        # Registry-Fallback innerhalb genau dieses PowerShell-Prozesses.
        foreach ($rootName in @('CurrentUser', 'LocalMachine')) {
            try {
                $hive = if ($rootName -eq 'CurrentUser') {
                    [Microsoft.Win32.RegistryHive]::CurrentUser
                } else {
                    [Microsoft.Win32.RegistryHive]::LocalMachine
                }
                $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey($hive, (Get-RegistryView))
                $key = $base.OpenSubKey('SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources')
                if ($null -ne $key) {
                    foreach ($name in $key.GetValueNames()) {
                        $items += [PSCustomObject]@{
                            name = [string]$name
                            driver = [string]$key.GetValue($name, '')
                            type = $(if ($rootName -eq 'CurrentUser') { 'User' } else { 'System' })
                        }
                    }
                    $key.Close()
                }
                $base.Close()
            } catch {}
        }
        return @($items)
    }
}

function Get-DsnNameFromConnectionString([string]$ConnectionString) {
    if ([string]::IsNullOrWhiteSpace($ConnectionString)) { return '' }
    $m = [regex]::Match($ConnectionString, '(?i)(?:^|;)\s*DSN\s*=\s*([^;]+)')
    if (-not $m.Success) { return '' }
    $name = $m.Groups[1].Value.Trim()
    if ($name.StartsWith('{') -and $name.EndsWith('}')) {
        $name = $name.Substring(1, $name.Length - 2)
    }
    return $name
}

function Get-DsnDetails([string]$DsnName) {
    $result = [ordered]@{
        found = $false
        name = $DsnName
        scope = ''
        driver = ''
        driver_path = ''
        dbq = ''
        dbq_exists = $null
        values = @{}
    }
    if ([string]::IsNullOrWhiteSpace($DsnName)) { return [PSCustomObject]$result }

    $view = Get-RegistryView
    foreach ($entry in @(
        @([Microsoft.Win32.RegistryHive]::CurrentUser, 'User'),
        @([Microsoft.Win32.RegistryHive]::LocalMachine, 'System')
    )) {
        $base = $null
        $key = $null
        try {
            $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey($entry[0], $view)
            $key = $base.OpenSubKey('SOFTWARE\ODBC\ODBC.INI\' + $DsnName)
            if ($null -eq $key) { continue }
            $result.found = $true
            $result.scope = [string]$entry[1]
            $vals = @{}
            foreach ($valueName in $key.GetValueNames()) {
                $vals[[string]$valueName] = [string]$key.GetValue($valueName, '')
            }
            $result.values = $vals
            foreach ($candidate in @('DriverName', 'Driver')) {
                if ($vals.ContainsKey($candidate) -and -not [string]::IsNullOrWhiteSpace([string]$vals[$candidate])) {
                    if ($candidate -eq 'Driver') {
                        $result.driver_path = [string]$vals[$candidate]
                    } else {
                        $result.driver = [string]$vals[$candidate]
                    }
                }
            }
            # Fuer dBASE sind DBQ/DEFAULTDIR die Verzeichniswerte. Ein
            # allgemeiner Anzeigename wie Database=(unbenannt) ist KEIN Pfad.
            foreach ($candidate in @('DBQ', 'DefaultDir', 'Directory', 'Path')) {
                if ($vals.ContainsKey($candidate) -and -not [string]::IsNullOrWhiteSpace([string]$vals[$candidate])) {
                    $candidateValue = ([string]$vals[$candidate]).Trim()
                    $cf = $candidateValue.ToLowerInvariant()
                    if ($cf -notin @('(unbenannt)', '<unbenannt>', 'unbenannt', '(unbekannt)', '<unbekannt>', 'unbekannt', '(unnamed)', '<unnamed>', 'unnamed', '(unknown)', '<unknown>', 'unknown')) {
                        $result.dbq = $candidateValue
                        break
                    }
                }
            }
            break
        }
        finally {
            try { if ($null -ne $key) { $key.Close() } } catch {}
            try { if ($null -ne $base) { $base.Close() } } catch {}
        }
    }

    # Der Anzeigename des Treibers steht verlaesslich in ODBC Data Sources.
    if ($result.found -and [string]::IsNullOrWhiteSpace([string]$result.driver)) {
        foreach ($hive in @([Microsoft.Win32.RegistryHive]::CurrentUser, [Microsoft.Win32.RegistryHive]::LocalMachine)) {
            $base = $null; $key = $null
            try {
                $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey($hive, $view)
                $key = $base.OpenSubKey('SOFTWARE\ODBC\ODBC.INI\ODBC Data Sources')
                if ($null -ne $key) {
                    $v = [string]$key.GetValue($DsnName, '')
                    if (-not [string]::IsNullOrWhiteSpace($v)) {
                        $result.driver = $v
                        break
                    }
                }
            } finally {
                try { if ($null -ne $key) { $key.Close() } } catch {}
                try { if ($null -ne $base) { $base.Close() } } catch {}
            }
        }
    }

    # Treiber-DLL aus ODBCINST.INI der *aktuellen Prozess-Bitness* bestimmen.
    if (-not [string]::IsNullOrWhiteSpace([string]$result.driver)) {
        $base = $null; $key = $null
        try {
            $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine, $view)
            $key = $base.OpenSubKey('SOFTWARE\ODBC\ODBCINST.INI\' + [string]$result.driver)
            if ($null -ne $key) {
                $driverPath = [string]$key.GetValue('Driver', '')
                if (-not [string]::IsNullOrWhiteSpace($driverPath)) {
                    $result.driver_path = $driverPath
                }
            }
        } finally {
            try { if ($null -ne $key) { $key.Close() } } catch {}
            try { if ($null -ne $base) { $base.Close() } } catch {}
        }
    }

    # Lokale dBase/DBF-Verzeichnisse koennen wir ohne Treiber-Aufruf pruefen.
    if (-not [string]::IsNullOrWhiteSpace([string]$result.dbq)) {
        $pathText = [string]$result.dbq
        if (-not $pathText.StartsWith('\\')) {
            try { $result.dbq_exists = [bool](Test-Path -LiteralPath $pathText) } catch { $result.dbq_exists = $null }
        }
    }
    return [PSCustomObject]$result
}

function Get-ConnectionStringValue([string]$ConnectionString, [string]$KeyName) {
    if ([string]::IsNullOrWhiteSpace($ConnectionString)) { return '' }
    try {
        $builder = New-Object System.Data.Odbc.OdbcConnectionStringBuilder
        $builder.ConnectionString = $ConnectionString
        if ($builder.ContainsKey($KeyName)) {
            return [string]$builder[$KeyName]
        }
    } catch {}
    return ''
}

function Set-ConnectionStringDbq([string]$ConnectionString, [string]$DataDirectory) {
    if ([string]::IsNullOrWhiteSpace($DataDirectory)) { return $ConnectionString }
    $builder = New-Object System.Data.Odbc.OdbcConnectionStringBuilder
    $builder.ConnectionString = $ConnectionString
    $builder['DBQ'] = $DataDirectory
    return $builder.ConnectionString
}

$conn = $null
$reader = $null
try {
    $inputJson = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($inputJson)) {
        throw 'Leere Helper-Anfrage.'
    }
    $request = $inputJson | ConvertFrom-Json
    $action = [string]$request.action
    $timeoutSeconds = 15
    try {
        if ($null -ne $request.timeout) { $timeoutSeconds = [Math]::Max(1, [int]$request.timeout) }
    } catch { $timeoutSeconds = 15 }

    if ($action -eq 'list_sources') {
        Write-BridgeJson @{
            ok = $true
            bitness = ([IntPtr]::Size * 8)
            sources = @(Get-VisibleOdbcSources)
        }
    }

    $connectionString = [string]$request.connection_string
    $requestedDbq = ''
    try { $requestedDbq = [string]$request.data_directory } catch { $requestedDbq = '' }
    if ([string]::IsNullOrWhiteSpace($requestedDbq)) {
        # Bei DSN-losem Dialogmodus steht DBQ bereits direkt im Connection-String.
        # Bei DSN-Modus existiert absichtlich kein DBQ im Connection-String.
        $requestedDbq = Get-ConnectionStringValue $connectionString 'DBQ'
    }
    $placeholderDbq = @('(unbenannt)', '<unbenannt>', 'unbenannt', '(unbekannt)', '<unbekannt>', 'unbekannt', '(unnamed)', '<unnamed>', 'unnamed', '(unknown)', '<unknown>', 'unknown')
    if (-not [string]::IsNullOrWhiteSpace($requestedDbq) -and $placeholderDbq -contains $requestedDbq.Trim().ToLowerInvariant()) {
        $requestedDbq = ''
    }
    if (-not [string]::IsNullOrWhiteSpace($requestedDbq)) {
        try { $requestedDbq = [System.IO.Path]::GetFullPath($requestedDbq) } catch {}
        # Nur ein expliziter Dialog-DBQ darf den Connection-String setzen.
        $connectionString = Set-ConnectionStringDbq $connectionString $requestedDbq
    }

    $dsnName = Get-DsnNameFromConnectionString $connectionString
    $dsnDetails = Get-DsnDetails $dsnName
    $effectiveDbq = $requestedDbq
    if ([string]::IsNullOrWhiteSpace($effectiveDbq)) {
        $effectiveDbq = Get-ConnectionStringValue $connectionString 'DBQ'
    }
    if ([string]::IsNullOrWhiteSpace($effectiveDbq) -and $dsnDetails.found) {
        $effectiveDbq = [string]$dsnDetails.dbq
    }

    if ($action -eq 'probe') {
        if (-not [string]::IsNullOrWhiteSpace($dsnName) -and -not $dsnDetails.found) {
            Write-BridgeJson @{
                ok = $false
                bitness = ([IntPtr]::Size * 8)
                error = ('DSN "' + $dsnName + '" ist fuer den ' + ([IntPtr]::Size * 8) + '-Bit-ODBC-Driver-Manager nicht registriert.')
                sources = @(Get-VisibleOdbcSources)
                dsn = $dsnDetails
            } 1
        }
        if (-not [string]::IsNullOrWhiteSpace($effectiveDbq) -and -not (Test-Path -LiteralPath $effectiveDbq -PathType Container)) {
            Write-BridgeJson @{
                ok = $false
                bitness = ([IntPtr]::Size * 8)
                error = ('Der effektiv verwendete DBF-Datenbankpfad existiert nicht: ' + [string]$effectiveDbq)
                sources = @(Get-VisibleOdbcSources)
                dsn = $dsnDetails
                configured_dbq = [string]$dsnDetails.dbq
                effective_dbq = [string]$effectiveDbq
            } 1
        }
        if ($dsnDetails.found -and -not [string]::IsNullOrWhiteSpace([string]$dsnDetails.driver_path)) {
            $driverPath = [Environment]::ExpandEnvironmentVariables([string]$dsnDetails.driver_path)
            if ([System.IO.Path]::IsPathRooted($driverPath) -and -not (Test-Path -LiteralPath $driverPath)) {
                Write-BridgeJson @{
                    ok = $false
                    bitness = ([IntPtr]::Size * 8)
                    error = ('Die registrierte ODBC-Treiber-DLL wurde nicht gefunden: ' + $driverPath)
                    sources = @(Get-VisibleOdbcSources)
                    dsn = $dsnDetails
                } 1
            }
        }
        Write-BridgeJson @{
            ok = $true
            bitness = ([IntPtr]::Size * 8)
            dsn = $dsnDetails
            configured_dbq = [string]$dsnDetails.dbq
            effective_dbq = [string]$effectiveDbq
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($requestedDbq)) {
        Write-BridgeStage ('PATH_MODE=DIALOG DBQ=' + $requestedDbq)
    } elseif (-not [string]::IsNullOrWhiteSpace($dsnName)) {
        Write-BridgeStage ('PATH_MODE=DSN MANAGER=' + $dsnName + ' DBQ=' + [string]$dsnDetails.dbq)
    }
    if (-not [string]::IsNullOrWhiteSpace($effectiveDbq)) {
        Write-BridgeStage ('DBQ=' + $effectiveDbq)
    }
    Write-BridgeStage ('OPEN_BEGIN timeout=' + $timeoutSeconds + 's')
    $conn = New-Object System.Data.Odbc.OdbcConnection
    $conn.ConnectionString = $connectionString
    # WICHTIG: Der Standardwert von System.Data.Odbc ist 15 Sekunden.
    # Stage 25 beendete den gesamten Helper beim 5-s-Test bereits nach 10 s,
    # bevor ODBC seinen eigenen Timeout melden konnte.
    try { $conn.ConnectionTimeout = $timeoutSeconds } catch {}

    try {
        $conn.Open()
        Write-BridgeStage 'OPEN_OK'
    }
    catch {
        Write-BridgeStage ('OPEN_ERROR ' + $_.Exception.GetType().FullName)
        Write-BridgeJson @{
            ok = $false
            bitness = ([IntPtr]::Size * 8)
            error = $_.Exception.Message
            sources = @(Get-VisibleOdbcSources)
            dsn = $dsnDetails
            connection_timeout = $timeoutSeconds
        } 1
    }

    if ($action -eq 'test') {
        $conn.Close()
        $conn = $null
        Write-BridgeJson @{
            ok = $true
            bitness = ([IntPtr]::Size * 8)
            dsn = $dsnDetails
            connection_timeout = $timeoutSeconds
        }
    }

    if ($action -ne 'execute') {
        throw ('Unbekannte Helper-Aktion: ' + $action)
    }

    $cmd = $conn.CreateCommand()
    $cmd.CommandText = [string]$request.sql
    try { $cmd.CommandTimeout = $timeoutSeconds } catch {}
    if ($null -ne $request.parameters) {
        foreach ($value in @($request.parameters)) {
            $parameter = $cmd.CreateParameter()
            if ($null -eq $value) {
                $parameter.Value = [DBNull]::Value
            } else {
                $parameter.Value = $value
            }
            [void]$cmd.Parameters.Add($parameter)
        }
    }

    $reader = $cmd.ExecuteReader()
    $columns = @()
    for ($i = 0; $i -lt $reader.FieldCount; $i++) {
        $columns += [string]$reader.GetName($i)
    }

    $rows = @()
    while ($reader.Read()) {
        $row = @()
        for ($i = 0; $i -lt $reader.FieldCount; $i++) {
            if ($reader.IsDBNull($i)) {
                $row += $null
                continue
            }
            $value = $reader.GetValue($i)
            if ($value -is [byte[]]) {
                $row += [Convert]::ToBase64String($value)
            } elseif ($value -is [DateTime]) {
                $row += $value.ToString('o')
            } else {
                $row += $value
            }
        }
        $rows += ,$row
    }
    $rowCount = $reader.RecordsAffected
    $reader.Close()
    $reader = $null
    $conn.Close()
    $conn = $null

    Write-BridgeJson @{
        ok = $true
        bitness = ([IntPtr]::Size * 8)
        columns = $columns
        rows = $rows
        rowcount = $rowCount
        dsn = $dsnDetails
    }
}
catch {
    try { if ($null -ne $reader) { $reader.Close() } } catch {}
    try { if ($null -ne $conn) { $conn.Close() } } catch {}
    Write-BridgeJson @{ ok = $false; bitness = ([IntPtr]::Size * 8); error = $_.Exception.Message } 1
}
