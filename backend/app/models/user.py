from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class User(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True, index=True)
    full_name: Mapped[str] = mapped_column(default="")
    hashed_password: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column(default="analyst")  # analyst | admin
    is_active: Mapped[bool] = mapped_column(default=True)
