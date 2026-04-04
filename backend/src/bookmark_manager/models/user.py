from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    email: str
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime


class UserLogin(SQLModel):
    email: str
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
