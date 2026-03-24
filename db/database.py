import os
import stat
import subprocess
from pathlib import Path

from sqlalchemy.engine import Connection
from sqlmodel import Session, SQLModel, create_engine

APP_DIR = Path.home() / ".tui_vault"
DB_PATH = APP_DIR / "vault.db"

APP_DIR.mkdir(parents=True, exist_ok=True)

sqlite_url = f"sqlite:///{DB_PATH}"

engine = create_engine(
    sqlite_url, echo=False, connect_args={"check_same_thread": False}
)


def init_db() -> None:
    from models.credential import Credential  # noqa: F401
    from models.user import User  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _run_schema_migrations()

    if os.name == "posix":  # Linux / macOS
        os.chmod(DB_PATH, stat.S_IRUSR | stat.S_IWUSR)
    elif os.name == "nt":
        _harden_windows_permissions()


def get_session() -> Session:
    return Session(engine)


def _run_schema_migrations() -> None:
    with Session(engine) as session:
        conn = session.connection()
        _add_column_if_missing(
            conn,
            table_name="credentials",
            column_name="title_nonce",
            alter_statement="ALTER TABLE credentials ADD COLUMN title_nonce BLOB",
        )
        _add_column_if_missing(
            conn,
            table_name="credentials",
            column_name="encrypted_title",
            alter_statement="ALTER TABLE credentials ADD COLUMN encrypted_title BLOB",
        )
        _add_column_if_missing(
            conn,
            table_name="users",
            column_name="theme",
            alter_statement=(
                "ALTER TABLE users "
                "ADD COLUMN theme VARCHAR NOT NULL DEFAULT 'textual-dark'"
            ),
        )

        session.commit()


def _add_column_if_missing(
    conn: Connection,
    table_name: str,
    column_name: str,
    alter_statement: str,
) -> None:
    if not _table_exists(conn, table_name):
        return

    columns = conn.exec_driver_sql(f"PRAGMA table_info({table_name})").all()
    column_names = {row[1] for row in columns}

    if column_name not in column_names:
        conn.exec_driver_sql(alter_statement)


def _table_exists(conn: Connection, table_name: str) -> bool:
    table_row = conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).first()
    return table_row is not None


def _harden_windows_permissions() -> None:
    current_username = os.environ.get("USERNAME")
    if not current_username:
        return

    commands = [
        ["icacls", str(APP_DIR), "/inheritance:r"],
        ["icacls", str(APP_DIR), "/grant:r", f"{current_username}:(OI)(CI)F"],
        ["icacls", str(DB_PATH), "/inheritance:r"],
        ["icacls", str(DB_PATH), "/grant:r", f"{current_username}:F"],
    ]

    for command in commands:
        subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        )
