from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    user_id: str
    ko_name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None     # ⬅️ gender 필드 추가

class UserCreate(UserBase):
    pw: str
    birth_date: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    preferred_food: Optional[str] = None
    preferred_tags: Optional[str] = None
    gender: Optional[str] = None     # ⬅️ User 생성 시에도 gender 추가

class UserUpdate(BaseModel):
    ko_name: Optional[str]
    email: Optional[str]
    height: Optional[float]
    weight: Optional[float]
    birth_date: Optional[str]
    preferred_food: Optional[str]
    preferred_tags: Optional[str]
    gender: Optional[str] = None     # ⬅️ 수정 시에도 gender 반영

class UserOut(UserBase):
    gender: Optional[str] = None     # ⬅️ 응답에도 gender 포함
    class Config:
        orm_mode = True
