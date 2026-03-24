from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.credential import Credential


def get_utc_now() -> datetime:
    # Función auxiliar para asegurar que los timestamps tengan zona horaria UTC.
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)

    username: str = Field(index=True, unique=True, max_length=50, nullable=False)

    auth_hash: str = Field(nullable=False)

    encryption_salt: bytes = Field(nullable=False)

    theme: str = Field(default="textual-dark", max_length=50)

    created_at: datetime = Field(default_factory=get_utc_now)

    credentials: list["Credential"] = Relationship(
        back_populates="user", cascade_delete=True
    )
