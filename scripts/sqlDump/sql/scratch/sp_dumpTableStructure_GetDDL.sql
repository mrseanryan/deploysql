--sp_dumpTableStructure_GetDDL.sql
--
--source: www.sqlservercentral.com
--
--note: this SP is not very robust - does not really work right now.
--
--===========================================================================
--
-- USAGE: exec sp_GetDDL whatever1    
--   or   exec sp_GetDDL 'schemaname.tablename' 
--   or   exec sp_GetDDL '[schemaname].[table name]'      
--#############################################################################    
-- copyright 2004-2009 by Lowell Izaguirre scripts*at*stormrage.com all rights reserved.    
-- http://www.stormrage.com/Portals/0/SSC/sp_GetDDL2000_V2.txt
-- You can use this however you like...this script is not rocket science, but it took a bit of work to create.
-- the only thing that I ask   
-- is that if you adapt my procedure or make it better, to simply send me a copy of it,   
-- so I can learn from the things you've enhanced.The feedback you give will be what makes   
-- it worthwhile to me, and will be fed back to the SQL community.  
-- add this to your toolbox of helpful scripts.
--############################################################################# 
--if you are going to put this in MASTER, and want it to be able to query 
--each database's sys.indexes, you MUST mark it as a system procedure:
--EXECUTE sp_ms_marksystemobject 'sp_GetDDL'
--#############################################################################   
--CREATE  
ALTER
PROCEDURE [dbo].[sp_GetDDL]    
  @TBL                VARCHAR(255)    
AS    
BEGIN  
  SET NOCOUNT ON
  DECLARE     @TBLNAME                VARCHAR(200),
              @SCHEMANAME             VARCHAR(255),
              @STRINGLEN              INT,
              @TABLE_ID               INT,
              @FINALSQL               VARCHAR(8000),
              @CONSTRAINTSQLS         VARCHAR(8000),
              @CHECKCONSTSQLS         VARCHAR(8000),
              @RULESCONSTSQLS         VARCHAR(8000),
              @FKSQLS                 VARCHAR(8000),
              @TRIGGERSTATEMENT       VARCHAR(8000),
              @INDEXSQLS              VARCHAR(8000)
--##############################################################################    
-- INITIALIZE    
--##############################################################################   
  --SET @TBL =  '[DBO].[WHATEVER1]'
  --does the tablename contain a schema? 
 
  SELECT @SCHEMANAME = ISNULL(PARSENAME(@TBL,2),'dbo') ,  
         @TBLNAME    = PARSENAME(@TBL,1) 
  SELECT 
    @TABLE_ID   = [id]    
  FROM sysobjects    
  WHERE [xtype]          =  'U'    
    AND [name]          <>  'dtproperties'    
    AND [name]           =  @TBLNAME  
    --SR - this does not work (assumes this user is the owner of the schema) - AND [uid] =  user_id(@SCHEMANAME) 
    ;  

--##############################################################################    
-- Check If TableName is Valid    
--##############################################################################    
  IF ISNULL(@TABLE_ID,0) = 0    
    BEGIN    
      SET @FINALSQL = 'Table object [' + @SCHEMANAME + '].[' + UPPER(@TBLNAME) + '] does not exist in Database [' + db_name()   + ']' 
      SELECT @FINALSQL; 
      RETURN 0   
    END    
--##############################################################################    
-- Valid Table, Continue Processing    
--##############################################################################  
  SELECT @FINALSQL = 'CREATE TABLE [' + @SCHEMANAME + '].[' + UPPER(@TBLNAME) + '] ( '    
  SELECT @TABLE_ID = OBJECT_ID(@TBLNAME)
  SELECT  
    @STRINGLEN = MAX(LEN(syscolumns.[name])) + 1  
  FROM sysobjects   
    INNER JOIN syscolumns   
      ON  sysobjects.id = syscolumns.id  
      AND sysobjects.id = @TABLE_ID;  
--##############################################################################  
--Get the columns, their definitions and defaults.
--##############################################################################  
  SELECT    
    @FINALSQL = @FINALSQL 
    + CASE    
        WHEN syscolumns.ISCOMPUTED = 1     
        THEN CHAR(13)     
             + '['     
             + UPPER(syscolumns.[name])      
             + '] '     
             + SPACE(@STRINGLEN - LEN(syscolumns.name))       
             + 'AS ' + UPPER(syscolumns.[name])    
        ELSE CHAR(13)     
             + '['     
             + UPPER(syscolumns.[name])      
             + '] '     
             + SPACE(@STRINGLEN - LEN(syscolumns.name))     
             + UPPER(TYPE_NAME(syscolumns.xusertype))     
             + CASE    
--IE NUMERIC(10,2)    
               WHEN TYPE_NAME(syscolumns.xusertype) IN ('decimal','numeric')     
               THEN '('     
                    + CONVERT(VARCHAR,syscolumns.prec)     
                    + ','     
                    + CONVERT(VARCHAR,syscolumns.xscale)     
                    + ') '     
                    + SPACE(6 - LEN(CONVERT(VARCHAR,syscolumns.prec)     
                    + ','     
                    + CONVERT(VARCHAR,syscolumns.xscale)))     
                    + SPACE(7)     
                    + SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                    + CASE    
                        WHEN syscolumns.isnullable = 0     
                        THEN ' NOT NULL'    
                        ELSE '     NULL'    
                      END    
--IE FLOAT(53)    
               WHEN  TYPE_NAME(syscolumns.xusertype) IN ('float','real')     
               THEN     
               --addition: if 53, no need to specifically say (53), otherwise display it    
                    CASE    
                      WHEN syscolumns.prec = 53     
                      THEN SPACE(11 - LEN(CONVERT(VARCHAR,syscolumns.prec)))     
                           + SPACE(7)     
                           + SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                           + CASE    
                               WHEN syscolumns.isnullable = 0     
                               THEN ' NOT NULL'    
                               ELSE '     NULL'    
                             END    
                      ELSE '('    
                           + CONVERT(VARCHAR,syscolumns.prec)     
                           + ') '     
                           + SPACE(6 - LEN(CONVERT(VARCHAR,syscolumns.prec)))     
                           + SPACE(7) + SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                           + CASE    
                               WHEN syscolumns.isnullable = 0     
                               THEN ' NOT NULL'    
                               ELSE '     NULL'    
                             END    
                      END    
--ie VARCHAR(40)    
               WHEN  TYPE_NAME(xusertype) IN ('char','varchar')     
               THEN CASE    
                      WHEN  length = -1     
                      THEN  '(8000)'     
                            + SPACE(6 - LEN(CONVERT(VARCHAR,syscolumns.length)))     
                            + SPACE(7) + SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                            + CASE    
                                WHEN syscolumns.isnullable = 0     
                                THEN ' NOT NULL'    
                                ELSE '     NULL'    
                              END    
                      ELSE '('    
                           + CONVERT(VARCHAR,syscolumns.length)     
                           + ') '     
                           + SPACE(6 - LEN(CONVERT(VARCHAR,syscolumns.length)))     
                           + SPACE(7) + SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                           + CASE    
                               WHEN syscolumns.isnullable = 0     
                               THEN ' NOT NULL'    
                               ELSE '     NULL'    
                             END    
                    END    
--ie NVARCHAR(40) 
               WHEN TYPE_NAME(syscolumns.xusertype) IN ('nchar','nvarchar')     
               THEN CASE    
                      WHEN  prec = -1     
                      THEN '(8000)'     
                           + SPACE(6 - LEN(CONVERT(VARCHAR,syscolumns.prec)))     
                           + SPACE(7)     
                           + SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                           + CASE    
                               WHEN syscolumns.isnullable = 0     
                               THEN  ' NOT NULL'    
                               ELSE '     NULL'    
                             END    
                      ELSE '('    
                           + CONVERT(VARCHAR,syscolumns.prec)     
                           + ') '     
                           + SPACE(6 - LEN(CONVERT(VARCHAR,syscolumns.prec)))     
                           + SPACE(7)     
                           + SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                           + CASE    
                               WHEN syscolumns.isnullable = 0     
                               THEN ' NOT NULL'    
                               ELSE '     NULL'    
                             END    
                    END    
--ie datetime
               WHEN TYPE_NAME(syscolumns.xusertype) IN ('datetime','money','text','image')     
               THEN SPACE(18 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                    + '              '     
                    + CASE    
                        WHEN syscolumns.isnullable = 0     
                        THEN ' NOT NULL'    
                        ELSE '     NULL'    
                      END    
--IE INT
               ELSE SPACE(16 - LEN(TYPE_NAME(syscolumns.xusertype)))     
                            + CASE    
                                WHEN COLUMNPROPERTY ( @TABLE_ID , name , 'IsIdentity' ) = 0       
                                THEN '              '    
                                ELSE ' IDENTITY('     
                                     + CONVERT(VARCHAR,ISNULL(IDENT_SEED(@TBLNAME),1) )     
                                     + ','     
                                     + CONVERT(VARCHAR,ISNULL(IDENT_INCR(@TBLNAME),1) )     
                                     + ')'    
                              END    
                            + SPACE(2)     
                            + CASE    
                                WHEN syscolumns.isnullable = 0     
                                THEN ' NOT NULL'    
                                ELSE '     NULL'    
                              END    
               END     
             + CASE    
                 WHEN syscolumns.[cdefault] = 0     
                 THEN ''   
                 ELSE ' DEFAULT '  + ISNULL(def.text ,'') 
                        --i thought it needed to be handled differently! NOT!    
               END  --CASE cdefault 
--##############################################################################  
-- COLLATE STATEMENTS
-- personally i do not like collation statements, 
-- but included here to make it easy on those who do
--############################################################################## 
/*
         + CASE 
             WHEN collation IS NULL 
             THEN ''
             ELSE ' COLLATE ' + syscolumns.collation
           END
*/
      END --iscomputed    
    + ','
    FROM syscolumns 
      LEFT OUTER JOIN syscomments  DEF 
        on syscolumns.cdefault = DEF.id
    Where syscolumns.id=@TABLE_ID
    ORDER BY syscolumns.colid
--##############################################################################  
--used for formatting the rest of the constraints:
--##############################################################################  
  SELECT  
    @STRINGLEN = MAX(LEN([name])) + 1  
  FROM sysobjects 
--##############################################################################  
--PK/Unique Constraints and Indexes, using the 2005/08 INCLUDE syntax
--############################################################################## 
  --2000 annoyance: could not use cross apply or for xml:
DECLARE @Results  TABLE (
                   [schema_id]             int,
                   [schema_name]           varchar(255),
                   [object_id]             int,
                   [object_name]           varchar(255),
                   [index_id]              int,
                   [index_name]            varchar(255),
                   [Rows]                  int,
                   [SizeMB]                decimal(19,3),
                   [IndexDepth]            int,
                   [type]                  int,
                   [type_desc]             varchar(30),
                   [fill_factor]           int,
                   [is_unique]             int,
                   [is_primary_key]        int ,
                   [is_unique_constraint]  int,
                   [indexcolumn]           varchar(50),
                   [colid]                 int,
                   [index_columns_key]     varchar(6000),
                   [index_columns_include] varchar(3))
INSERT INTO @Results
select 
    sysobjects.uid   AS schema_id, 
    user_name(uid)   AS schema_name,
	sysobjects.id    AS object_id, 
    sysobjects.name  AS object_name,
    sysindexes.indid as index_id,
--
    ISNULL(sysindexes.name, '---') AS index_name,
	sysindexes.Rows, 
    0 AS SizeMB, 
    IndexProperty(sysobjects.id, sysindexes.name, 'IndexDepth') AS IndexDepth,
    CASE
      WHEN sysindexes.indid = 0 then 0
      WHEN sysindexes.indid = 1 then 1
      ELSE 2
    END AS type,
    CASE 
      WHEN INDEXPROPERTY (sysindexes.ID,sysindexes.NAME,'ISCLUSTERED') = 1
      THEN 'CLUSTERED'
      ELSE 'NONCLUSTERED'
    END AS type_desc, 
    INDEXPROPERTY (sysindexes.ID,sysindexes.NAME,'INDEXFILLFACTOR') AS fill_factor,
	INDEXPROPERTY (sysindexes.ID,sysindexes.NAME,'ISUNIQUE') AS [is_unique],
    INDEXPROPERTY (sysindexes.ID,sysindexes.NAME,'ISCLUSTERED') AS [is_primary_key],
    CASE 
      WHEN sysobjects.xtype='UQ' 
      THEN 1 
      ELSE 0 
    END AS is_unique_constraint,
    syscolumns.name AS indexcolumn,
    sysindexkeys.colid,
	''    AS index_columns_key,
	'---' AS index_columns_include
 
from sysindexes
inner join  sysobjects on sysindexes.id = sysobjects.id
inner join sysindexkeys
on  sysindexes.id = sysindexkeys.id 
and sysindexes.indid = sysindexkeys.indid
INNER JOIN syscolumns 
                               ON   sysindexkeys.id=syscolumns.id 
                               AND  sysindexkeys.colid=syscolumns.colid
WHERE sysindexes.INDID > 0 
AND sysindexes.INDID < 255 
AND (sysindexes.STATUS & 64)=0
and user_name(uid)      LIKE CASE WHEN @SCHEMANAME='' THEN user_name(uid)  ELSE @SCHEMANAME END
AND sysobjects.name     LIKE CASE WHEN @TBLNAME=''    THEN sysobjects.name ELSE @TBLNAME END
ORDER BY user_name(uid) , sysobjects.name, sysindexes.name,sysindexkeys.colid 

--now update the column to have all the names

declare @indexname varchar(200), @name varchar(200)
--select @name ='' ,@indexname =category from test where id = 1 
update t 
set @name = case when @indexname = index_name then @name +','+ indexcolumn else indexcolumn end , index_columns_key = @name, @indexname = index_name
from @results t

update @results
set index_columns_key = x.index_columns_key
from @results t
join (select max(index_columns_key)index_columns_key, index_name from @results group by index_name)x
on x.index_name = t.index_name
--cleanup the extra rows
delete from t
From @results t
inner join (select index_name,MIN(colid) AS colid FROM @results GROUP BY index_name)x
ON T.index_name = X.index_name
WHERE T.index_name = X.index_name 
AND T.colid <> x.colid
--@Results table has both PK,s Uniques and indexes in thme...pull them out for adding to funal results:
SET @CONSTRAINTSQLS = ''
SET @INDEXSQLS      = ''
  
--############################################################################## 
--constriants
--############################################################################## 
SELECT  @CONSTRAINTSQLS = @CONSTRAINTSQLS + 
CASE 
  WHEN is_primary_key = 1 or is_unique = 1
  THEN CHAR(13)
       + 'CONSTRAINT   [' + index_name + '] ' 
       + SPACE(@STRINGLEN - LEN(index_name))
       + CASE  WHEN is_primary_key = 1 THEN ' PRIMARY KEY ' ELSE CASE  WHEN is_unique = 1     THEN ' UNIQUE      '      ELSE '' END END 
       + type_desc + CASE WHEN type_desc='NONCLUSTERED' THEN '' ELSE '   ' END
       + ' (' + index_columns_key + ')' 
       + CASE WHEN index_columns_include <> '---' THEN ' INCLUDE (' + index_columns_include + ')' ELSE '' END
       + CASE WHEN fill_factor <> 0 THEN ' WITH FILLFACTOR = ' + CONVERT(VARCHAR(30),fill_factor) ELSE '' END
  ELSE ''
END + ',' 
from @RESULTS
where [type_desc] != 'HEAP'
  AND is_primary_key = 1 or is_unique = 1
order by is_primary_key desc,is_unique desc
--############################################################################## 
--indexes
--############################################################################## 
SELECT @INDEXSQLS = @INDEXSQLS + 
CASE 
  WHEN is_primary_key = 0 or is_unique = 0
  THEN CHAR(13)
       + 'CREATE INDEX [' + index_name + '] '
       + SPACE(@STRINGLEN - LEN(index_name))
       + ' ON [' + [object_name] + ']'
       + ' (' + index_columns_key + ')' 
       + CASE WHEN index_columns_include <> '---' THEN ' INCLUDE (' + index_columns_include + ')' ELSE '' END
       + CASE WHEN fill_factor <> 0 THEN ' WITH FILLFACTOR = ' + CONVERT(VARCHAR(30),fill_factor) ELSE '' END

END 
from @RESULTS
where [type_desc] != 'HEAP'
  AND is_primary_key = 0 AND is_unique = 0
order by is_primary_key desc,is_unique desc
--##############################################################################  
--CHECK Constraints
--############################################################################## 
  SET @CHECKCONSTSQLS = ''
  SELECT
    @CHECKCONSTSQLS = @CHECKCONSTSQLS 
    + CHAR(13)
    + ISNULL('CONSTRAINT   [' + sysobjects.name + '] '
    + SPACE(@STRINGLEN - LEN(sysobjects.name)) 
    + ' CHECK ' + ISNULL(syscomments.text,'')
    + ',','')
  FROM sysobjects
    INNER JOIN syscomments ON sysobjects.id = syscomments.id 
  WHERE sysobjects.xtype = 'C' 
    AND sysobjects.parent_obj = @TABLE_ID
--##############################################################################    
--FOREIGN KEYS 
--############################################################################## 
  SET @FKSQLS = '' ;    
  SELECT 
    @FKSQLS=@FKSQLS 
    + CHAR(13) 
    + 'CONSTRAINT   [' + OBJECT_NAME(constid) +']'
    + SPACE(@STRINGLEN - LEN(OBJECT_NAME(constid) )) 
    + '  FOREIGN KEY ('   + COL_NAME(fkeyid,fkey)
    + ') REFERENCES '    + OBJECT_NAME(rkeyid) 
    +'(' + COL_NAME(rkeyid,rkey) + '),' 
  from sysforeignkeys 
  WHERE fkeyid = @TABLE_ID
--##############################################################################  
--RULES
--############################################################################## 
 SET @RULESCONSTSQLS = ''
 SELECT 
   @RULESCONSTSQLS = @RULESCONSTSQLS 
   + ISNULL(
            CHAR(13) 
            + 'if not exists(SELECT NAME FROM SYSOBJECTS WHERE XTYPE=''R'' AND NAME = ''[' + sysobjects.name + ']'')' + CHAR(13)
            + syscomments.text  + CHAR(13)
            + 'EXEC sp_binderule  [' + sysobjects.name + '], ''[' + OBJECT_NAME(syscolumns.id) + '].[' + syscolumns.name + ']''' + CHAR(13) + 'GO' ,'')
 from syscolumns 
   inner join sysobjects 
     on syscolumns.domain = sysobjects.id
   inner join syscomments 
     on sysobjects.id = syscomments.id 
 where sysobjects.xtype = 'R' 
   and  syscolumns.domain <> 0
   and syscolumns.id = @TABLE_ID
--##############################################################################  
--TRIGGERS
--############################################################################## 
 SET @TRIGGERSTATEMENT = ''    
 SELECT    
   @TRIGGERSTATEMENT = @TRIGGERSTATEMENT +  CHAR(13) + [text] + CHAR(13) + 'GO'    
 FROM syscomments    
 WHERE id IN(SELECT    
               id    
             FROM sysobjects    
             WHERE xtype      = 'TR'    
               AND parent_obj = @TABLE_ID)  
 
--##############################################################################  
--FINAL CLEANUP AND PRESENTATION  
--##############################################################################  
--at this point, there is a trailing comma, or it blank  
  SELECT 
    @FINALSQL = @FINALSQL
                + @CONSTRAINTSQLS
                + @CHECKCONSTSQLS
                + @FKSQLS
--note that this trims the trailing comma from the end of the statements  
  SET @FINALSQL = SUBSTRING(@FINALSQL,1,LEN(@FINALSQL) -1) ;  
  SET @FINALSQL = @FINALSQL + ')' + CHAR(13) ; 

SELECT @FINALSQL 
     + @INDEXSQLS
     + @RULESCONSTSQLS
     + @TRIGGERSTATEMENT

END

