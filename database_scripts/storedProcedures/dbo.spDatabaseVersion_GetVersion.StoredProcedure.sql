/****** Object:  StoredProcedure [dbo].[dbo.spDatabaseVersion_GetVersion.StoredProcedure.sql]    Script Date: 02/20/2012 18:16:21 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

--DROP PROCEDURE [dbo].[spDatabaseVersion_GetVersion]
--exec [dbo].[spDatabaseVersion_GetVersion]
CREATE PROCEDURE [dbo].[spDatabaseVersion_GetVersion]
--no params
AS


SET NOCOUNT ON --prevetn row count reports (as would be read by the Python script DeploySQL.py)

--note: CANNOT use output params with pyton -> so just use a SELECT at end of the stored procedure
SELECT 
max(DbVersion) as DbVersion
from
tblDatabaseVersion


GO
