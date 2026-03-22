from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from models.user import get_utc_now

if TYPE_CHECKING:
    from models.user import User


class Credential(SQLModel, table=True):
    __tablename__ = "credentials"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)

    # Metadato en texto plano para búsquedas en la TUI (ej. "GitHub", "Google")
    title: str = Field(index=True, nullable=False)

    # Nuevo esquema: título cifrado en reposo
    title_nonce: bytes | None = Field(default=None, nullable=True)
    encrypted_title: bytes | None = Field(default=None, nullable=True)

    # Vector de inicialización para AES-GCM
    nonce: bytes = Field(nullable=False)

    # El diccionario JSON encriptado que contiene el usuario, password, url, notas, etc.
    encrypted_payload: bytes = Field(nullable=False)

    created_at: datetime = Field(default_factory=get_utc_now)

    user: "User" = Relationship(back_populates="credentials")
