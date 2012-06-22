setlocal
set PYTHONPATH=..

SET DEBUG_ON=-d

REM comment this out, to turn on debugging:
SET DEBUG_ON=

SET OUTDIR=%TEMP%\dumpSql

if not exist %OUTDIR% (mkdir %OUTDIR%)

SET PATH_TO_PS=C:\WINDOWS\system32\WindowsPowerShell\v1.0\powershell.exe

time /t

dumpSqlObjectsToDisk.py  %DEBUG_ON% 192.168.0.203\SQL2005DEV licensing_dev licensing %OUTDIR% "c:\Program Files\Microsoft SQL Server\100\Tools\binn" %PATH_TO_PS%
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

time /t

echo _________________________________________
echo .
echo Results:
echo .
REM tree /f %OUTDIR%


echo .
echo _________________________________________

GOTO DONE

:ERROR_LABEL
error_occurred!

REM type %PATH_TO_DUMP_OUT%

:DONE
