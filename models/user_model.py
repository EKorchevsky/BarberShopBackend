from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from enums import UserRole

if TYPE_CHECKING:
    from .refresh_token_model import RefreshToken

class User(SQLModel, table=True):
    __tablename__ = "users"
    __allow_unmapped__ = True

    id: Optional[int] = Field(default=None, primary_key=True)
    role: UserRole = Field(default=UserRole.USER)

    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=100)
    password: str = Field(max_length=255)

    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user", cascade_delete=True)