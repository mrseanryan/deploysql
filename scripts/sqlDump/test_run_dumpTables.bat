@ECHO OFF
SETLOCAL

SET PASS=xxx
SET OUTDIR=%temp%

del %TEMP%\*.sql

SET PATH_TO_PS=C:\WINDOWS\system32\WindowsPowerShell\v1.0\powershell.exe

time /t

%PATH_TO_PS% -File dumpTableSql.ps1 192.168.0.203\SQL2005DEV eLicensing_UP_ToWEB licensing %PASS% %OUTDIR%
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

time /t

GOTO DONE

:ERROR_LABEL
error_occurred!

REM type %PATH_TO_DUMP_OUT%

:DONE
echo .
echo _________________________________________
