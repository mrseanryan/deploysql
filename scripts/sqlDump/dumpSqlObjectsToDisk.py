"""
dumpSqlObjectsToDisk.py

dump SQL objects to disk, so that they can be commited to source control.

we place each database object type in its own directory.

The file names follow the convention used by SSMS when it performs a dump-to-disk operation.

USAGE:	dumpSqlObjectsToDisk.py [OPTIONS] <SQL Server> <Database name or CSV file listing databases> <SQL user> <path to output directory> <path to sqlcmd.exe directory> <path to Powershell.exe>

OPTIONS:

	-c -csv		Database name is actually a CSV file, listing databases to dump.  This allows user to login just once per database server.
	-d -debug		Show extra info to help debugging.
	-h -help		Show this help message.
	-w -warnings		Show warnings only (non-verbose output)
"""

#Dependencies:
#
#Python 2.7.x
#pywin32 - http://sourceforge.net/projects/pywin32/
#pyodbc - http://code.google.com/p/pyodbc/downloads/list


#TODO - dump tables - execute dumpTableSql.ps1
#TODO - dump schemas - use sp_helptext
#TODO - dump Triggers - use sp_helptext
#TODO - sub-progress, per dbObjectType

import csv

import getopt
import getpass

import sys
import traceback

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
errorLogFilepath = ""

bIsDbNameAcsvFile = False
dbDetailsList = []

# unfortunately, need to use short file paths, to execute a process.  Using pywin32 to get around this, by converting path to short paths.
sqlCmd = "sqlcmd.exe"
#sqlCmdDirPath = "c:\Progra~1\MI6841~1\90\Tools\Binn\\"
sqlCmdDirPath = ""

pathToPowershell = ""

###############################################################
#usage() - prints out the usage text, from the top of this file :-)
def usage():
    print __doc__

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

class UserFunctionFactory(DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for User Defined Function"""
	def __init__(self):
		super(UserFunctionFactory, self).__init__('UDF', 'UserDefinedFunction')
		
class ViewFactory(DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for View"""
	def __init__(self):
		super(ViewFactory,self).__init__('VIEW', 'View')

class NullDatabaseObjectFactory(DatabaseObjectFactoryBase):
	"""factory for creating an in-memory DatabaseObject for Null case (do-nothing) """
	def __init__(self):
		super(NullDatabaseObjectFactory,self).__init__('NULL', 'Null')

	def CreateDatabaseObject(self, row):
		return None

#factory function, to create appropriate factory:
def CreateDatabaseObjectFactory(dbObjectType):
	if (dbObjectType == 'SCHEMA_CREATE'):
		dbObjectFactory = SchemaFactory()
	elif (dbObjectType == 'SP'):
		dbObjectFactory = StoredProcedureFactory()
	elif (dbObjectType == 'TABLE_CREATE'):
		dbObjectFactory = NullDatabaseObjectFactory() #tables are handled by a Powershell script
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
dictDbObjectTypeToSqlScript['TABLE_CREATE'] = "listTables.sql" #TODO - remove as this is not used!
dictDbObjectTypeToSqlScript['UDF'] = "listFunctions.sql"
dictDbObjectTypeToSqlScript['VIEW'] = "listViews.sql"

###############################################################
#FUNCTIONS

def cleanupSqlScript(dbSettings, outputFilepath):
	"""
	tidies up the SQL script that we have dumped out of the database
	"""
	with open(outputFilepath) as file:
		#fileOut = tempfile.NamedTemporaryFile('w+') #w+ truncates any existing file
		tempFilepath = getTempDir() + "\\dumpSql.cleanup.temp"
		with open(tempFilepath, "w+") as fileOut: #w+ truncates any existing file
			writeHeader(dbSettings, fileOut)
			#NOT adding an IF EXISTS, as these are always CREATE scripts (and we do not want to duplicate the SQL for an ALTER script)
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

def readDbNamesFile(dbNamesFilepath):
	dbDetails = []
	listFileReader = csv.reader(open(dbNamesFilepath, 'rb'), delimiter=',')
	for row in listFileReader:
		if(len(row) > 0):
			dbName = row[0]
			if(dbName[0] == '#'):
				continue # a comment line
			dbOutDirPath = row[1]
			
			dbDetails.append( (dbName, dbOutDirPath) )
	
	return dbDetails

def writeHeader(dbSettings, file):
	#do NOT write a date or anything else that would change, as then ALL files will show as changed by the source control system!
	file.writelines( ("-- dumped from database '"+dbSettings.sqlDbName+"' by dumpSqlObjectsToDisk.py =======================", "\n") )

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
			if dbObject != None:
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

def dumpObjectsToDisk(dbSettings, dbObjects, pathToOutputDir, errors, pathToPowershell):
	#backup each db object to its own script (to match SSMS behaviour)
	iNumObjectsProcessed = 0
	numObjects = len(dbObjects)
	currentType = ""
	for dbObject in dbObjects:
		currentType = printCurrentType(dbObject, currentType)
		
		#if 'sfbIsBankHoliday' in dbObject.sqlScriptName :
		#	import pdb
		#	pdb.set_trace()
		
		dbObjectsThisScript = [dbObject]
		dir = pathToOutputDir + "\\" + dictDbObjectTypeToSubDir[dbObject.dbObjectType]
		
		ensureDirExists(dir)
		
		fixUpScriptFileName(dbObject)
		
		outputFilepath = dir + "\\" + dbObject.sqlScriptName
		
		debugOut("out path:" + outputFilepath)
		
		try:
			backupOriginalObjects(dbSettings, dbObjectsThisScript, outputFilepath)
			cleanupSqlScript(dbSettings, outputFilepath)
		except Exception, ex:
			strEx = traceback.format_exc()
			errors.append( (dbObject, strEx) )
			
		iNumObjectsProcessed = iNumObjectsProcessed + 1
		printOut("\r" + str((iNumObjectsProcessed * 100) / numObjects) + "%", LOG_WARNINGS, False) #show some progress, even if low verbosity
	
	dumpTablesToDisk(dbSettings, pathToOutputDir, pathToPowershell)
	
	printOut("\r" + "100" + "%" + getEndline(), LOG_WARNINGS)
	return

#use external script to dump tables to SQL
def dumpTablesToDisk(dbSettings, outputFilepath, pathToPowershell):
	printOut(getEndline() + "Dumping tables to disk ...")

	scriptToRun = "dumpTableSql.ps1"
	outputFilepath = outputFilepath + "\\" + dictDbObjectTypeToSubDir["TABLE_CREATE"]
	
	scriptToRun = os.path.abspath(scriptToRun)
	outputFilepath = os.path.abspath(outputFilepath)
	
	args = "-File " + scriptToRun + " " + dbSettings.sqlServerInstance + " " + dbSettings.sqlDbName + " " + sqlUser + " " + sqlPassword + " " + outputFilepath
	
	pathToPowershellDir = win32api.GetShortPathName(os.path.dirname(pathToPowershell))

	runExe(pathToPowershell, pathToPowershellDir, args)

	return

def getErrorSummary(errors):
	summary = ""
	for (dbObject, ex) in errors:
		summary = summary + "failed to dump object " + str(dbObject.schema) + "." + str(dbObject.sqlObjectName) + getEndline()
	return summary

def logErrors(errors, errorLogFilepath):
	if(len(errors) > 0):
		if(len(errorLogFilepath) == 0):
			errorLogFilepath = "sqlDump.errors.log"
		errorFile = open(errorLogFilepath, 'w+') #overwrite existing file
		for (dbObject, ex) in errors:
			errorFile.write(">> Could not dump object " + dbObject.GetFullname() + " - error: " + ex)
		printOut("Please see the file "+errorLogFilepath+" for more details")

def showResults(dbObjects, pathToOutputDir, errors, errorLogFilepath):
	printOut(getErrorSummary(errors))
	printOut(getEndline())
	printOut(str(len(dbObjects) )+ " objects were dumped to disk at " + pathToOutputDir)
	printOut(str(len(errors)) + " errors occurred")
	logErrors(errors, errorLogFilepath)

###############################################################
#main() - main program entry point
#args = <SQL Server> <Database name> <SQL user> <path to output directory> <path to sqlcmd.exe directory>
def main(argv):
	
	global sqlServerInstance, sqlDbName, sqlUser, sqlPassword, pathToOutputDir, sqlCmdDirPath, pathToPowershell
	global bIsDbNameAcsvFile, dbDetailsList

	try:
		opts, args = getopt.getopt(argv, "cdhw", ["csv", "debug", "help", "warnings"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	if(len(args) !=6):
		usage()
		sys.exit(3)
	#assign the args to variables:
	sqlServerInstance = args[0]
	sqlDbName = args[1]
	sqlUser = args[2]
	pathToOutputDir = args[3]
	sqlCmdDirPath = args[4]
	pathToPowershell = args[5]
	
	#convert sqlCmdDirPath to short file names:
	#printOut("looking for sqlcmd.exe at " + sqlCmdDirPath + "\n")
	sqlCmdDirPath = win32api.GetShortPathName(sqlCmdDirPath)
	
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-c", "--csv"):
			bIsDbNameAcsvFile = True
		elif opt in ("-d", "--debug"):
			#debug mode:
			setLogVerbosity(LOG_VERBOSE)
		elif opt in ("-w", "--warnings"):
			setLogVerbosity(LOG_WARNINGS)

	if(bIsDbNameAcsvFile):
		dbDetailsList = readDbNamesFile(sqlDbName)
		(firstDbName, dbOutDir) = dbDetailsList[0]
		sqlDbName = firstDbName #use the first database, to get the password from user
	else:
		dbDetailsList.append( (sqlDbName, pathToOutputDir) )
	prompt = "Please enter the password for server: " + sqlServerInstance + " database: " + sqlDbName + " user: " + sqlUser + " "
	sqlPassword = getpass.getpass(prompt)

if __name__ == "__main__":
    main(sys.argv[1:])

###############################################################
#MAIN

for (dbName, dbOutDir) in dbDetailsList:

	printOut(" ____________________________________________")
	printOut("Processing database " + dbName + "..." )

	errorLogFilepath = "sqlDump." + dbName + ".errors.log"

	dbSettings = DatabaseConnectiongSettings(sqlServerInstance, dbName, sqlUser, sqlPassword, sqlCmd, sqlCmdDirPath)

	dbConn = createConnection(dbSettings)

	dbObjects = findExistingDatabaseObjects(dbConn)

	errors = [] #(dbObject, ex)
	dumpObjectsToDisk(dbSettings, dbObjects, dbOutDir, errors, pathToPowershell)

	showResults(dbObjects, dbOutDir, errors, errorLogFilepath)

###############################################################
