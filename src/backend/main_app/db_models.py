from sqlalchemy import BigInteger
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



class WorldsSchemaDB(Base):
    __tablename__ = "worlds"

    world_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    seed: Mapped[int]
    w: Mapped[int]
    h: Mapped[int]
    is_public: Mapped[bool]



class PlanetsSchemaDB(Base):
    __tablename__ = "planets"

    planet_id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int]
    res1: Mapped[int]
    res2: Mapped[int]
    x: Mapped[int] 
    y: Mapped[int]
    shield_on: Mapped[bool]



class TransactionsSchemaDB(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    user_from_id: Mapped[int]
    user_to_id: Mapped[int]
    res1: Mapped[int]
    res2: Mapped[int]
    created_at: Mapped[int] = mapped_column(BigInteger)