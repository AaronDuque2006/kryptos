import os
import stat
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

APP_DIR = Path.home() / ".tui_vault"
DB_PATH = APP_DIR / "vault.db"

APP_DIR.mkdir(parents=True, exist_ok=True)

sqlite_url = f"sqlite:///{DB_PATH}"

engine = create_engine(
    sqlite_url, 
    echo=False,
    connect_args={"check_same_thread": False} 
)

def init_db():
    from models.user import User
    from models.credential import Credential
    
    SQLModel.metadata.create_all(engine)
    
    if os.name == 'posix': # Linux / macOS
        os.chmod(DB_PATH, stat.S_IRUSR | stat.S_IWUSR)

def get_session() -> Session    :
    with Session(engine) as session:
        yield session