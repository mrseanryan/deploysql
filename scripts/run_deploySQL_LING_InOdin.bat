@ECHO OFF

SETLOCAL


REM using a relative path, which will work on an Odin dev box, AND in production (as build script uses the same relative path)
SET PATH_TO_NEW_SQL_DIR=%PATH_TO_COMREG%\LING\sql\database_scripts\

SET PATH_TO_DUMP_OUT=%PATH_TO_NEW_SQL_DIR%originalSqlObjects.sql
SET PATH_TO_NEW_RESULTS=%PATH_TO_NEW_SQL_DIR%newSQLresults.txt

REM WinXP + SQL SERVER 2005:
REM SET PATH_TO_SQLCMD_DIR=c:\Progra~1\MI6841~1\90\Tools\Binn\\

REM SQL Server 2008 client:
SET PATH_TO_SQLCMD_DIR=c:\Program Files\Microsoft SQL Server\100\Tools\binn

REM for Windows7 + SQLSERVER2008:
REM SET PATH_TO_SQLCMD_DIR=c:\Progra~1\MICROS~4\100\Tools\Binn\\

REM Settings for dev database:
SET SERVER=192.168.0.203\SQL2005DEV
REM SET SERVER=SERVER\SQLSERVER_2005
SET DBNAME=licensing_dev

echo deploying SQL scripts:
DeploySQL.py  %SERVER% %DBNAME% licensing %PATH_TO_NEW_SQL_DIR%\..\scripts\list_of_SQL_scripts_to_deploy.csv   %PATH_TO_DUMP_OUT%		%PATH_TO_NEW_SQL_DIR%		%PATH_TO_NEW_RESULTS%		"%PATH_TO_SQLCMD_DIR%"
IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

REM echo backup of original SQL:
REM type %PATH_TO_DUMP_OUT%
REM IF %ERRORLEVEL% NEQ 0 (GOTO ERROR_LABEL)

GOTO DONE

:ERROR_LABEL
error_occurred!

REM type %PATH_TO_DUMP_OUT%

:DONE
