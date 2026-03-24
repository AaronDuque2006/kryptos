from datetime import UTC, datetime

from sqlmodel import Session, create_engine, select

from db import database
from models.user import User


def _create_legacy_users_table(db_engine) -> None:
    with db_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                auth_hash VARCHAR NOT NULL,
                encryption_salt BLOB NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )
        conn.exec_driver_sql(
            """
            INSERT INTO users (id, username, auth_hash, encryption_salt, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                1,
                "legacy_user",
                "legacy_hash",
                b"legacy_salt",
                datetime.now(UTC).isoformat(),
            ),
        )


def test_init_db_migrates_legacy_users_theme_column(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "legacy_vault.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    _create_legacy_users_table(test_engine)

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "APP_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(database, "_harden_windows_permissions", lambda: None)

    database.init_db()

    with Session(test_engine) as session:
        conn = session.connection()
        columns = conn.exec_driver_sql("PRAGMA table_info(users)").all()
        column_names = [row[1] for row in columns]

        assert "theme" in column_names

        migrated_theme = conn.exec_driver_sql(
            "SELECT theme FROM users WHERE id = 1"
        ).scalar_one()
        assert migrated_theme == "textual-dark"

        user = session.exec(select(User).where(User.username == "legacy_user")).first()
        assert user is not None
        assert user.theme == "textual-dark"


def test_run_schema_migrations_is_idempotent_for_users_theme(
    tmp_path, monkeypatch
) -> None:
    db_path = tmp_path / "legacy_vault.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    _create_legacy_users_table(test_engine)

    monkeypatch.setattr(database, "engine", test_engine)

    database._run_schema_migrations()
    database._run_schema_migrations()

    with Session(test_engine) as session:
        conn = session.connection()
        columns = conn.exec_driver_sql("PRAGMA table_info(users)").all()
        theme_columns = [row for row in columns if row[1] == "theme"]

        assert len(theme_columns) == 1
