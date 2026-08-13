from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class UsersSchemaDB(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str]
    user_email: Mapped[str] 
    user_password: Mapped[str]
    is_admin: Mapped[bool]
    res1: Mapped[int]
    res2: Mapped[int]
