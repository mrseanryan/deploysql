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
import win32api

from string import split

from deploySQL_common import *
from database_common import *


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

def getHighestVersion(dbObjects):
	highestDbVersion = 00000000
	for dbObject in dbObjects:
		if dbObject.dbVersion > highestDbVersion:
			highestDbVersion = dbObject.dbVersion
	return long(highestDbVersion)

#get todays date, in Sql Server format
#def getSQLdateToday():
#	#xxx
#	return "'2012-02-20 18:24:44.383'"

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

def runNewSQLscripts(dbSettings, dbObjects, pathToNewSqlDir, outputFilepath):
	numScriptsRan = 0
	global dictDbObjectTypeToSubDir, IsDummyRun
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
		
		sqlCopyFile.write('use ' + dbSettings.sqlDbName + getEndline())
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
			execSqlScript(dbSettings, sqlScriptCopy, outputFilepath)
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

dbSettings = DatabaseConnectiongSettings(sqlServerInstance, sqlDbName, sqlUser, sqlPassword, sqlCmd, sqlCmdDirPath)

dbConn = createConnection(dbSettings)
dbVersion = getCurrentDatabaseVersion(dbConn)

dbObjects = readListfile(sqlScriptListfilePath)
dbFilteredObjects = filterObjectsByDbVersion(dbVersion, dbObjects)

backupOriginalObjects(dbSettings, dbFilteredObjects, origOutputFilepath)
numScriptsRan=runNewSQLscripts(dbSettings, dbFilteredObjects, pathToNewSqlDir, newOutputFilepath)
highestDbVersion = getHighestVersion(dbFilteredObjects)
bDbWasUpgraded = setCurrentDatabaseVersion(dbConn, dbVersion, highestDbVersion)
outputSummary(dbObjects, dbFilteredObjects, bDbWasUpgraded, highestDbVersion, numScriptsRan)
dbConn.close()

###############################################################

