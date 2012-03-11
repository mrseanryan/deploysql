REM @ECHO OFF

REM script to copy new SQL to a temp DEPLOY directory, to make it easy to deploy SQL

REM TODO - replace this with a proper installer (InnoSetup) that reads from the database_scripts directory

SETLOCAL

SET DEST_DIR=%TEMP%\temp.deploy.me

IF NOT EXIST %DEST_DIR% (MKDIR %DEST_DIR%)

REM TODO make the Py script look in current dir, if not an absolute path
SET SCRIPT_DIR=..\scripts
SET CSV_FILENAME=%SCRIPT_DIR%\example_list_of_SQL_scripts_to_deploy.csv

SET DEST_DIR_PARENT=%DEST_DIR%

SET DEST_DIR=%DEST_DIR%\sql

IF NOT EXIST %DEST_DIR% (MKDIR %DEST_DIR%)

del /Q %DEST_DIR%\*.*

SET DEST_DIR_DATABASE_SCRIPTS=%DEST_DIR%\database_scripts
IF NOT EXIST %DEST_DIR_DATABASE_SCRIPTS% (MKDIR %DEST_DIR_DATABASE_SCRIPTS%)

SET DEST_DIR_SCRIPTS=%DEST_DIR%\scripts
IF NOT EXIST %DEST_DIR_SCRIPTS% (MKDIR %DEST_DIR_SCRIPTS%)


REM TODO make a nice py script to read from a CSV file instead
SET SCRIPT_SRC=%SCRIPT_DIR%
SET SCRIPT_SRC_SQL=%SCRIPT_DIR%\..\database_scripts

echo ____________________________________________________________________________________
echo Copying deploy scripts ...
xcopy /Y		%SCRIPT_SRC%\*.csv					%DEST_DIR_SCRIPTS%\
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

xcopy /Y		%SCRIPT_SRC%\*.py													%DEST_DIR_SCRIPTS%\
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

xcopy /Y		%SCRIPT_SRC%\run_deploySQL.bat											%DEST_DIR_SCRIPTS%\
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

echo ____________________________________________________________________________________
echo Copying SQL scripts ...

pushd %SCRIPT_DIR%
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)
CopySQLtoDeploy.py %CSV_FILENAME%          %SCRIPT_SRC_SQL%\     %DEST_DIR_DATABASE_SCRIPTS%\
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)
popd

REM *** ADD YOUR MODIFIED SQL SCRIPTS TO THE CSV FILE ***

echo ____________________________________________________________________________________
echo Listing the files to deploy:
tree /f %DEST_DIR_PARENT%
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

REM this causes CI build to freeze: explorer %DEST_DIR_PARENT%
REM IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

GOTO DONE

:ERROR_LABEL
error_occurred!

:DONE
REM pause
