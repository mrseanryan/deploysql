--exec dbo.spDatabaseVersion_SetVersion 3000703
/*
DELETE
from
tblDatabaseVersion
WHERE
DbVersion = 3000703
*/

exec [dbo].[spDatabaseVersion_GetVersion]

select 
*
from
tblDatabaseVersion


--exec dbo.spDatabaseVersion_SetVersion 123
