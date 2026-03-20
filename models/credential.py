from sqlmodel import SQLModel, Field, Relationship
from user import User, get_utc_now
from datetime import datetime

class Credential(SQLModel, table=True):
    __tablename__ = "credentials"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)

    # Metadato en texto plano para búsquedas en la TUI (ej. "GitHub", "Google")
    title: str = Field(index=True, nullable=False)
    
    # Vector de inicialización para AES-GCM
    nonce: bytes = Field(nullable=False)
    
    # El diccionario JSON encriptado que contiene el usuario, password, url, notas, etc.
    encrypted_payload: bytes = Field(nullable=False)
    
    created_at: datetime = Field(default_factory=get_utc_now)

    user: User = Relationship(back_populates="credentials")