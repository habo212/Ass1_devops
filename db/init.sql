-- Creates one database and one login per service on the local SQL Server.
-- Run by the one-off `db-init` compose service with sqlcmd, after SQL Server is healthy.
-- Safe to run again: every statement first checks whether its object already exists.
-- Tables are NOT created here; each service creates its own with its migrations.
-- Passwords are sqlcmd variables, filled from environment variables, never written here.

IF DB_ID('workouts') IS NULL CREATE DATABASE workouts;
IF DB_ID('records') IS NULL CREATE DATABASE records;
GO

IF SUSER_ID('workouts_user') IS NULL
    CREATE LOGIN workouts_user WITH PASSWORD = '$(WORKOUTS_DB_PASSWORD)';
IF SUSER_ID('records_user') IS NULL
    CREATE LOGIN records_user WITH PASSWORD = '$(RECORDS_DB_PASSWORD)';
GO

-- Each login becomes a user in its own database only, so workouts_user cannot
-- open the records database and records_user cannot open the workouts database.
-- db_owner of its own database lets the service run its own migrations.
USE workouts;
IF USER_ID('workouts_user') IS NULL CREATE USER workouts_user FOR LOGIN workouts_user;
IF IS_ROLEMEMBER('db_owner', 'workouts_user') = 0 ALTER ROLE db_owner ADD MEMBER workouts_user;
GO

USE records;
IF USER_ID('records_user') IS NULL CREATE USER records_user FOR LOGIN records_user;
IF IS_ROLEMEMBER('db_owner', 'records_user') = 0 ALTER ROLE db_owner ADD MEMBER records_user;
GO

PRINT 'db/init.sql done: databases workouts and records, one login each';
