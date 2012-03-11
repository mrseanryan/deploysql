"""
DeploySQL.py

This script is used to deploy multiple SQL scripts against a database.

The database objects are first backed up, before executing the new scripts.

USAGE:	DeploySQL.py [OPTIONS] <SQL Server> <Database name> <SQL user> <listfile of SQL scripts> <output file of original database objects> <path to directory containing NEW SQL scripts> <path to output file for new SQL script results> <path to sqlcmd.exe directory>

OPTIONS:

	-d -dummyrun		Run in 'dummy run' mode, so no changes are made to the database.
	-h -help		Show this help message.
	-w -warnings		Show warnings only (non-verbose output)
"""

#Dependencies:
#
#Python 2.7.x
#pywin32 - http://sourceforge.net/projects/pywin32/
#pyodbc - http://code.google.com/p/pyodbc/downloads/list

###############################################################
#TODO
#
# cleanup on fail: use TRANS in SQL ?
# rename original SQL file, if it already exists (to a new unique name) 
#
###############################################################

import getopt
import getpass
import re
import os
import pyodbc
import shutil
import subprocess
import win32api

from string import split

from deploySQL_common import *


###############################################################
# settings:

sqlServerInstance = ""
sqlDbName = ""
sqlUser = ""
sqlPassword = ""
sqlScriptListfilePath = ""
origOutputFilepath = ""
pathToNewSqlDir = ""
newOutputFilepath = ""

IsDummyRun = False

# unfortunately, need to use short file paths, to execute a process.  Using pywin32 to get around this, by converting path to short paths.
sqlCmd = "sqlcmd.exe"
#sqlCmdDirPath = "c:\Progra~1\MI6841~1\90\Tools\Binn\\"
sqlCmdDirPath = ""


###############################################################
#usage() - prints out the usage text, from the top of this file :-)
def usage():
    print __doc__

###############################################################
#main() - main program entry point
#args = <SQL Server>	<SQL user>	<SQL password>	<listfile of SQL scripts>		<output file of original database objects>
def main(argv):
	
	global sqlServerInstance, sqlDbName, sqlUser, sqlPassword, sqlScriptListfilePath, origOutputFilepath, pathToNewSqlDir, newOutputFilepath, sqlCmdDirPath, IsDummyRun

	try:
		opts, args = getopt.getopt(argv, "dhw", ["dummyrun", "help", "warnings"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	if(len(args) != 8):
		usage()
		sys.exit(3)
	#assign the args to variables:
	sqlServerInstance = args[0]
	sqlDbName = args[1]
	sqlUser = args[2]
	sqlScriptListfilePath = args[3]
	origOutputFilepath = args[4]
	pathToNewSqlDir = args[5]
	newOutputFilepath = args[6]
	sqlCmdDirPath = args[7]
	
	#convert sqlCmdDirPath to short file names:
	#printOut("looking for sqlcmd.exe at " + sqlCmdDirPath + "\n")
	sqlCmdDirPath = win32api.GetShortPathName(sqlCmdDirPath)
	
	for opt, arg in opts:
		if opt in ("-d", "--dummyrun"):
			IsDummyRun = True
		elif opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-w", "--warnings"):
			setLogVerbosity(LOG_WARNINGS)

	prompt = "Please enter the password for server: " + sqlServerInstance + " database: " + sqlDbName + " user: " + sqlUser + " "
	sqlPassword = getpass.getpass(prompt)

if __name__ == "__main__":
    main(sys.argv[1:])

###############################################################
#FUNCTIONS

def createSqlDumpScript(dbObjects, pathToSqlDumpScript):
	global sqlDbName
	if os.path.exists(pathToSqlDumpScript):
		os.remove(pathToSqlDumpScript)
	sqlDumpScriptFile = open(pathToSqlDumpScript, 'w+')
	sqlDumpScriptFile.write('use ' + sqlDbName + getEndline())
	sqlDumpScriptFile.write(getEndline() + "GO" + getEndline()) # need a GO before any CREATE/ALTER PROCEDURE
	sqlDumpScriptFile.write("declare @currentObjectName varchar(200)" + getEndline())
	sqlDumpScriptFile.write("select @currentObjectName = 'unknown'" + getEndline())
	sqlDumpScriptFile.write(getEndline())
	
	for dbObject in dbObjects:
		#printOut("dbObjectType = " + dbObject.dbObjectType + " sqlScriptName = " + dbObject.sqlScriptName + " sqlObjectName = " + dbObject.sqlObjectName)
		if len(dbObject.sqlObjectName) > 0:
			printOut("backing up database object " + dbObject.sqlObjectName)
			sqlExec = "exec sp_helptext '"+dbObject.sqlObjectName+"'" + getEndline()
			sqlDumpScriptFile.write(getSqlExists(dbObject.dbObjectType, dbObject.sqlObjectName, sqlExec))
		else:
			if dbObject.dbObjectType != 'SP_NEW' and dbObject.dbObjectType != 'UDF_NEW'and dbObject.dbObjectType != 'VIEW_NEW':
				addWarning("Cannot backup a SQL object for SQL script " + dbObject.sqlScriptName + " as the object name is not known")
	#add 'goto' for handling errors:
	sqlErrorGoto = "goto OK" + getEndline()
	sqlErrorGoto = sqlErrorGoto + "ERROR_CANNOT_BACKUP:" + getEndline()
	sqlErrorGoto = sqlErrorGoto + "RAISERROR (N'Cannot backup object %s, as it does not exist', 11 /*Severity*/, 1 /*State*/, @currentObjectName )" + getEndline()
	sqlErrorGoto = sqlErrorGoto + "OK:" + getEndline() #label to allow OK run to skip the error label
	sqlDumpScriptFile.write(sqlErrorGoto)
	sqlDumpScriptFile.write("GO" + getEndline())

def backupOriginalObjects(dbObjects, outputFilepath):
	global sqlServerInstance, sqlCmdPath
	#create the SQL file which will dump out the required database objects:
	pathToSqlDumpScript = "temp.dumpSQLobjects.sql"
	createSqlDumpScript(dbObjects, pathToSqlDumpScript)
	#exec the dump script:
	execSqlScript(pathToSqlDumpScript, outputFilepath)

def createConnection():
	global sqlServerInstance, sqlDbName, sqlUser, sqlPassword
	connStr = ( r'DRIVER={SQL Server};SERVER=' +
	sqlServerInstance + ';DATABASE=' + sqlDbName + ';' +
	'Uid=' + sqlUser + ";Pwd=" + sqlPassword + ";"    )
	conn = pyodbc.connect(connStr)
	return conn
	
def createCursor(dbConnection):
	cursor = dbConnection.cursor()
	return cursor
	
def execSqlScript(pathToSqlScript, outputFilepath):
	global sqlServerInstance, sqlUser, sqlPassword, sqlCmd, sqlCmdDirPath
	
	#sqlcmd.exe - ref:   http://msdn.microsoft.com/en-us/library/ms162773.aspx
	
	#sqlcmd -S (local) -U <user> -P <password>   -i dumpDatabaseObject.sql  -o originalSQL.sql
	pathToSqlScript = os.path.abspath(pathToSqlScript)
	outputFilepath = os.path.abspath(outputFilepath)
	args = "-S " + sqlServerInstance + " -U " + sqlUser + " -P " + sqlPassword + " -i " + pathToSqlScript + " -o " + outputFilepath + " -r 0 -b -m -1"    #-b is to exit on SQL error
	runExe(sqlCmd, sqlCmdDirPath, args)

def filterObjectsByDbVersion(dbVersion, dbObjects):
	dbFilteredObjects = []
	for dbObject in dbObjects:
		if(dbObject.dbVersion <= dbVersion):
			printOut("Skipping SQL script " + dbObject.sqlScriptName + " as its version " +str(dbObject.dbVersion) + " is same or older than the current database version " + str(dbVersion))
			continue
		else:
			dbFilteredObjects.append(dbObject)
	return dbFilteredObjects

def getCurrentDatabaseVersion(dbConn):
	dbVersion = 00000000
	
	cursor = createCursor(dbConn)
	cursor.execute("exec spDatabaseVersion_GetVersion")
	
	#now perform a SELECT to get the database version:
	for row in cursor:
		dbVersion = row.DbVersion
	
	cursor.close()
	return dbVersion
	
def getEndline():
	return "\r\n" #OK for Windows

def getHighestVersion(dbObjects):
	highestDbVersion = 00000000
	for dbObject in dbObjects:
		if dbObject.dbVersion > highestDbVersion:
			highestDbVersion = dbObject.dbVersion
	return long(highestDbVersion)

#get todays date, in Sql Server format
def getSQLdateToday():
	#xxx
	return "'2012-02-20 18:24:44.383'"
	
#get some SQL which checks if the given database object exists (if not, then we cannot back it up, and its a SQL error via a 'goto')
def getSqlExists(dbObjectType, sqlObjectName, sqlExec):
	existsLine = ""
	if dbObjectType == "VIEW":
		existsLine = "IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'"+sqlObjectName+"'))" + getEndline()
	elif dbObjectType == "SP":
		existsLine = "IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'"+sqlObjectName+"') AND type in (N'P', N'PC'))" + getEndline()
	elif dbObjectType == "UDF":
		existsLine = "IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'"+sqlObjectName+"') AND type in (N'FN', N'IF', N'TF', N'FS', N'FT'))"
	if len(existsLine) > 0:
		sqlExists = existsLine
		sqlExists = sqlExists + "BEGIN" + getEndline()
		sqlExists = sqlExists + sqlExec + getEndline()
		sqlExists = sqlExists + "END" + getEndline()
		#add Else as an error (since if it does not exist, then we cannot backup!)
		sqlExists = sqlExists + "ELSE" + getEndline()
		sqlExists = sqlExists + "BEGIN" + getEndline()
		sqlExists = sqlExists + "select @currentObjectName = '" + sqlObjectName + "'"+ getEndline()
		sqlExists = sqlExists + "goto ERROR_CANNOT_BACKUP" + getEndline()
		sqlExists = sqlExists + "END" + getEndline()
		return sqlExists
	else:
		raise Exception("not implemented: check for existence of database object type " + dbObjectType)

def getTempDir():
	return os.environ['TEMP'] + '\\'

def outputSummary(dbObjects, dbFilteredObjects, bDbWasUpgraded, newDbVersion, numScriptsRan):
	global IsDummyRun, origOutputFilepath
	printOut("")
	printOut("Deploy SQL results:")
	printOut( str(getNumWarnings()) + " warnings occurred" )
	printOut( str(len(dbObjects)) + " scripts were processed")
	printOut( str(numScriptsRan) + " scripts were executed")
	printOut( "Original database objects were backed up to " + origOutputFilepath)
	if(IsDummyRun):
		printOut("Dummy run - no database changes were made")
	if(bDbWasUpgraded and not IsDummyRun):
			printOut("The database has been upgraded to version " + str(newDbVersion))
	else:
		printOut("The database was NOT upgraded")
	#TODO - add more summary info

def runExe(targetScriptName, targetScriptDirPath, args):
	scriptWorkingDir = targetScriptDirPath #os.path.dirname(targetScriptPath)
	toExec = os.path.join(targetScriptDirPath, targetScriptName) + " " + args
	printOut("Running exe " + toExec)
	printOut("working dir = " + scriptWorkingDir)
	process = subprocess.Popen(toExec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = scriptWorkingDir)
	(stdout_cap, stderr_cap) = process.communicate()
	if(len(stderr_cap) > 0):
		raise Exception(str(stderr_cap))
	printOut(" >> " + str(stdout_cap));
	if(process.returncode != 0):
		raise Exception("Process returned error code:" + str(process.returncode))

def runNewSQLscripts(dbObjects, pathToNewSqlDir, outputFilepath):
	numScriptsRan = 0
	global sqlDbName, dictDbObjectTypeToSubDir, IsDummyRun
	for dbObject in dbObjects:
		#we need to specify the database name, so we copy the script, and prefix a 'use' clause
		sqlScriptCopy = getTempDir() + dbObject.sqlScriptName
		
		if IsDummyRun:
			printOut("[dummy run] - not executing SQL script " + dbObject.sqlScriptName)
		else:
			printOut("Executing SQL script " + dbObject.sqlScriptName)
		subDir = dictDbObjectTypeToSubDir[dbObject.dbObjectType]
		pathToSqlScript = os.path.join( os.path.join(pathToNewSqlDir, subDir), dbObject.sqlScriptName)
		
		#add the 'use' clause:
		sqlOrigFile = open(pathToSqlScript, 'r')
		sqlCopyFile = open(sqlScriptCopy, 'w')
		
		sqlCopyFile.write('use ' + sqlDbName + getEndline())
		sqlCopyFile.write(getEndline() + "GO" + getEndline()) # need a GO before any CREATE/ALTER PROCEDURE
	
		#now just append the rest of the original file: (with replacements)
		#we make some replacements, to help manage whether SP is CREATE or ALTER, by setting SP or SP_NEW in the listfile:
		#
		#TODO consider having a IF EXISTS ... CREATE/ALTER structure, which would be more robust
		#TODO make it easier to add new db types
		dictFindToReplace = dict()
		if(dbObject.dbObjectType == "SP"):
			dictFindToReplace["CREATE PROCEDURE"] = "ALTER PROCEDURE"
		elif(dbObject.dbObjectType == "SP_NEW"):
			dictFindToReplace["ALTER PROCEDURE"] = "CREATE PROCEDURE"
		elif(dbObject.dbObjectType == "UDF"):
			dictFindToReplace["CREATE FUNCTION"] = "ALTER FUNCTION"
		elif(dbObject.dbObjectType == "UDF_NEW"):
			dictFindToReplace["ALTER FUNCTION"] = "CREATE FUNCTION"
		elif(dbObject.dbObjectType == "VIEW"):
			dictFindToReplace["CREATE VIEW"] = "ALTER VIEW"
		elif(dbObject.dbObjectType == "VIEW_NEW"):
			dictFindToReplace["ALTER VIEW"] = "CREATE VIEW"
		
		for origLine in sqlOrigFile:
			for find in dictFindToReplace.iterkeys():
				origLine = origLine.replace(find, dictFindToReplace[find])
			sqlCopyFile.write(origLine)
		
		sqlOrigFile.close()
		sqlCopyFile.close()
		
		if not IsDummyRun:
			#exec the copy of the original SQL script:
			execSqlScript(sqlScriptCopy, outputFilepath)
			numScriptsRan = numScriptsRan + 1
	return numScriptsRan


def setCurrentDatabaseVersion(dbConn, dbVersion, newDbVersion):
	if(newDbVersion > dbVersion):
		cursor = createCursor(dbConn)
		cursor.execute("exec spDatabaseVersion_SetVersion " + str(newDbVersion))
		dbConn.commit()
		cursor.close()
		
		return True
	return False
		
def validateArgs(sqlScriptListfilePath, origOutputFilepath):
	if not os.path.exists(sqlScriptListfilePath):
		raise Exception("The listfile of SQL scripts could not be found: " + sqlScriptListfilePath)
	if os.path.exists(origOutputFilepath):
		raise Exception("The output file of original objects, already exists: " + origOutputFilepath)


###############################################################
#main
validateArgs(sqlScriptListfilePath, origOutputFilepath)

dbConn = createConnection()
dbVersion = getCurrentDatabaseVersion(dbConn)

dbObjects = readListfile(sqlScriptListfilePath)
dbFilteredObjects = filterObjectsByDbVersion(dbVersion, dbObjects)

backupOriginalObjects(dbFilteredObjects, origOutputFilepath)
numScriptsRan=runNewSQLscripts(dbFilteredObjects, pathToNewSqlDir, newOutputFilepath)
highestDbVersion = getHighestVersion(dbFilteredObjects)
bDbWasUpgraded = setCurrentDatabaseVersion(dbConn, dbVersion, highestDbVersion)
outputSummary(dbObjects, dbFilteredObjects, bDbWasUpgraded, highestDbVersion, numScriptsRan)
dbConn.close()

###############################################################

