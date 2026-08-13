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
   