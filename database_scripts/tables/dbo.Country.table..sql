--table Country

/****** Object:  Table [dev].[Country]    Script Date: 02/20/2012 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO
--drop table [dev].Country
CREATE TABLE [dev].Country
(
	id int IDENTITY NOT NULL,
	Name varchar(20) NOT NULL,
	IsInEU bit NOT NULL
 CONSTRAINT [PK_Country] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]
