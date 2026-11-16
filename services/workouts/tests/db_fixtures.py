"""Test database setup shared by this service's tests.

Tests run against a real SQL Server (the compose one locally, a service container
in CI), in a database called workouts_test that is dropped and recreated once per run.
It is never the service's real database.
"""
import os

import pymssql
import pytest

from workouts.db import parse_database_url

# An admin login on the test SQL Server, allowed to create databases.
SERVER_URL = os.environ.get("TEST_SQLSERVER_URL", "mssql://sa:LocalDev_Only1!@localhost:1433/master")
TEST_DB = "workouts_test"


@pytest.fixture(scope="session")
def database_url():
    """Create a brand-new, empty test database once, and return its URL."""
    conn = pymssql.connect(**parse_database_url(SERVER_URL), autocommit=True)
    cur = conn.cursor()
    cur.execute(f"""
        IF DB_ID('{TEST_DB}') IS NOT NULL
        BEGIN
            ALTER DATABASE {TEST_DB} SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            DROP DATABASE {TEST_DB};
        END
    """)
    cur.execute(f"CREATE DATABASE {TEST_DB}")
    conn.close()
    return SERVER_URL.rsplit("/", 1)[0] + "/" + TEST_DB


def empty_tables(database_url, tables):
    """Delete every row so the next test starts clean. The schema stays."""
    conn = pymssql.connect(**parse_database_url(database_url))
    cur = conn.cursor()
    for table in tables:
        cur.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
