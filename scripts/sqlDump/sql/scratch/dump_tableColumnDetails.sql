-- Dump table schema / structure info
declare @tabelObjectId int
set @tabelObjectId = 
--Object_ID(N'prs.tblPrsLicence')
Object_ID(N'dbo.tblLicence')

select
  'Column_name' = ac.name,
  'Type'        = type_name(ac.user_type_id),
  'Length'            = convert(int, ac.max_length),
  'Nullable'        = case when ac.is_nullable = 0 then 'No' else 'Yes' end,
  'Identity'    = case when ac.is_identity = 0 then 'No' else 'Yes' end,
  'PK'          = case when exists(
                    select 1 from sys.index_columns ic
                    inner join sys.columns c  on  ic.object_id = c.object_id
                                              and c.column_id = ic.column_id
                    where ic.object_id = @tabelObjectId and c.name = ac.name
                  ) then 'Yes' else 'No' end,
  'FK'          = case when exists(
                    select 1 from sys.foreign_key_columns fc
                    inner join sys.columns c  on  c.object_id = parent_object_id
                                              and c.column_id = fc.parent_column_id
                    where fc.parent_object_id = @tabelObjectId and c.name = ac.name
                  ) then 'Yes' else 'No' end
from sys.all_columns ac where ac.object_id = @tabelObjectId
