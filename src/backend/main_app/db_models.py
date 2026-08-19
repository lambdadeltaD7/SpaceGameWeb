from sqlalchemy import BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import bcrypt


class Base(DeclarativeBase):
    pass



class UsersSchemaDB(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str]
    user_email: Mapped[str] 
    user_password: Mapped[str]
    pass_salted_hashed: Mapped[str]
    is_admin: Mapped[bool]
    res1: Mapped[int]
    res2: Mapped[int]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        password = kwargs["user_password"]

        self.is_admin = False
        self.res1 = 100
        self.res2 = 100

        salt = bcrypt.gensalt()
        self.pass_salted_hashed = str(
            bcrypt.hashpw(
                password = password.encode("utf-8"),
                salt = salt
            )
        )[2:-1]



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
    user_id: Mapped[int]
    res1: Mapped[int]
    res2: Mapped[int]
    x: Mapped[int] 
    y: Mapped[int]
    shield_on: Mapped[bool]


    def to_dict(self, to_str=False):
        return {
            "planet_id": self.planet_id,
            "world_id": self.world_id,
            "user_id": self.user_id,
            "res1": self.res1,
            "res2": self.res2,
            "x": self.x,
            "y": self.y,
            "shield_on" : self.shield_on if not to_str else str(self.shield_on)
        }



class TransactionsSchemaDB(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    user_from_id: Mapped[int]
    user_to_id: Mapped[int]
    res1: Mapped[int]
    res2: Mapped[int]
    created_at: Mapped[int] = mapped_column(BigInteger)