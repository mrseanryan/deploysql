setlocal
set PYTHONPATH=..

SET DEBUG_ON=-d

REM comment this out, to turn on debugging:
SET DEBUG_ON=

SET OUTDIR=..\..\..\..\hg_LING_main\LINGandLicensing\LING\sql\database_scripts

echo _________________________________________
echo .
echo Dumping Licensing database to disk ...
echo .

if not exist %OUTDIR% (dir_not_found)
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

time /t

dumpSqlObjectsToDisk.py  %DEBUG_ON% 192.168.0.203\SQL2005DEV licensing_dev licensing %OUTDIR% "c:\Program Files\Microsoft SQL Server\100\Tools\binn" sqlDump.Licensing.errors.log
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
