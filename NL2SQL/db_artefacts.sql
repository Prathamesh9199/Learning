-- =======================================================
-- 1. SCHEMA SETUP
-- =======================================================
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'DB_AGENT')
BEGIN
    EXEC('CREATE SCHEMA [DB_AGENT]')
END
GO

-- =======================================================
-- 2. LOGGING TABLE (For feedback_logger_node)
-- =======================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[DB_AGENT].[SESSION_LOGS]') AND type in (N'U'))
BEGIN
    CREATE TABLE DB_AGENT.SESSION_LOGS (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        SessionID NVARCHAR(100),
        UserQuery NVARCHAR(MAX),
        DB_AGENTPlan NVARCHAR(MAX),			-- The reasoning steps taken
        SQLQueryExecuted NVARCHAR(MAX),		-- The SP executed
        ToolName NVARCHAR(100),				-- Which tool was used?
        ExecutionTimeMs INT,
        Timestamp DATETIME2 DEFAULT SYSDATETIME()
    );
END
GO

-- =======================================================
-- 3. STORED PROCEDURE LIBRARY (The DB_AGENT's Tools)
-- =======================================================

-- TOOL 1: Get High-Level Monthly Stats (Descriptive)
-- Usage: "What was the total cost in Q1?"
CREATE OR ALTER PROCEDURE DB_AGENT.sp_GetMonthlyCost
    @MonthYear NVARCHAR(20) = NULL,		-- Optional: 'May-24' or NULL for all
    @ProjectName NVARCHAR(100) = NULL	-- Optional: Filter by Project
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        MONTH_YEAR, 
        SUM(COST) as TotalCost, 
        SUM(FTE) as TotalFTE,
        COUNT(DISTINCT PROJECT_ID) as ActiveProjects
    FROM SEMANTIC.COST_PER_PERSON
    WHERE (@MonthYear IS NULL OR MONTH_YEAR = @MonthYear)
      AND (@ProjectName IS NULL OR PROJECT_NAME = @ProjectName)
    GROUP BY MONTH_YEAR
    ORDER BY MONTH_YEAR;
END
GO

-- TOOL 2: Get Metric Broken Down by Dimension (Descriptive / Drill-Down)
-- Usage: "Show me cost by Location" or "Headcount by Grade"
CREATE OR ALTER PROCEDURE DB_AGENT.sp_GetMetricByDimension
    @Metric NVARCHAR(50),		-- 'COST', 'FTE', 'HEADCOUNT'
    @Dimension NVARCHAR(50),	-- 'LOCATION', 'GRADE', 'CUSTOMER_NAME', 'PROJECT_NAME'
    @MonthYear NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    -- Safety: Whitelist inputs to prevent SQL Injection
    IF @Metric NOT IN ('COST', 'FTE', 'HEADCOUNT') 
       OR @Dimension NOT IN ('LOCATION', 'GRADE', 'CUSTOMER_NAME', 'PROJECT_NAME', 'TENURE_BUCKET', 'VBU', 'HBU')
    BEGIN
        THROW 51000, 'Invalid Parameter provided.', 1;
        RETURN;
    END

    DECLARE @SQL NVARCHAR(MAX);
    DECLARE @AggColumn NVARCHAR(50);

    -- Map User Intent to SQL Column
    IF @Metric = 'HEADCOUNT' SET @AggColumn = 'COUNT(*)'
    ELSE SET @AggColumn = 'SUM(' + QUOTENAME(@Metric) + ')'

    SET @SQL = '
        SELECT TOP 20 
            ' + QUOTENAME(@Dimension) + ' as Dimension, 
            ' + @AggColumn + ' as Value,
            COUNT(*) as RecordCount
        FROM SEMANTIC.COST_PER_PERSON
        WHERE (''' + ISNULL(@MonthYear, 'ALL') + ''' = ''ALL'' OR MONTH_YEAR = @MonthYear)
        GROUP BY ' + QUOTENAME(@Dimension) + '
        ORDER BY Value DESC';

    EXEC sp_executesql @SQL, N'@MonthYear NVARCHAR(20)', @MonthYear;
END
GO

-- TOOL 3: The "Scientist" Tool (Diagnostic)
-- Usage: "Compare Cost between Onshore and Offshore" (Hypothesis Testing)
-- This tool helps the DB_AGENT confirm if a factor (like Location) actually causes a difference.
CREATE OR ALTER PROCEDURE DB_AGENT.sp_CompareMetricByFactor
    @Metric NVARCHAR(50),     -- 'COST' or 'FTE'
    @Factor NVARCHAR(50),     -- 'LOCATION', 'GRADE', 'EMP_TYPE'
    @Value1 NVARCHAR(100),    -- e.g. 'OFFSHORE'
    @Value2 NVARCHAR(100)     -- e.g. 'ONSHORE'
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Safety Check
    IF @Factor NOT IN ('LOCATION', 'GRADE', 'EMP_TYPE', 'CUSTOMER_TYPE', 'BILLING_TYPE')
    BEGIN
        THROW 51000, 'Invalid Factor for comparison.', 1;
        RETURN;
    END

    DECLARE @SQL NVARCHAR(MAX);

    SET @SQL = '
        SELECT 
            ' + QUOTENAME(@Factor) + ' as Factor_Group,
            SUM(' + QUOTENAME(@Metric) + ') as Total_Metric,
            AVG(' + QUOTENAME(@Metric) + ') as Avg_Per_Person,
            COUNT(*) as Headcount
        FROM SEMANTIC.COST_PER_PERSON
        WHERE ' + QUOTENAME(@Factor) + ' IN (@Val1, @Val2)
        GROUP BY ' + QUOTENAME(@Factor);

    EXEC sp_executesql @SQL, N'@Val1 NVARCHAR(100), @Val2 NVARCHAR(100)', @Value1, @Value2;
END
GO

-- TOOL 4: Ambiguity Resolver (Socratic Helper)
-- Usage: DB_AGENT asks "Did you mean 'UHG' or 'United Health'?"
CREATE OR ALTER PROCEDURE DB_AGENT.sp_GetDistinctValues
    @ColumnName NVARCHAR(50),
    @SearchTerm NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @ColumnName NOT IN ('PROJECT_NAME', 'CUSTOMER_NAME', 'LOCATION', 'CITY', 'GRADE')
    BEGIN
        RETURN;
    END

    DECLARE @SQL NVARCHAR(MAX);
    SET @SQL = 'SELECT DISTINCT TOP 10 ' + QUOTENAME(@ColumnName) + ' as Value 
                FROM SEMANTIC.COST_PER_PERSON 
                WHERE (@SearchTerm IS NULL OR ' + QUOTENAME(@ColumnName) + ' LIKE ''%'' + @SearchTerm + ''%'')';
    
    EXEC sp_executesql @SQL, N'@SearchTerm NVARCHAR(50)', @SearchTerm;
END
GO

/*******************************************************
 * SHERLOCK AGENT - STATE PERSISTENCE TABLE
 * Stores serialized graph state for "Zombie Recovery"
 *******************************************************/
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'agent_checkpoints' AND type = 'U')
BEGIN
    CREATE TABLE agent_checkpoints (
        thread_id NVARCHAR(255) NOT NULL,
        checkpoint_id NVARCHAR(255) NOT NULL,
        parent_checkpoint_id NVARCHAR(255) NULL,
        checkpoint_data NVARCHAR(MAX) NOT NULL, -- JSON/Serialized State
        metadata NVARCHAR(MAX) NULL,
        created_at DATETIME DEFAULT GETDATE(),
        PRIMARY KEY (thread_id, checkpoint_id)
    );
    
    -- Index for fast lookups by thread
    CREATE INDEX IX_Checkpoints_Thread ON agent_checkpoints(thread_id, created_at DESC);
END
GO