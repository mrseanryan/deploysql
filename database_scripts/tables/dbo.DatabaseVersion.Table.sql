--dbo.tblDatabaseVersion.Table.sql

--table to store the VERSION of the database schema.
--this allows us to:
--1) automagically upgrade any database (provided this table is present + has correct initial version)
--2) manually inspect a database, and see which schema version is in place
--3) see when was the database upgraded

--DROP TABLE tblDatabaseVersion

/****** Object:  Table [dbo].[tblDatabaseVersion]    Script Date: 02/20/2012 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO
--drop table tblDatabaseVersion
CREATE TABLE [dbo].tblDatabaseVersion
(
	DbVersion bigint NOT NULL, /*		format is 11223344 - where:
										11 = Major number (2 digit)
										22 = Minor number (2 digit)
										33 = Release number (2 digit)
										44 = build number (2 digit)
										
										example:	MyProduct 1.0.4 = 01000400
													MyProduct 1.0.7 build 2 = 01000702
								*/
	UpgradeDate datetime NOT NULL
 CONSTRAINT [PK_tblDatabaseVersion] PRIMARY KEY CLUSTERED 
(
	[DbVersion] ASC --making this be the primary key, to prevent duplicate values
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]

/*
Initially we MANUALLY create this table + insert appropriate version, to match how up to date the database is.
For a list of the database versions, see LING\sql\scripts\list_of_SQL_scripts_to_deploy.csv

INSERT INTO
dbo.tblDatabaseVersion
values
(
01000702, getdate()
)
*/

GO
