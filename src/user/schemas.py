# src/user/schemas.py
from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum


# -----------------------------
# 유저 기본 스키마
# -----------------------------
class GenderEnum(str, Enum):
    male = "male"
    female = "female"


class UserBase(BaseModel):
    user_id: str
    ko_name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[GenderEnum] = None  # gender 필드 추가


class UserCreate(UserBase):
    pw: str
    birth_date: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    preferred_food: Optional[str] = None
    preferred_tags: Optional[str] = None
    gender: Optional[GenderEnum] = None  # User 생성 시에도 gender 추가


class UserUpdate(BaseModel):
    ko_name: Optional[str] = None
    email: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    birth_date: Optional[str] = None
    preferred_food: Optional[str] = None
    preferred_tags: Optional[str] = None
    gender: Optional[GenderEnum] = None  # 수정 시에도 gender 반영


class UserOut(UserBase):
    gender: Optional[GenderEnum] = None  # 응답에도 gender 포함

    class Config:
        from_attributes = True


# -----------------------------
# 유저 작성 레시피 스키마 (입력/수정)
# -----------------------------
class UserRecipeBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class UserRecipeCreate(UserRecipeBase):
    # 조리 단계 텍스트(1~20)
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

    # 조리 단계 이미지(1~20)
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

    # 분류/재료 (문자열 또는 배열 둘 다 허용)
    category: Optional[str] = None
    ingredients: Optional[Union[str, List[str]]] = None

    # 영양정보(문자 그대로, DB와 동일)
    INFO_ENG: Optional[str] = None  # kcal
    INFO_CAR: Optional[str] = None  # g
    INFO_PRO: Optional[str] = None  # g
    INFO_FAT: Optional[str] = None  # g
    INFO_NA: Optional[str] = None   # mg

    # 팁
    RCP_NA_TIP: Optional[str] = None

    # ✅ 새 입력 방식(배열/JSON 문자열 모두 허용)
    steps: Optional[Union[List[str], str]] = None
    step_images: Optional[Union[List[str], str]] = None


class UserRecipeUpdate(BaseModel):
    # 업데이트 가능한 필드 전부 Optional
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    
    steps: Optional[List[str]] = None           # 텍스트 단계
    step_images: Optional[List[str]] = None     # (선택) 단계별 이미지 경로 배열

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


# -----------------------------
# 유저 작성 레시피 스키마 (리스트/요약 출력)
#  - 기존 화면/엔드포인트와 호환 유지
# -----------------------------
class UserRecipeOut(BaseModel):
    # PK & 작성자
    id: int
    user_id: str

    # 기본 정보
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

    # 통계
    view_count: int
    avg_rating: float            # decimal(3,2) → float 직렬화
    rating_count: int

    # 타임스탬프
    created_at: datetime
    updated_at: datetime

    # 조리 단계 텍스트(1~20)
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

    # 조리 단계 이미지 경로(1~20)
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

    # 분류/재료(저장된 원문: 문자열)
    category: Optional[str] = None
    ingredients: Optional[str] = None  # DB는 text(문자열)

    # 영양정보(문자 그대로, DB와 동일)
    INFO_ENG: Optional[str] = None  # kcal
    INFO_CAR: Optional[str] = None  # g
    INFO_PRO: Optional[str] = None  # g
    INFO_FAT: Optional[str] = None  # g
    INFO_NA: Optional[str] = None   # mg

    # 팁(저장된 원문: 문자열)
    RCP_NA_TIP: Optional[str] = None

    class Config:
        from_attributes = True


# -----------------------------
# ✅ 유저 레시피 상세 출력(상세 페이지 전용)
#    - 프론트가 바로 렌더링 가능한 표준 필드 제공
#    - 호환을 위해 기존 MANUALxx/RCP_*도 함께 포함
# -----------------------------
class UserRecipeDetailOut(BaseModel):
    # PK & 작성자
    id: int
    user_id: str

    # 기본 정보
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

    # 통계
    view_count: int
    avg_rating: float
    rating_count: int

    # 타임스탬프
    created_at: datetime
    updated_at: datetime

    # ====== ✅ 표준화된 상세 필드 (프론트가 사용) ======
    ingredients: List[str] = []  # ["당근 100g", "달걀 2개", ...]
    steps: List[str] = []        # ["1. 당근을 ...", "2. ...", ...]
    tip: Optional[str] = None    # 팁

    # ====== 호환용 필드(기존 화면/컴포넌트 참고 시) ======
    # 조리 단계 텍스트(1~20)
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

    # 조리 단계 이미지(1~20)
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

    # 재료/팁(문자열 버전)
    RCP_PARTS_DTLS: Optional[str] = None  # 호환용 문자열
    RCP_NA_TIP: Optional[str] = None      # 호환용 문자열

    # 영양정보(문자 그대로, DB와 동일)
    INFO_ENG: Optional[str] = None  # kcal
    INFO_CAR: Optional[str] = None  # g
    INFO_PRO: Optional[str] = None  # g
    INFO_FAT: Optional[str] = None  # g
    
    INFO_NA: Optional[str] = None   # mg
    
    # 단계 저장 전용 입력 모델
    class StepsIn(BaseModel):
        steps: List[str]
        step_images: Optional[List[str]] = None

    class Config:
        from_attributes = True
