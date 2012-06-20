SELECT 
schemas.name as schema_name
,
tables.name
FROM 
sys.tables tables
inner join sys.schemas schemas
on tables.schema_id = schemas.schema_id

order by
schema_name,
tables.name

