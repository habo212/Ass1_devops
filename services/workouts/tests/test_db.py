"""The connection string, the retry on connect, and the migration runner."""
import pymssql
import pytest

from workouts import create_app, db
from workouts.migrate import apply_migrations, find_migrations, split_batches


# --- DATABASE_URL ---

def test_parse_database_url():
    assert db.parse_database_url("mssql://app_user:p%40ss@sql.example:1444/workouts") == {
        "server": "sql.example", "port": 1444,
        "user": "app_user", "password": "p@ss", "database": "workouts",
    }


def test_parse_database_url_default_port():
    assert db.parse_database_url("mssql://u:p@host/workouts")["port"] == 1433


@pytest.mark.parametrize("bad", [None, "", "postgres://u:p@host/db", "mssql://u:p@host", "mssql:///db"])
def test_parse_database_url_rejects(bad):
    with pytest.raises(ValueError):
        db.parse_database_url(bad)


def test_create_app_needs_a_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        create_app()


# --- retry on connect (Azure SQL resuming from pause) ---

def test_connect_retries_with_backoff_until_the_database_answers(monkeypatch):
    tries = []

    def fake_connect(**kwargs):
        tries.append(kwargs["server"])
        if len(tries) < 4:
            raise pymssql.OperationalError("40613: database is not currently available")
        return "connection"

    monkeypatch.setattr(db.pymssql, "connect", fake_connect)
    waits = []
    assert db.connect("mssql://u:p@host/d", sleep=waits.append) == "connection"
    assert waits == [1.0, 2.0, 4.0]


def test_connect_gives_up_after_the_last_try(monkeypatch):
    def always_down(**kwargs):
        raise pymssql.OperationalError("40613")

    monkeypatch.setattr(db.pymssql, "connect", always_down)
    waits = []
    with pytest.raises(pymssql.OperationalError):
        db.connect("mssql://u:p@host/d", attempts=6, sleep=waits.append)
    assert waits == [1.0, 2.0, 4.0, 8.0, 10.0]  # capped at 10 s, no wait after the last try


# --- migration runner ---

def test_find_migrations_in_order(tmp_path):
    for name in ("002_b.sql", "001_a.sql", "README.md"):
        (tmp_path / name).write_text("")
    assert find_migrations(tmp_path) == ["001_a.sql", "002_b.sql"]


@pytest.mark.parametrize("names", [["1_a.sql"], ["001-A.sql"], ["001_a.sql", "001_b.sql"]])
def test_find_migrations_rejects_bad_names(tmp_path, names):
    for name in names:
        (tmp_path / name).write_text("")
    with pytest.raises(ValueError):
        find_migrations(tmp_path)


def test_split_batches_on_go_lines():
    sql = "ALTER TABLE t ADD c INT;\nGO\n  go  \nUPDATE t SET c = 1;\n-- GOAL is not a separator\n"
    assert split_batches(sql) == ["ALTER TABLE t ADD c INT;", "UPDATE t SET c = 1;\n-- GOAL is not a separator"]


def connect_to(database_url):
    return pymssql.connect(**db.parse_database_url(database_url), as_dict=True)


def test_second_start_applies_nothing(app, database_url):
    conn = connect_to(database_url)
    assert apply_migrations(conn, db.MIGRATIONS_DIR) == []
    cur = conn.cursor()
    cur.execute("SELECT version FROM schema_migrations ORDER BY version")
    assert [r["version"] for r in cur.fetchall()] == find_migrations(db.MIGRATIONS_DIR)
    conn.close()


def test_migration_runs_its_batches_in_order_and_once(app, database_url, tmp_path):
    (tmp_path / "901_demo.sql").write_text(
        "CREATE TABLE migrate_demo (id INT);\nINSERT INTO migrate_demo VALUES (1);\nGO\n"
        "ALTER TABLE migrate_demo ADD label NVARCHAR(10) NOT NULL DEFAULT 'kept';\n"
    )
    conn = connect_to(database_url)
    try:
        assert apply_migrations(conn, tmp_path) == ["901_demo.sql"]
        assert apply_migrations(conn, tmp_path) == []
        cur = conn.cursor()
        cur.execute("SELECT id, label FROM migrate_demo")
        assert cur.fetchall() == [{"id": 1, "label": "kept"}]  # existing row kept its data
    finally:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS migrate_demo; DELETE FROM schema_migrations WHERE version = '901_demo.sql'")
        conn.commit()
        conn.close()


def test_failed_migration_is_rolled_back_and_not_recorded(app, database_url, tmp_path):
    (tmp_path / "902_broken.sql").write_text("CREATE TABLE migrate_broken (id INT);\nSELECT 1 / 0;\n")
    conn = connect_to(database_url)
    with pytest.raises(pymssql.Error):
        apply_migrations(conn, tmp_path)
    cur = conn.cursor()
    cur.execute("SELECT OBJECT_ID('migrate_broken') AS id")
    assert cur.fetchone()["id"] is None
    cur.execute("SELECT COUNT(*) AS n FROM schema_migrations WHERE version = '902_broken.sql'")
    assert cur.fetchone()["n"] == 0
    conn.close()
