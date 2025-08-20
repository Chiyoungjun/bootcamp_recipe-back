from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# 기존 User 스키마
class UserBase(BaseModel):
    user_id: str
    ko_name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None      # ⬅️ gender 필드 추가


class UserCreate(UserBase):
    pw: str
    birth_date: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    preferred_food: Optional[str] = None
    preferred_tags: Optional[str] = None
    gender: Optional[str] = None      # ⬅️ User 생성 시에도 gender 추가


class UserUpdate(BaseModel):
    ko_name: Optional[str]
    email: Optional[str]
    height: Optional[float]
    weight: Optional[float]
    birth_date: Optional[str]
    preferred_food: Optional[str]
    preferred_tags: Optional[str]
    gender: Optional[str] = None      # ⬅️ 수정 시에도 gender 반영


class UserOut(UserBase):
    gender: Optional[str] = None      # ⬅️ 응답에도 gender 포함

    class Config:
        from_attributes = True


# 추가: 유저 작성 레시피 스키마


class UserRecipeBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class UserRecipeCreate(UserRecipeBase):
    MANUAL01: Optional[str] = None
    MANUAL02: Optional[str] = None
    MANUAL03: Optional[str] = None
    MANUAL04: Optional[str] = None
    MANUAL05: Optional[str] = None
    MANUAL06: Optional[str] = None
    MANUAL07: Optional[str] = None
    MANUAL08: Optional[str] = None
    MANUAL09: Optional[str] = None
    MANUAL10: Optional[str] = None
    MANUAL11: Optional[str] = None
    MANUAL12: Optional[str] = None
    MANUAL13: Optional[str] = None
    MANUAL14: Optional[str] = None
    MANUAL15: Optional[str] = None
    MANUAL16: Optional[str] = None
    MANUAL17: Optional[str] = None
    MANUAL18: Optional[str] = None
    MANUAL19: Optional[str] = None
    MANUAL20: Optional[str] = None

    MANUAL_IMG01: Optional[str] = None
    MANUAL_IMG02: Optional[str] = None
    MANUAL_IMG03: Optional[str] = None
    MANUAL_IMG04: Optional[str] = None
    MANUAL_IMG05: Optional[str] = None
    MANUAL_IMG06: Optional[str] = None
    MANUAL_IMG07: Optional[str] = None
    MANUAL_IMG08: Optional[str] = None
    MANUAL_IMG09: Optional[str] = None
    MANUAL_IMG10: Optional[str] = None
    MANUAL_IMG11: Optional[str] = None
    MANUAL_IMG12: Optional[str] = None
    MANUAL_IMG13: Optional[str] = None
    MANUAL_IMG14: Optional[str] = None
    MANUAL_IMG15: Optional[str] = None
    MANUAL_IMG16: Optional[str] = None
    MANUAL_IMG17: Optional[str] = None
    MANUAL_IMG18: Optional[str] = None
    MANUAL_IMG19: Optional[str] = None
    MANUAL_IMG20: Optional[str] = None

    category: Optional[str] = None
    ingredients: Optional[str] = None

    INFO_ENG: Optional[str] = None
    INFO_CAR: Optional[str] = None
    INFO_PRO: Optional[str] = None
    INFO_FAT: Optional[str] = None
    INFO_NA: Optional[str] = None

    RCP_NA_TIP: Optional[str] = None


class UserRecipeUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    image_url: Optional[str]

    MANUAL01: Optional[str]
    MANUAL02: Optional[str]
    MANUAL03: Optional[str]
    MANUAL04: Optional[str]
    MANUAL05: Optional[str]
    MANUAL06: Optional[str]
    MANUAL07: Optional[str]
    MANUAL08: Optional[str]
    MANUAL09: Optional[str]
    MANUAL10: Optional[str]
    MANUAL11: Optional[str]
    MANUAL12: Optional[str]
    MANUAL13: Optional[str]
    MANUAL14: Optional[str]
    MANUAL15: Optional[str]
    MANUAL16: Optional[str]
    MANUAL17: Optional[str]
    MANUAL18: Optional[str]
    MANUAL19: Optional[str]
    MANUAL20: Optional[str]

    MANUAL_IMG01: Optional[str]
    MANUAL_IMG02: Optional[str]
    MANUAL_IMG03: Optional[str]
    MANUAL_IMG04: Optional[str]
    MANUAL_IMG05: Optional[str]
    MANUAL_IMG06: Optional[str]
    MANUAL_IMG07: Optional[str]
    MANUAL_IMG08: Optional[str]
    MANUAL_IMG09: Optional[str]
    MANUAL_IMG10: Optional[str]
    MANUAL_IMG11: Optional[str]
    MANUAL_IMG12: Optional[str]
    MANUAL_IMG13: Optional[str]
    MANUAL_IMG14: Optional[str]
    MANUAL_IMG15: Optional[str]
    MANUAL_IMG16: Optional[str]
    MANUAL_IMG17: Optional[str]
    MANUAL_IMG18: Optional[str]
    MANUAL_IMG19: Optional[str]
    MANUAL_IMG20: Optional[str]

    category: Optional[str]
    ingredients: Optional[str]

    INFO_ENG: Optional[str]
    INFO_CAR: Optional[str]
    INFO_PRO: Optional[str]
    INFO_FAT: Optional[str]
    INFO_NA: Optional[str]

    RCP_NA_TIP: Optional[str]


class UserRecipeOut(UserRecipeBase):
    id: int
    user_id: str
    view_count: int
    avg_rating: float
    rating_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
