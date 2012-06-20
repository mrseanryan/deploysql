"""
dumpSqlObjectsToDisk.py

dump SQL objects to disk, so that they can be commited to source control.

we place each database object type in its own directory.

The file names follow the convention used by SSMS when it performs a dump-to-disk operation.

USAGE:	dumpSqlObjectsToDisk.py [OPTIONS] <SQL Server> <Database name> <SQL user> <path to output directory> <path to sqlcmd.exe directory>

OPTIONS:

	-d -debug		Show extra info to help debugging.
	-h -help		Show this help message.
	-w -warnings		Show warnings only (non-verbose output)
"""

#Dependencies:
#
#Python 2.7.x
#pywin32 - http://sourceforge.net/projects/pywin32/
#pyodbc - http://code.google.com/p/pyodbc/downloads/list

import getopt
import getpass

import sys

import win32api

from deploySQL_common import *
from database_common import *
from shutil import move


###############################################################
# settings:

sqlServerInstance = ""
sqlDbName = ""
sqlUser = ""
sqlPassword = ""
pathToOutputDir = ""

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
#args = <SQL Server> <Database name> <SQL user> <path to output directory> <path to sqlcmd.exe directory>
def main(argv):
	
	global sqlServerInstance, sqlDbName, sqlUser, sqlPassword, pathToOutputDir, sqlCmdDirPath

	try:
		opts, args = getopt.getopt(argv, "dhw", ["debug", "help", "warnings"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	if(len(args) !=5):
		usage()
		sys.exit(3)
	#assign the args to variables:
	sqlServerInstance = args[0]
	sqlDbName = args[1]
	sqlUser = args[2]
	pathToOutputDir = args[3]
	sqlCmdDirPath = args[4]
	
	#convert sqlCmdDirPath to short file names:
	#printOut("looking for sqlcmd.exe at " + sqlCmdDirPath + "\n")
	sqlCmdDirPath = win32api.GetShortPathName(sqlCmdDirPath)
	
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-d", "--debug"):
			#debug mode:
			setLogVerbosity(LOG_VERBOSE)
		elif opt in ("-w", "--warnings"):
			setLogVerbosity(LOG_WARNINGS)

	prompt = "Please enter the password for server: " + sqlServerInstance + " database: " + sqlDbName + " user: " + sqlUser + " "
	#xxxx sqlPassword = getpass.getpass(prompt)
	sqlPassword = "skyandsing3"

if __name__ == "__main__":
    main(sys.argv[1:])

###############################################################
#CLASSES

class DatabaseObjectFactoryBase(object):
	"""factory for creating an in-memory DatabaseObject
	derived classes know how to handle the details for each object type
	"""
	def __init__(self, dbObjectType, ssmsObjectType):
		self.dbObjectType = dbObjectType
		self.ssmsObjectType = ssmsObjectType

	def CreateDatabaseObject(self, row):
		dbVersion = '-1'
		dbObjectType = self.dbObjectType
		sqlObjectName = row.name
		schema = row.schema_name
		sqlScriptName =  schema + "." + sqlObjectName + "." + self.ssmsObjectType + ".sql"
		return DatabaseObject(dbVersion, dbObjectType, sqlObjectName, sqlScriptName, schema)

class StoredProcedureFactory(DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for Stored Procedure"""
	def __init__(self):
		super(StoredProcedureFactory, self).__init__('SP', 'StoredProcedure')

class SchemaFactory (DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for Schema"""
	def __init__(self):
		super(SchemaFactory , self).__init__('SCHEMA_CREATE', 'Schema')

class TableFactory(DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for Table"""
	def __init__(self):
		super(TableFactory, self).__init__('TABLE_CREATE', 'Table')
		
class UserFunctionFactory(DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for User Defined Function"""
	def __init__(self):
		super(UserFunctionFactory, self).__init__('UDF', 'UserDefinedFunction')
		
class ViewFactory(DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for View"""
	def __init__(self):
		super(ViewFactory,self).__init__('VIEW', 'View')

#TODO - Triggers

#factory function, to create appropriate factory:
def CreateDatabaseObjectFactory(dbObjectType):
	if (dbObjectType == 'SCHEMA_CREATE'):
		dbObjectFactory = SchemaFactory()
	elif (dbObjectType == 'SP'):
		dbObjectFactory = StoredProcedureFactory()
	elif (dbObjectType == 'TABLE_CREATE'):
		dbObjectFactory = TableFactory()
	elif (dbObjectType == 'UDF'):
		dbObjectFactory = UserFunctionFactory()
	elif (dbObjectType == 'VIEW'):
		dbObjectFactory = ViewFactory()
	else:
		raise Exception("Unrecognised dbObjectType:" + dbObjectType)
	return dbObjectFactory

###############################################################
#VARIABLES

#set mapping from dbObject type -> SQL dump script, so we know how to find the existing database objects
#
#having the SQL scripts in separate files makes it easier to test the SQL
dictDbObjectTypeToSqlScript = dict()
dictDbObjectTypeToSqlScript['SCHEMA_CREATE'] = "listSchemas.sql"
dictDbObjectTypeToSqlScript['SP'] = "listUserStoredProcedures.sql"
dictDbObjectTypeToSqlScript['TABLE_CREATE'] = "listTables.sql"
dictDbObjectTypeToSqlScript['UDF'] = "listFunctions.sql"
dictDbObjectTypeToSqlScript['VIEW'] = "listViews.sql"

###############################################################
#FUNCTIONS

def cleanupSqlScript(outputFilepath):
	"""
	tidies up the SQL script that we have dumped out of the database
	"""
	with open(outputFilepath) as file:
		#fileOut = tempfile.NamedTemporaryFile('w+') #w+ truncates any existing file
		tempFilepath = getTempDir() + "\\dumpSql.cleanup.temp"
		with open(tempFilepath, "w+") as fileOut: #w+ truncates any existing file
			writeHeader(fileOut)
			bFirst = True
			numLinesToSkip = 0
			for line in file:
				if bFirst:
					if line[0:4] == "Msg ":
						numLinesToSkip = 4
				bFirst = False
				
				if numLinesToSkip == 0 and hasLineAllSpaces(line):
					numLinesToSkip = 1
				
				if numLinesToSkip > 0:
					numLinesToSkip = numLinesToSkip - 1
				else:
					fileOut.write(line)
		fileOut.close()
	move(tempFilepath, outputFilepath)

def hasLineAllSpaces(line):
	for char in line:
		if char != ' ' and char != '\r' and char != '\n':
			return False
	return True

def writeHeader(file):
	#do NOT write a date or anything else that would change, as then ALL files will show as changed by the source control system!
	file.writelines( ("-- dumped from database by dumpSqlObjectsToDisk.py =======================", "\n") )

def findExistingDatabaseObjects(dbConn):
	dbObjects = []
	
	for dbObjectType in dictDbObjectTypeToSqlScript.iterkeys():
		sqlListScript = dictDbObjectTypeToSqlScript[dbObjectType]
		sql = readFromFileIntoString("sql\\" + sqlListScript)
	
		dbObjectFactory = CreateDatabaseObjectFactory(dbObjectType)
	
		debugOut("sql:" + sql)
	
		cursor = createCursor(dbConn)
		cursor.execute(sql)
	
		#now perform a SELECT to get the list of objects:
		for row in cursor:
			dbObject = dbObjectFactory.CreateDatabaseObject(row)
			dbObjects.append(dbObject)
		
		cursor.close()
	
	return dbObjects

def fixUpScriptFileName(dbObject):
	dbObject.sqlScriptName = dbObject.sqlScriptName.replace(' ', '_')
	#TODO - find a way to get sqlcmd.exe to dump a file that has spaces in its name

def printCurrentType(dbObject, currentType):
	if(dbObject.dbObjectType != currentType):
		currentType = dbObject.dbObjectType
		printOut("\r" + "Dumping " + currentType + "s to disk =================", LOG_WARNINGS)
	return currentType

def dumpObjectsToDisk(dbSettings, dbObjects, pathToOutputDir, errors):
	#backup each db object to its own script (to match SSMS behaviour)
	iNumObjectsProcessed = 0
	numObjects = len(dbObjects)
	currentType = ""
	for dbObject in dbObjects:
		currentType = printCurrentType(dbObject, currentType)
		dbObjectsThisScript = [dbObject]
		dir = pathToOutputDir + "\\" + dictDbObjectTypeToSubDir[dbObject.dbObjectType]
		
		ensureDirExists(dir)
		
		fixUpScriptFileName(dbObject)
		
		outputFilepath = dir + "\\" + dbObject.sqlScriptName
		
		debugOut("out path:" + outputFilepath)
		
		try:
			backupOriginalObjects(dbSettings, dbObjectsThisScript, outputFilepath)
			cleanupSqlScript(outputFilepath)
		except Exception, ex:
			errors.append( (dbObject, ex) )
			
		iNumObjectsProcessed = iNumObjectsProcessed + 1
		printOut("\r" + str((iNumObjectsProcessed * 100) / numObjects) + "%", LOG_WARNINGS, False) #show some progress, even if low verbosity
		
	printOut("\r" + "100" + "%", LOG_WARNINGS)
	return

def getErrorSummary(errors):
	summary = ""
	for (dbObject, ex) in errors:
		summary = summary + "failed to dump object " + str(dbObject.schema) + "." + str(dbObject.sqlObjectName) + getEndline()
	return summary

def showResults(dbObjects, pathToOutputDir, errors):
	printOut(str(len(dbObjects) )+ " objects were dumped to disk at " + pathToOutputDir)
	printOut(str(len(errors)) + " errors occurred")
	printOut(getEndline())
	printOut(getErrorSummary(errors))

###############################################################
#MAIN

dbSettings = DatabaseConnectiongSettings(sqlServerInstance, sqlDbName, sqlUser, sqlPassword, sqlCmd, sqlCmdDirPath)

dbConn = createConnection(dbSettings)

dbObjects = findExistingDatabaseObjects(dbConn)

errors = [] #(dbObject, ex)
dumpObjectsToDisk(dbSettings, dbObjects, pathToOutputDir, errors)

showResults(dbObjects, pathToOutputDir, errors)

###############################################################
