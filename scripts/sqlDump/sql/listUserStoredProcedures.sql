Select 
schemas.name as schema_name,
procs.name
from 
sys.procedures procs
inner join sys.schemas schemas
on procs.schema_id = schemas.schema_id
where 
procs.[type] = 'P' 
and 
procs.is_ms_shipped = 0 
and 
procs.[name] not like 'sp[_]%diagram%'


order by
schema_name,
procs.name

