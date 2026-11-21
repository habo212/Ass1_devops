-- Azure SQL version of db/init.sql: run inside one service's database by infra/azure-setup.sh.
-- Azure SQL has no server-level CREATE LOGIN for apps, so each service gets a contained user
-- that exists only in its own database and owns it. APP_USER and APP_PASSWORD come from env.
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '$(APP_USER)')
    CREATE USER [$(APP_USER)] WITH PASSWORD = '$(APP_PASSWORD)';
ELSE
    ALTER USER [$(APP_USER)] WITH PASSWORD = '$(APP_PASSWORD)';
GO
ALTER ROLE db_owner ADD MEMBER [$(APP_USER)];
GO
