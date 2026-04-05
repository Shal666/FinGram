from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    surname: str = Field(min_length=1)
    age: int = Field(ge=13, le=120)
    currency: str = Field(default="KZT")  # KZT, RUB, USD

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    surname: str
    age: int
    currency: str
    role: str = "user"
    created_at: datetime

class UserUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    age: Optional[int] = Field(None, ge=13, le=120)
    currency: Optional[str] = None