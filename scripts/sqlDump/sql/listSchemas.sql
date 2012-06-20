SELECT 
SCHEMA_NAME(schema_id) AS schema_name,
SCHEMA_NAME(schema_id) AS name --to match the other SQL scripts

--,OBJECTPROPERTYEX(OBJECT_ID,'IsIndexed') AS IsIndexed
--,OBJECTPROPERTYEX(OBJECT_ID,'IsIndexable') AS IsIndexable
--,*
FROM sys.schemas

order by schema_name
