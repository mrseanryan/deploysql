/****** Object:  View [dev].[viewCountriesInEU]    Script Date: 01/31/2012 14:30:39 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
IF NOT EXISTS (SELECT * FROM sys.views WHERE object_id = OBJECT_ID(N'[dev].[viewCountriesInEU]'))
EXEC dbo.sp_executesql @statement = N'CREATE VIEW [dev].[viewCountriesInEU]
AS
SELECT      Name
FROM          dev.Country
WHERE      IsInEU = 1
'
GO
