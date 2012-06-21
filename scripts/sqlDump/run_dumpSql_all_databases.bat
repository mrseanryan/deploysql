@ECHO OFF
setlocal

echo .
echo _________________________________________
echo Dumping ALL the databases to disk ...
echo _________________________________________
echo .

set PYTHONPATH=..

SET DEBUG_ON=-d

REM comment this out, to turn on debugging:
SET DEBUG_ON=

SET DBNAMES=databaseList.csv

SET OUTDIR=%TEMP%

if not exist %OUTDIR% (dir_not_found)
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

time /t

dumpSqlObjectsToDisk.py -c %DEBUG_ON% 192.168.0.203\SQL2005DEV %DBNAMES% licensing %OUTDIR% "c:\Program Files\Microsoft SQL Server\100\Tools\binn"
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
