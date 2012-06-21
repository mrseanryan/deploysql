@ECHO OFF

echo .
echo _________________________________________
echo Dumping ALL the databases to disk ...
echo _________________________________________
echo .

call run_dumpSql_to_LING_Licensing.bat
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

call run_dumpSql_eLicensing.bat
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

call run_dumpSql_eLicensing_DOWN_FromWeb.bat
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

call run_dumpSql_eLicensing_UP_ToWeb.bat
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

GOTO DONE

:ERROR_LABEL
error_occurred!

:DONE
echo .
echo _________________________________________
