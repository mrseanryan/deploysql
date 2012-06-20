"""
database_common.py

shared code to connect and manipulate the database.
"""

import os
import pyodbc
import tempfile

from deploySQL_common import *

###############################################################
#GLOBALS - THIS MODULE


###############################################################
#CLASSES

class DatabaseConnectiongSettings:
	"""holds details about a database object"""
	def __init__(self, sqlServerInstance, sqlDbName, sqlUser, sqlPassword, sqlCmd, sqlCmdDirPath):
		self.sqlServerInstance = sqlServerInstance
		self.sqlDbName = sqlDbName
		self.sqlUser = sqlUser
		self.sqlPassword = sqlPassword
		self.sqlCmd = sqlCmd
		self.sqlCmdDirPath = sqlCmdDirPath

###############################################################
#FUNCTIONS

def createSqlDumpScript(dbSettings, dbObjects, pathToSqlDumpScript):
	if os.path.exists(pathToSqlDumpScript):
		os.remove(pathToSqlDumpScript)
	sqlDumpScriptFile = open(pathToSqlDumpScript, 'w+')
	sqlDumpScriptFile.write('use ' + dbSettings.sqlDbName + getEndline())
	sqlDumpScriptFile.write(getEndline() + "GO" + getEndline()) # need a GO before any CREATE/ALTER PROCEDURE
	sqlDumpScriptFile.write("declare @currentObjectName varchar(200)" + getEndline())
	sqlDumpScriptFile.write("select @currentObjectName = 'unknown'" + getEndline())
	sqlDumpScriptFile.write(getEndline())
	
	for dbObject in dbObjects:
		#printOut("dbObjectType = " + dbObject.dbObjectType + " sqlScriptName = " + dbObject.sqlScriptName + " sqlObjectName = " + dbObject.sqlObjectName)
		if len(dbObject.sqlObjectName) > 0:
			printOut("dumping database object to disk: " + dbObject.schema + "." + dbObject.sqlObjectName, LOG_VERBOSE)
			sqlExec = "exec sp_helptext '"+dbObject.schema + "." + dbObject.sqlObjectName+"'" + getEndline()
			sqlDumpScriptFile.write(getSqlExists(dbObject.dbObjectType, dbObject.schema, dbObject.sqlObjectName, sqlExec))
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

def backupOriginalObjects(dbSettings, dbObjects, outputFilepath):
	#create the SQL file which will dump out the required database objects:
	pathToSqlDumpScript = getTempDir() + "\\temp.dumpSQLobjects.sql"
	createSqlDumpScript(dbSettings, dbObjects, pathToSqlDumpScript)
	#exec the dump script:
	execSqlScript(dbSettings, pathToSqlDumpScript, outputFilepath)

def createConnection(dbSettings):
	connStr = ( r'DRIVER={SQL Server};SERVER=' +
	dbSettings.sqlServerInstance + ';DATABASE=' + dbSettings.sqlDbName + ';' +
	'Uid=' + dbSettings.sqlUser + ";Pwd=" + dbSettings.sqlPassword + ";"    )
	conn = pyodbc.connect(connStr)
	return conn
	
def createCursor(dbConnection):
	cursor = dbConnection.cursor()
	return cursor
	
def execSqlScript(dbSettings, pathToSqlScript, outputFilepath):
	
	#sqlcmd.exe - ref:   http://msdn.microsoft.com/en-us/library/ms162773.aspx
	
	#sqlcmd -S (local) -U <user> -P <password>   -i dumpDatabaseObject.sql  -o originalSQL.sql
	pathToSqlScript = os.path.abspath(pathToSqlScript)
	outputFilepath = os.path.abspath(outputFilepath)
	args = "-S " + dbSettings.sqlServerInstance + " -U " + dbSettings.sqlUser + " -P " + dbSettings.sqlPassword + " -i " + pathToSqlScript + " -o " + outputFilepath + " -r 0 -b -m -1"    #-b is to exit on SQL error
	runExe(dbSettings.sqlCmd, dbSettings.sqlCmdDirPath, args)

#get some SQL which checks if the given database object exists (if not, then we cannot back it up, and its a SQL error via a 'goto')
def getSqlExists(dbObjectType, schema, sqlObjectName, sqlExec):
	existsLine = ""
	if dbObjectType == "VIEW":
		existsLine = "IF  EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'"+schema + "." + sqlObjectName+"'))" + getEndline()
	elif dbObjectType == "SP":
		existsLine = "IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'"+schema + "." + sqlObjectName+"') AND type in (N'P', N'PC'))" + getEndline()
	elif dbObjectType == "UDF":
		existsLine = "IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'"+schema + "." + sqlObjectName+"') AND type in (N'FN', N'IF', N'TF', N'FS', N'FT'))"
	if len(existsLine) > 0:
		sqlExists = existsLine
		sqlExists = sqlExists + "BEGIN" + getEndline()
		sqlExists = sqlExists + sqlExec + getEndline()
		sqlExists = sqlExists + "END" + getEndline()
		#add Else as an error (since if it does not exist, then we cannot backup!)
		sqlExists = sqlExists + "ELSE" + getEndline()
		sqlExists = sqlExists + "BEGIN" + getEndline()
		sqlExists = sqlExists + "select @currentObjectName = '" + schema + "." + sqlObjectName + "'"+ getEndline()
		sqlExists = sqlExists + "goto ERROR_CANNOT_BACKUP" + getEndline()
		sqlExists = sqlExists + "END" + getEndline()
		return sqlExists
	else:
		raise Exception("not implemented: check for existence of database object type " + dbObjectType)

def getTempDir():
	return tempfile.gettempdir()

def parseSqlScriptName(dbObjectType, sqlScriptName):
	#we need to parse names like this:
	#dbo.spLicenceDocLoader_IsLicenceTypeSigned.SQL
	#dbo.spAmateurExam_Licence.StoredProcedure.sql
	sqlObjectName = ""
	if (dbObjectType == 'SP'):
		sqlObjectName = sqlScriptName.lower()
		sqlObjectName = sqlObjectName.replace('.sql', '')
		sqlObjectName = sqlObjectName.replace('.storedprocedure', '')
	if (dbObjectType == 'UDF'):
		sqlObjectName = sqlScriptName.lower()
		sqlObjectName = sqlObjectName.replace('.sql', '')
		sqlObjectName = sqlObjectName.replace('.UserDefinedFunction', '')
	elif (dbObjectType == 'VIEW'):
		sqlObjectName = sqlScriptName.lower()
		sqlObjectName = sqlObjectName.replace('.sql', '')
		sqlObjectName = sqlObjectName.replace('.view', '')
	else:
		if dbObjectType != 'SP_NEW' and dbObjectType != 'UDF_NEW' and dbObjectType != 'VIEW_NEW':
			addWarning("Cannot determine original object for the SQL script " + sqlScriptName)
	return sqlObjectName
###############################################################
