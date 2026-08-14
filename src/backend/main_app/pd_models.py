from pydantic import BaseModel, Field, EmailStr



class UsersSchemaPD(BaseModel):
    user_name: str = Field(max_length=63)
    user_email: EmailStr = Field(max_length=63)
    user_password: str  = Field(max_length=63)
    is_admin: bool = Field(default=False)
    res1: int = Field(default=100, ge=0)
    res2: int = Field(default=100, ge=0)

class UsersSchemaReg(BaseModel):
    user_name: str = Field(max_length=63)
    user_email: EmailStr = Field(max_length=63)
    user_password: str  = Field(max_length=63)

class UsersSchemaLog(BaseModel):
    user_name: str = Field(max_length=63)
    user_password: str  = Field(max_length=63)



class WorldsSchemaPD(BaseModel):
    user_id: int
    seed: int = Field(ge=0)
    w: int = Field(ge=16, le=64)
    h: int = Field(ge=16, le=64)
    is_pulic: bool



class PlanetsSchemaPD(BaseModel):
    world_id: int
    res1: int = Field(ge=0)
    res2: int = Field(ge=0)
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    shield_on: bool


class TransactionsSchemaPD(BaseModel):
    user_from_id: int
    user_to_id: int
    res1: int = Field(ge=0)
    res2: int = Field(ge=0)
    created_at: int  = Field(ge=0)