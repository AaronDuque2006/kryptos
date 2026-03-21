import os
import stat
import subprocess
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

APP_DIR = Path.home() / ".tui_vault"
DB_PATH = APP_DIR / "vault.db"

APP_DIR.mkdir(parents=True, exist_ok=True)

sqlite_url = f"sqlite:///{DB_PATH}"

engine = create_engine(
    sqlite_url, echo=False, connect_args={"check_same_thread": False}
)


def init_db():
    from models.user import User  # noqa: F401
    from models.credential import Credential  # noqa: F401

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
        columns = conn.exec_driver_sql("PRAGMA table_info(credentials)").all()
        column_names = {row[1] for row in columns}

        if "title_nonce" not in column_names:
            conn.exec_driver_sql("ALTER TABLE credentials ADD COLUMN title_nonce BLOB")

        if "encrypted_title" not in column_names:
            conn.exec_driver_sql(
                "ALTER TABLE credentials ADD COLUMN encrypted_title BLOB"
            )

        session.commit()


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
