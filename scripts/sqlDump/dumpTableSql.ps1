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

$s = new-object ('Microsoft.SqlServer.Management.Smo.Server') '192.168.0.203\SQL2005DEV'

$conContext = $s.ConnectionContext
$conContext.LoginSecure = $FALSE
$conContext.Login = "licensing"
$conContext.Password = "xxx"

$db = $s.Databases['licensing_dev']

$scrp = new-object ('Microsoft.SqlServer.Management.Smo.Scripter') ($s)
$scrp.Options.AppendToFile = $True
$scrp.Options.ClusteredIndexes = $True
$scrp.Options.DriAll = $True
$scrp.Options.ScriptDrops = $False
$scrp.Options.IncludeHeaders = $False
$scrp.Options.ToFileOnly = $True
$scrp.Options.Indexes = $True
$scrp.Options.WithDependencies = $True
$scrp.Options.FileName = 'C:\Temp\licensing_dev.Tables.SQL'

$tablearray = @()
foreach($item in $db.Tables) { $tablearray+=@($item) }
$scrp.Script($tablearray)

Write-Host "Scripting complete"