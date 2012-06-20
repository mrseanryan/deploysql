SELECT 
SCHEMA_NAME(schema_id) AS schema_name
,name
FROM sys.objects
WHERE type IN ('FN', 'IF', 'TF')  -- scalar, inline table-valued, table-valued

order by
schema_name,
name
