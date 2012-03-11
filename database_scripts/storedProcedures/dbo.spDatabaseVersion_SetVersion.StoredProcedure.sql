/****** Object:  StoredProcedure [dbo].[dbo.spDatabaseVersion_SetVersion.StoredProcedure.sql]    Script Date: 02/20/2012 18:16:21 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

--DROP PROCEDURE [dbo].[spDatabaseVersion_SetVersion]
--exec [dbo].[spDatabaseVersion_SetVersion] 00000102
CREATE PROCEDURE [dbo].[spDatabaseVersion_SetVersion]
@nextVersion bigint
AS


SET NOCOUNT ON --prevetn row count reports (as would be read by the Python script DeploySQL.py)

--note: CANNOT use output params with pyton -> so just use a SELECT at end of the stored procedure

INSERT INTO
dbo.tblDatabaseVersion
values
(
@nextVersion, getdate()
)


GO
