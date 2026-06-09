##############################################################
#  Enterprise SQL Server AI Agent - Connection Manager
#  Usage: . .\SqlAgent.ps1   (dot-source to load functions)
##############################################################

Import-Module SqlServer -ErrorAction SilentlyContinue

# Session state file for persisting connections
$script:StateFile  = "$PSScriptRoot\connections.json"
$script:Connections = @{}
$script:ActiveId    = $null

#region ── Persistence helpers ──────────────────────────────

function Save-State {
    $state = @{
        Active      = $script:ActiveId
        Connections = $script:Connections
    }
    $state | ConvertTo-Json -Depth 5 | Set-Content $script:StateFile -Encoding UTF8
}

function Load-State {
    if (Test-Path $script:StateFile) {
        $state = Get-Content $script:StateFile -Raw | ConvertFrom-Json
        $script:ActiveId = $state.Active
        $script:Connections = @{}
        foreach ($prop in $state.Connections.PSObject.Properties) {
            $script:Connections[$prop.Name] = @{
                Label            = $prop.Value.Label
                ConnectionString = $prop.Value.ConnectionString
                AddedAt          = $prop.Value.AddedAt
            }
        }
        Write-Host "✅ Loaded $($script:Connections.Count) saved connection(s)." -ForegroundColor Green
    }
}

#endregion

#region ── Connection commands ──────────────────────────────

function Add-SqlConnection {
    <#
    .SYNOPSIS
        Register a new SQL Server connection.
    .EXAMPLE
        Add-SqlConnection -Label "Prod" -ConnectionString "Server=myserver;Database=mydb;Integrated Security=True;"
        Add-SqlConnection -Label "Dev"  -ConnectionString "Server=.\SQLEXPRESS;Database=Northwind;User Id=sa;Password=pass;"
    #>
    param(
        [Parameter(Mandatory)] [string] $Label,
        [Parameter(Mandatory)] [string] $ConnectionString,
        [switch] $SetActive
    )

    $id = $Label.ToLower() -replace '\s+','-'

    $script:Connections[$id] = @{
        Label            = $Label
        ConnectionString = $ConnectionString
        AddedAt          = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    }

    if ($SetActive -or $script:Connections.Count -eq 1) {
        $script:ActiveId = $id
        Write-Host "🟢 Active connection set to: [$Label]" -ForegroundColor Cyan
    }

    Save-State
    Write-Host "✅ Connection '$Label' (id: $id) saved." -ForegroundColor Green
    Show-SqlConnections
}

function Remove-SqlConnection {
    <#
    .SYNOPSIS  Remove a saved connection by ID or label.
    .EXAMPLE   Remove-SqlConnection -Id "prod"
    #>
    param([Parameter(Mandatory)] [string] $Id)

    $Id = $Id.ToLower()
    if ($script:Connections.ContainsKey($Id)) {
        $label = $script:Connections[$Id].Label
        $script:Connections.Remove($Id)
        if ($script:ActiveId -eq $Id) { $script:ActiveId = $null }
        Save-State
        Write-Host "🗑️  Connection '$label' removed." -ForegroundColor Yellow
    } else {
        Write-Host "❌ Connection ID '$Id' not found." -ForegroundColor Red
    }
}

function Use-SqlConnection {
    <#
    .SYNOPSIS  Switch the active connection.
    .EXAMPLE   Use-SqlConnection -Id "dev"
    #>
    param([Parameter(Mandatory)] [string] $Id)

    $Id = $Id.ToLower()
    if ($script:Connections.ContainsKey($Id)) {
        $script:ActiveId = $Id
        Save-State
        $label = $script:Connections[$Id].Label
        Write-Host "🟢 Switched active connection to: [$label]" -ForegroundColor Cyan
    } else {
        Write-Host "❌ ID '$Id' not found. Use Show-SqlConnections to list available." -ForegroundColor Red
    }
}

function Show-SqlConnections {
    <#
    .SYNOPSIS  List all saved connections with active indicator.
    #>
    if ($script:Connections.Count -eq 0) {
        Write-Host "⚠️  No connections saved. Use Add-SqlConnection to add one." -ForegroundColor Yellow
        return
    }

    Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host   "║           Saved SQL Server Connections                   ║" -ForegroundColor Cyan
    Write-Host   "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

    foreach ($key in $script:Connections.Keys | Sort-Object) {
        $c      = $script:Connections[$key]
        $active = if ($key -eq $script:ActiveId) { "▶ ACTIVE" } else { "        " }
        $masked = Mask-ConnectionString $c.ConnectionString
        Write-Host "`n  $active  ID: $key" -ForegroundColor $(if ($key -eq $script:ActiveId) {'Green'} else {'Gray'})
        Write-Host "           Label : $($c.Label)"
        Write-Host "           String: $masked"
        Write-Host "           Added : $($c.AddedAt)"
    }
    Write-Host ""
}

function Test-SqlConnection {
    <#
    .SYNOPSIS  Test connectivity for a saved connection (or the active one).
    .EXAMPLE   Test-SqlConnection
               Test-SqlConnection -Id "prod"
    #>
    param([string] $Id = $script:ActiveId)

    $conn = Get-ActiveConnection $Id
    if (-not $conn) { return }

    Write-Host "🔌 Testing connection: [$($conn.Label)]..." -ForegroundColor Cyan
    try {
        $result = Invoke-Sqlcmd -ConnectionString $conn.ConnectionString `
                                -Query "SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName, @@VERSION AS Version" `
                                -ErrorAction Stop
        Write-Host "✅ Connected!" -ForegroundColor Green
        Write-Host "   Server  : $($result.ServerName)"
        Write-Host "   Database: $($result.DatabaseName)"
        Write-Host "   Version : $($result.Version -split "`n" | Select-Object -First 1)"
    } catch {
        Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

#endregion

#region ── Query execution ──────────────────────────────────

function Invoke-SqlAgentQuery {
    <#
    .SYNOPSIS  Execute a READ-ONLY T-SQL query on the active (or specified) connection.
    .EXAMPLE
        Invoke-SqlAgentQuery -Query "SELECT TOP 10 * FROM Sales.Orders"
        Invoke-SqlAgentQuery -Query "SELECT ..." -Id "dev"
    #>
    param(
        [Parameter(Mandatory)] [string] $Query,
        [string] $Id = $script:ActiveId,
        [int]    $MaxRows = 500
    )

    # Security check – block destructive commands
    $blocked = @('\bDROP\b','\bTRUNCATE\b','\bDELETE\b','\bUPDATE\b',
                 '\bALTER\b','\bCREATE\b','\bEXEC\b','\bxp_cmdshell\b','\bBULK\s+INSERT\b')
    foreach ($pattern in $blocked) {
        if ($Query -imatch $pattern) {
            Write-Host "🚫 BLOCKED: Query contains forbidden command ($($Matches[0])). Agent is READ-ONLY." -ForegroundColor Red
            return
        }
    }

    $conn = Get-ActiveConnection $Id
    if (-not $conn) { return }

    Write-Host "`n⚙️  Executing on [$($conn.Label)]..." -ForegroundColor Cyan
    try {
        $results = Invoke-Sqlcmd -ConnectionString $conn.ConnectionString `
                                 -Query $Query `
                                 -MaxCharLength 4000 `
                                 -ErrorAction Stop

        if ($results) {
            $count = @($results).Count
            Write-Host "✅ $count row(s) returned.`n" -ForegroundColor Green
            $results | Select-Object -First $MaxRows | Format-Table -AutoSize
        } else {
            Write-Host "✅ Query executed. No rows returned." -ForegroundColor Green
        }

        # Log to history
        Add-QueryHistory -ConnectionId $Id -Query $Query -Status "Success"
    } catch {
        Write-Host "❌ Query failed: $($_.Exception.Message)" -ForegroundColor Red
        Add-QueryHistory -ConnectionId $Id -Query $Query -Status "Error: $($_.Exception.Message)"
    }
}

function Get-SqlSchema {
    <#
    .SYNOPSIS  Discover tables/views/columns in the active database.
    .EXAMPLE
        Get-SqlSchema
        Get-SqlSchema -SchemaName "Sales"
        Get-SqlSchema -TableName "Orders"
    #>
    param(
        [string] $SchemaName,
        [string] $TableName,
        [string] $Id = $script:ActiveId
    )

    $filter = "1=1"
    if ($SchemaName) { $filter += " AND t.TABLE_SCHEMA = '$SchemaName'" }
    if ($TableName)  { $filter += " AND t.TABLE_NAME  LIKE '%$TableName%'" }

    $q = @"
SELECT
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    t.TABLE_TYPE,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH AS MAX_LEN,
    c.IS_NULLABLE,
    c.COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.TABLES  t
JOIN INFORMATION_SCHEMA.COLUMNS c
  ON c.TABLE_SCHEMA = t.TABLE_SCHEMA
 AND c.TABLE_NAME   = t.TABLE_NAME
WHERE $filter
ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
"@
    Invoke-SqlAgentQuery -Query $q -Id $Id
}

function Get-QueryHistory {
    <#
    .SYNOPSIS  Show recent query history for this session.
    #>
    $histFile = "$PSScriptRoot\query_history.json"
    if (Test-Path $histFile) {
        $h = Get-Content $histFile -Raw | ConvertFrom-Json
        $h | Select-Object -Last 20 | Format-Table -AutoSize
    } else {
        Write-Host "No query history yet." -ForegroundColor Yellow
    }
}

#endregion

#region ── Internal helpers ─────────────────────────────────

function Get-ActiveConnection {
    param([string] $Id = $script:ActiveId)
    if (-not $Id) {
        Write-Host "⚠️  No active connection. Use Add-SqlConnection or Use-SqlConnection first." -ForegroundColor Yellow
        return $null
    }
    if (-not $script:Connections.ContainsKey($Id)) {
        Write-Host "❌ Connection ID '$Id' not found." -ForegroundColor Red
        return $null
    }
    return $script:Connections[$Id]
}

function Mask-ConnectionString {
    param([string] $cs)
    # Mask password value
    $cs -replace '(Password|Pwd)\s*=\s*[^;]+', '$1=*****'
}

function Add-QueryHistory {
    param([string]$ConnectionId, [string]$Query, [string]$Status)
    $histFile = "$PSScriptRoot\query_history.json"
    $history  = if (Test-Path $histFile) { Get-Content $histFile -Raw | ConvertFrom-Json } else { @() }
    $history += [PSCustomObject]@{
        ConnectionId = $ConnectionId
        Query        = $Query -replace '\s+', ' '
        Status       = $Status
        ExecutedAt   = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    }
    $history | ConvertTo-Json -Depth 3 | Set-Content $histFile -Encoding UTF8
}

#endregion

#region ── Help ─────────────────────────────────────────────

function Show-SqlAgentHelp {
    Write-Host @"

╔══════════════════════════════════════════════════════════════════╗
║          Enterprise SQL Server AI Agent — Command Reference      ║
╚══════════════════════════════════════════════════════════════════╝

  CONNECTION MANAGEMENT
  ─────────────────────
  Add-SqlConnection    -Label "Prod" -ConnectionString "Server=...;Database=...;"
                       [-SetActive]          → Register + optionally activate

  Use-SqlConnection    -Id "prod"            → Switch active connection

  Remove-SqlConnection -Id "prod"            → Delete saved connection

  Show-SqlConnections                        → List all saved connections

  Test-SqlConnection   [-Id "prod"]          → Ping test + server info

  QUERYING
  ────────
  Invoke-SqlAgentQuery -Query "SELECT ..."   → Run a READ-ONLY query
                       [-Id "dev"]           → Override active connection
                       [-MaxRows 500]        → Limit display rows

  Get-SqlSchema        [-SchemaName "Sales"] → Discover tables & columns
                       [-TableName "Order"]

  HISTORY & HELP
  ──────────────
  Get-QueryHistory                           → Show recent query log
  Show-SqlAgentHelp                          → This help screen

  CONNECTION STRING EXAMPLES
  ──────────────────────────
  Windows Auth : Server=myserver\INST;Database=mydb;Integrated Security=True;
  SQL Auth     : Server=myserver;Database=mydb;User Id=sa;Password=secret;
  Azure SQL    : Server=tcp:myserver.database.windows.net,1433;Database=mydb;
                 Authentication=Active Directory Interactive;
  LocalDB      : Server=(localdb)\MSSQLLocalDB;Database=mydb;Integrated Security=True;

"@ -ForegroundColor Cyan
}

#endregion

# Auto-load saved state on dot-source
Load-State
Show-SqlAgentHelp
