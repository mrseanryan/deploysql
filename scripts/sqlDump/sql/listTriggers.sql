SELECT 
'dbo' as schema_name --TODO - should get schema of associatd table or view (if a DML trigger and not a DDL or logon trigger)
,name
--,*

FROM 
--sysobjects WHERE xtype='TR'
sys.triggers

--SQL to dump a trigger:
--EXEC sp_helptext 'trMobileAntennaeUpdate'
