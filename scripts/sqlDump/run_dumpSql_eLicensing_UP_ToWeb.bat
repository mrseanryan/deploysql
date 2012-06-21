@ECHO OFF
setlocal

set PYTHONPATH=..

SET DEBUG_ON=-d

REM comment this out, to turn on debugging:
SET DEBUG_ON=

SET OUTDIR=..\..\..\..\hg_eLicensing_DB_and_common\hg_eLicensing_DB\database\eLicensing_UP_ToWEB\database_scripts

SET DBNAME=eLicensing_UP_ToWEB

echo _________________________________________
echo .
echo Dumping %DBNAME% database to disk ...
echo .

if not exist %OUTDIR% (dir_not_found)
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

time /t

dumpSqlObjectsToDisk.py  %DEBUG_ON% 192.168.0.203\SQL2005DEV %DBNAME% licensing %OUTDIR% "c:\Program Files\Microsoft SQL Server\100\Tools\binn"   sqlDump.eLicensing_UP_ToWEB.errors.log
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

time /t

GOTO DONE

echo _________________________________________
echo .
echo Results:
echo .
tree /f %OUTDIR%

GOTO DONE

:ERROR_LABEL
error_occurred!

REM type %PATH_TO_DUMP_OUT%

:DONE
echo .
echo _________________________________________
