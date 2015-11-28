"""
common code used by DeploySQL.py + CopySQLtoDeploy.py

- print out progress & results
- processing files
"""

#Dependencies:		Python 2.x

import csv
import sys
from os.path import *

#pathsep ; on windows  , on unix
from os import mkdir, pathsep

import subprocess

###############################################################
# settings:
#LOG_WARNINGS_ONLY - this means, only output if the verbosity is LOG_WARNINGS
LOG_WARNINGS, LOG_WARNINGS_ONLY, LOG_NORMAL, LOG_VERBOSE = range(4)

logVerbosity = LOG_NORMAL

numWarnings = 0

#set mapping from dbObject type -> subdirectory, to locate SQL scripts:
dictDbObjectTypeToSubDir = dict()
dictDbObjectTypeToSubDir['SCHEMA_CREATE'] = "schemas\\"
dictDbObjectTypeToSubDir['SP'] = "storedProcedures\\"
dictDbObjectTypeToSubDir['SP_NEW'] = "storedProcedures\\"
dictDbObjectTypeToSubDir['TABLE_POP'] = "tables_populated\\"
dictDbObjectTypeToSubDir['TABLE_ALTER'] = "tables_modified\\"
dictDbObjectTypeToSubDir['TABLE_CREATE'] = "tables\\"
dictDbObjectTypeToSubDir['UDF'] = "userDefinedFunctions\\"
dictDbObjectTypeToSubDir['UDF_NEW'] = "userDefinedFunctions\\"
dictDbObjectTypeToSubDir['VIEW'] = "views\\"
dictDbObjectTypeToSubDir['VIEW_NEW'] = "views\\"


###############################################################
#CLASSES

class DatabaseObject:
	"""holds details about a database object"""
	def __init__(self, dbVersion, dbObjectType, sqlObjectName, sqlScriptName, schema):
		self.dbVersion = long(dbVersion)
		self.dbObjectType = dbObjectType
		self.sqlObjectName = sqlObjectName
		self.sqlScriptName = sqlScriptName
		self.schema = schema

	def GetFullname(self):
		return self.schema + "." + self.dbObjectType

###############################################################
#FUNCTIONS

def addWarning(warningMsg):
	global numWarnings
	numWarnings = numWarnings + 1
	printOut("! WARNING - " + warningMsg, LOG_WARNINGS)

#ask_ok() - prompts the user to continue
def ask_ok(prompt, retries=3, complaint='Yes or no, please!'):
    while True:
        ok = raw_input(prompt)
        ok = ok.lower()
        if ok in ('y', 'ye', 'yes'):
            return True
        if ok in ('n', 'no', 'nop', 'nope'):
            return False
        retries = retries - 1
        if retries < 0:
            raise IOError('refusenik user')
        print complaint        

def debugOut(message):
	printOut(message, LOG_VERBOSE)

def ensureDirExists(dirPath):
	if not exists(dirPath):
		mkdir(dirPath)

def getEndline():
	return "\r\n" #OK for Windows

#provide access to the global that is in this module:
def getNumWarnings():
	return numWarnings

def parseSchemaFromObjectName(sqlObjectNameFromFilename): #returns (schema, sqlObjectName)
	schema = ""
	sqlObjectName = ""
	if "." in sqlObjectNameFromFilename:
		iDotPos = sqlObjectNameFromFilename.find(".")
		schema = sqlObjectNameFromFilename[0:iDotPos]
		sqlObjectName = sqlObjectNameFromFilename[iDotPos + 1: ]
	else:
		schema = 'dbo' #default
		sqlObjectName = sqlObjectNameFromFilename
	return (schema, sqlObjectName)

def parseSqlScriptName(dbObjectType, sqlScriptName): #returns (schema, sqlObjectName)
	#we need to parse names like this:
	#dbo.spLoader_IsTypeSigned.SQL
	#dbo.spMyStoredProcedure.StoredProcedure.sql
	sqlObjectNameFromFilename = ""
	if (dbObjectType == 'SP'):
		sqlObjectNameFromFilename = sqlScriptName.lower()
		sqlObjectNameFromFilename = sqlObjectNameFromFilename.replace('.sql', '')
		sqlObjectNameFromFilename = sqlObjectNameFromFilename.replace('.storedprocedure', '')
	elif (dbObjectType == 'UDF'):
		sqlObjectNameFromFilename = sqlScriptName.lower()
		sqlObjectNameFromFilename = sqlObjectNameFromFilename.replace('.sql', '')
		sqlObjectNameFromFilename = sqlObjectNameFromFilename.replace('.UserDefinedFunction', '')
	elif (dbObjectType == 'VIEW'):
		sqlObjectNameFromFilename = sqlScriptName.lower()
		sqlObjectNameFromFilename = sqlObjectNameFromFilename.replace('.sql', '')
		sqlObjectNameFromFilename = sqlObjectNameFromFilename.replace('.view', '')
	else:
		if dbObjectType != 'SP_NEW' and dbObjectType != 'UDF_NEW' and dbObjectType != 'VIEW_NEW':
			addWarning("Cannot determine original object for the SQL script " + sqlScriptName)
			
	#remove the schema prefix, if it is present:
	(schema, sqlObjectName) = parseSchemaFromObjectName(sqlObjectNameFromFilename)
	
	return (schema, sqlObjectName)

#printOut()
#this function prints out, according to user's options for verbosity
def printOut(txt, verb = LOG_NORMAL, bNewLine = True):
	global logVerbosity
	#txt = "> " + txt #prefix to make it easier to grep our output from 7zip's
	if(bNewLine):
		txt = txt + "\n"
	if verb == LOG_WARNINGS_ONLY:
		if logVerbosity == LOG_WARNINGS: #special case :-(
			sys.stdout.write(txt)
	elif(logVerbosity >= verb):
		sys.stdout.write(txt)
		

def readFromFileIntoString(filepath):
	strContents = ''
	with open(filepath, 'r') as file:
		for line in file:
			strContents = strContents + line

	return strContents

def readListfile(sqlScriptListfilePath):
	#read in the list of database objects:
	dbObjects = []
	listFileReader = csv.reader(open(sqlScriptListfilePath, 'rb'), delimiter=',')
	for row in listFileReader:
		if(len(row) > 0):
			dbVersion = row[0]
			if(dbVersion[0] == '#'):
				continue # a comment line
			dbObjectType = row[1]
			sqlScriptName = row[2]
			(schema, sqlObjectName) = parseSqlScriptName(dbObjectType, sqlScriptName)
			#printOut("dbObjectType = " + dbObjectType + " sqlScriptName = " + sqlScriptName + " sqlObjectName = " + sqlObjectName)
			dbObjects.append(DatabaseObject(dbVersion,dbObjectType, sqlObjectName, sqlScriptName, schema))
	return dbObjects

def runExe(targetScriptName, targetScriptDirPath, args):
	scriptWorkingDir = targetScriptDirPath #os.path.dirname(targetScriptPath)
	toExec = join(targetScriptDirPath, targetScriptName) + " " + args
	printOut("Running exe " + toExec, LOG_VERBOSE)
	printOut("working dir = " + scriptWorkingDir, LOG_VERBOSE)
	process = subprocess.Popen(toExec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = scriptWorkingDir)
	(stdout_cap, stderr_cap) = process.communicate()
	if(len(stderr_cap) > 0):
		raise Exception(str(stderr_cap))
	if(len(stdout_cap) > 0):
		printOut(" >> " + str(stdout_cap));
	if(process.returncode != 0):
		raise Exception("Process returned error code:" + str(process.returncode))

#set the global in this module
def setLogVerbosity(verbosity):
	global logVerbosity
	logVerbosity = verbosity

###############################################################
#self tests - SUPPORT
def checkEquals(testName, expected, actual):
	if(expected != actual):
		raise Exception("!!!TEST FAIL - "+testName+" - expected value:" + str(expected) + " actual value:" + str(actual) )

def checkEqualsCaseInsensitive(testName, expected, actual):
	checkEquals(testName, expected.lower(), actual.lower())

###############################################################
#self tests (unit tests!)

def selfTestCommon():
	"""run some self-tests - basically unit tests - for COMMON"""
	test_parseSqlScriptName()

def test_parseSqlScriptName_runner(dbObjectType, sqlScriptFilename, expectedSchema, expectedSqlObjectName):
	testName = 'test_parseSqlScriptName_runner'
	(actualSchema, actualSqlObjectName) = parseSqlScriptName(dbObjectType, sqlScriptFilename) #returns (schema, sqlObjectName)
	checkEqualsCaseInsensitive(testName, expectedSchema, actualSchema)
	checkEqualsCaseInsensitive(testName, expectedSqlObjectName, actualSqlObjectName)
	return

def test_parseSqlScriptName():
	test_parseSqlScriptName_runner('SP', 'dbo.spMyStoredProcedure.StoredProcedure.sql', 'dbo', 'spMyStoredProcedure')
	test_parseSqlScriptName_runner('SP', 'spDocumentation_GetPdfFilenameSuffix.StoredProcedure.sql', 'dbo', 'spDocumentation_GetPdfFilenameSuffix')
	test_parseSqlScriptName_runner('SP', 'prs.uspMy_Report.StoredProcedure.sql', 'PRS', 'uspMy_Report')
	test_parseSqlScriptName_runner('SP', 'prs.uspMYdb_Report.sql', 'PRS', 'uspMYdb_Report')
	return
