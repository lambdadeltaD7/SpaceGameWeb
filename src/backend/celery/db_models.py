from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


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


    def to_dict(self, to_str=False):
        return {
            "planet_id": self.planet_id,
            "world_id": self.world_id,
            "res1": self.res1,
            "res2": self.res2,
            "x": self.x,
            "y": self.y,
            "shield_on" : self.shield_on if not to_str else str(self.shield_on)
        }


