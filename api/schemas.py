import uuid
import re
from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import validator
from pydantic import EmailStr

LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")

class Tag_(BaseModel):
    tag: str
    user_id: int


class TagCreate(Tag_):
    pass


class TaskCreate(BaseModel):
    title: str
    user_id: uuid.UUID


class TaskResponse(TaskCreate):
    id: int
    created_at: datetime
    tag_id: int | None


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

    @validator('name')
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    @validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise HTTPException(status_code=422, detail='Password should contains more that 8 letters')
        return value

class UserShow(BaseModel):
    email: str
    user_id: uuid.UUID
    name: str