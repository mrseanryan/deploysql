# Script all tables in a database
#
#Dependencies: Windows Powershell 2.0 (XP)
#
#Dump the SQL to create given tables.
#Uses SMO to properly create the sql, with FKs and constraints, just like SSMS!
#
#ref: http://stackoverflow.com/questions/21547/in-sql-server-how-do-i-generate-a-create-table-statement-for-a-given-table
#
[System.Reflection.Assembly]::LoadWithPartialName("Microsoft.SqlServer.SMO")  | out-null

# ===============================================================

if ($args.Length -ne 5)
{
    Write-Host "dumpTableSql.ps1"
    Write-Host "USAGE: <SQL Server Instance> <Database name> <User> <Password> <Output directory>"
    exit 1
}

$sqlServerInstance = $args[0]
$dbName = $args[1]

$login = $args[2]
$pass = $args[3]

$outDirPath=$args[4]
# ===============================================================
Write-Host "_____________________________________________________"
Write-Host "Dumping tables to disk from " $sqlServerInstance " - " $dbName " to " $outDirPath

# ===============================================================

$s = new-object ('Microsoft.SqlServer.Management.Smo.Server') $sqlServerInstance

$conContext = $s.ConnectionContext
$conContext.LoginSecure = $FALSE
$conContext.Login = $login
$conContext.Password = $pass

$db = $s.Databases[$dbName]

$scrp = new-object ('Microsoft.SqlServer.Management.Smo.Scripter') ($s)
$scrp.Options.AppendToFile = $False
$scrp.Options.ClusteredIndexes = $True
$scrp.Options.DriAll = $True
$scrp.Options.ScriptDrops = $False
$scrp.Options.IncludeHeaders = $False
$scrp.Options.ToFileOnly = $True
$scrp.Options.Indexes = $True
$scrp.Options.WithDependencies = $False
#$scrp.Options.AnsiFile = $False
$scrp.Options.Encoding = new-object "System.Text.ASCIIEncoding"
#$scrp.Options.FileName = $outDirPath + '\licensing_dev.Tables.SQL'

#$tablearray = @()
$iItem = 1
foreach($item in $db.Tables)
{ 
    Write-Host "Scripting table " $iItem " of " $db.Tables.Count " - " $item.Name
    #$tablearray+=@($item)
    $schema_name = $item.Schema
    $scrp.Options.FileName = $outDirPath + '\'+$schema_name+'.' + $item.Name + '.Table.sql'
    $scrp.Script(@($item))
    
    $iItem = $iItem + 1
}

Write-Host "Scripting complete"
