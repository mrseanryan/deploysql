"""
CopySQLtoDeploy.py

This script is used to copy multiple SQL scripts to a deployment location.

USAGE:		CopySQLtoDeploy.py	<listfile of SQL scripts>		<path to directory containing NEW SQL scripts> <path to output directory> 	[OPTIONS]
"""

#Dependencies:
#
#Python 2.7.x


###############################################################

import csv
import getopt
import sys
import re
import os
import shutil
import subprocess
from os.path import exists, join

#pathsep ; on windows  , on unix
from os import pathsep

from string import split

from deploySQL_common import *


###############################################################
# settings:

sqlScriptListfilePath = ""
pathToNewSqlDir = ""
destDirpath = ""

###############################################################
#usage() - prints out the usage text, from the top of this file :-)
def usage():
    print __doc__

###############################################################
#main() - main program entry point
#args = <listfile of SQL scripts>		<path to directory containing NEW SQL scripts> <path to output directory> 
def main(argv):
	
	global sqlScriptListfilePath, pathToNewSqlDir, destDirpath

	try:
		opts, args = getopt.getopt(argv, "hw", ["help", "warnings"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	if(len(args) != 3):
		usage()
		sys.exit(3)
	#assign the args to variables:
	
	sqlScriptListfilePath = args[0]
	pathToNewSqlDir = args[1]
	destDirpath = args[2]
	
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-w", "--warnings"):
			setLogVerbosity(LOG_WARNINGS)

if __name__ == "__main__":
    main(sys.argv[1:])

###############################################################
#FUNCTIONS

def copySQLscripts(dbObjects, pathToNewSqlDir, destDirpath):
	ensureDirExists(destDirpath)
	for dbObject in dbObjects:
		printOut("Copying SQL script " + dbObject.sqlScriptName)
		subDir = dictDbObjectTypeToSubDir[dbObject.dbObjectType]
		pathToSqlScript = pathToNewSqlDir + subDir + dbObject.sqlScriptName
		pathToDest = destDirpath + subDir + dbObject.sqlScriptName
		ensureDirExists(destDirpath + subDir)
		shutil.copyfile(pathToSqlScript, pathToDest)
	
def outputSummary(dbObjects):
	printOut( str(getNumWarnings()) + " warnings occurred" )
	printOut( str(len(dbObjects)) + " scripts were copied")
	#TODO - add more summary info

################################################################
#main()

dbObjects = readListfile(sqlScriptListfilePath)
copySQLscripts(dbObjects, pathToNewSqlDir, destDirpath)
outputSummary(dbObjects)
