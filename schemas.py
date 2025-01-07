from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    password: str
    email_id: EmailStr
    phone_no: str
    random_path: str

class UserUpdate(BaseModel):
    username: str
    password: str
    random_path: str

class UserResponse(BaseModel):
    id: int
    username: str
    email_id: EmailStr
    phone_no: str
    random_path: str

    class Config:
        orm_mode = True

