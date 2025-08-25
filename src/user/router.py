from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from .service import UserService
from .schemas import UserRecipeOut, UserRecipeUpdate
from user.models import UserRecipe, User
from database import get_db
from recipe.service import add_or_update_rating


# 아래를 추가 (폴더별 __init__.py 있으면 작동, 없는 경우 만들어주세요)
from sqlalchemy import func
from recipe.models import Rating                # 기본/사용자 레시피 별점 모델
from recipe.schemas import RatingRequest  
# 별점 등록용 Pydantic 스키마
router = APIRouter()
service = UserService()

def filter_non_empty_manuals(recipe_dict):
    filtered = recipe_dict.copy()
    manual_text_keys = [f"MANUAL{str(i).zfill(2)}" for i in range(1, 21)]
    manual_img_keys = [f"MANUAL_IMG{str(i).zfill(2)}" for i in range(1, 21)]

    for key in manual_text_keys:
        if not filtered.get(key):
            filtered.pop(key, None)

    for key in manual_img_keys:
        if not filtered.get(key):
            filtered.pop(key, None)

    return filtered

@router.get("/")
async def get_users():
    try:
        data = await service.get_users()
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
async def get_one_user(user_id: str):
    try:
        data = await service.get_one_user(user_id)
        if data is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": 200, "message": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signin")
async def sign_in(request: Request):
    user_info = await request.json()
    try:
        data = await service.sign_in(user_info)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/signup")
async def sign_up(request: Request):
    user_info = await request.json()
    try:
        data = await service.sign_up(user_info)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{user_id}")
async def update_user(user_id: str, request: Request):
    update_info = await request.json()
    try:
        data = await service.update_user(user_id, update_info)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def filter_non_empty_manuals(recipe_dict):
    filtered = recipe_dict.copy()
    manual_text_keys = [f"MANUAL{str(i).zfill(2)}" for i in range(1, 21)]
    manual_img_keys = [f"MANUAL_IMG{str(i).zfill(2)}" for i in range(1, 21)]
    for key in manual_text_keys:
        if not filtered.get(key):
            filtered.pop(key, None)
    for key in manual_img_keys:
        if not filtered.get(key):
            filtered.pop(key, None)
    return filtered

@router.post("/{user_id}/recipes", response_model=int)
async def create_user_recipe(
    user_id: str,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image_url: Optional[UploadFile] = File(None),
    ingredients: str = Form(...),
    INFO_ENG: Optional[str] = Form(None),
    INFO_CAR: Optional[str] = Form(None),
    INFO_PRO: Optional[str] = Form(None),
    INFO_FAT: Optional[str] = Form(None),
    INFO_NA: Optional[str] = Form(None),
    RCP_NA_TIP: Optional[str] = Form(None),

    # 메뉴얼 텍스트 20개
    MANUAL01: Optional[str] = Form(None),
    MANUAL02: Optional[str] = Form(None),
    MANUAL03: Optional[str] = Form(None),
    MANUAL04: Optional[str] = Form(None),
    MANUAL05: Optional[str] = Form(None),
    MANUAL06: Optional[str] = Form(None),
    MANUAL07: Optional[str] = Form(None),
    MANUAL08: Optional[str] = Form(None),
    MANUAL09: Optional[str] = Form(None),
    MANUAL10: Optional[str] = Form(None),
    MANUAL11: Optional[str] = Form(None),
    MANUAL12: Optional[str] = Form(None),
    MANUAL13: Optional[str] = Form(None),
    MANUAL14: Optional[str] = Form(None),
    MANUAL15: Optional[str] = Form(None),
    MANUAL16: Optional[str] = Form(None),
    MANUAL17: Optional[str] = Form(None),
    MANUAL18: Optional[str] = Form(None),
    MANUAL19: Optional[str] = Form(None),
    MANUAL20: Optional[str] = Form(None),

    # 메뉴얼 이미지 20개
    MANUAL_IMG01: Optional[UploadFile] = File(None),
    MANUAL_IMG02: Optional[UploadFile] = File(None),
    MANUAL_IMG03: Optional[UploadFile] = File(None),
    MANUAL_IMG04: Optional[UploadFile] = File(None),
    MANUAL_IMG05: Optional[UploadFile] = File(None),
    MANUAL_IMG06: Optional[UploadFile] = File(None),
    MANUAL_IMG07: Optional[UploadFile] = File(None),
    MANUAL_IMG08: Optional[UploadFile] = File(None),
    MANUAL_IMG09: Optional[UploadFile] = File(None),
    MANUAL_IMG10: Optional[UploadFile] = File(None),
    MANUAL_IMG11: Optional[UploadFile] = File(None),
    MANUAL_IMG12: Optional[UploadFile] = File(None),
    MANUAL_IMG13: Optional[UploadFile] = File(None),
    MANUAL_IMG14: Optional[UploadFile] = File(None),
    MANUAL_IMG15: Optional[UploadFile] = File(None),
    MANUAL_IMG16: Optional[UploadFile] = File(None),
    MANUAL_IMG17: Optional[UploadFile] = File(None),
    MANUAL_IMG18: Optional[UploadFile] = File(None),
    MANUAL_IMG19: Optional[UploadFile] = File(None),
    MANUAL_IMG20: Optional[UploadFile] = File(None),
):
    print("==== [라우터 진입] ====")
    for i in range(1, 21):
        print(f"MANUAL{str(i).zfill(2)}:", locals().get(f"MANUAL{str(i).zfill(2)}"))
        img = locals().get(f"MANUAL_IMG{str(i).zfill(2)}")
        print(f"MANUAL_IMG{str(i).zfill(2)}:", img.filename if img and hasattr(img, "filename") else img)

    manual_texts = [
        MANUAL01 or "", MANUAL02 or "", MANUAL03 or "", MANUAL04 or "", MANUAL05 or "",
        MANUAL06 or "", MANUAL07 or "", MANUAL08 or "", MANUAL09 or "", MANUAL10 or "",
        MANUAL11 or "", MANUAL12 or "", MANUAL13 or "", MANUAL14 or "", MANUAL15 or "",
        MANUAL16 or "", MANUAL17 or "", MANUAL18 or "", MANUAL19 or "", MANUAL20 or "",
    ]
    manual_imgs_raw = [
        MANUAL_IMG01, MANUAL_IMG02, MANUAL_IMG03, MANUAL_IMG04, MANUAL_IMG05,
        MANUAL_IMG06, MANUAL_IMG07, MANUAL_IMG08, MANUAL_IMG09, MANUAL_IMG10,
        MANUAL_IMG11, MANUAL_IMG12, MANUAL_IMG13, MANUAL_IMG14, MANUAL_IMG15,
        MANUAL_IMG16, MANUAL_IMG17, MANUAL_IMG18, MANUAL_IMG19, MANUAL_IMG20,
    ]
    manual_imgs = [img if img and hasattr(img, "filename") else None for img in manual_imgs_raw]

    data = {
        "name": name,
        "description": description or "",
        "ingredients": ingredients,
        "INFO_ENG": INFO_ENG or "",
        "INFO_CAR": INFO_CAR or "",
        "INFO_PRO": INFO_PRO or "",
        "INFO_FAT": INFO_FAT or "",
        "INFO_NA": INFO_NA or "",
        "RCP_NA_TIP": RCP_NA_TIP or "",
        **{f"MANUAL{str(i).zfill(2)}": manual_texts[i-1] for i in range(1, 21)},
    }

    new_id = await service.create_user_recipe(
        user_id,
        data,
        image_file=image_url,
        manual_imgs=manual_imgs
    )
    return new_id




@router.get("/recipes/search", response_model=List[UserRecipeOut])
async def search_all_public_recipes(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    query = db.query(UserRecipe).filter(UserRecipe.name.contains(q))
    recipes = query.order_by(UserRecipe.created_at.desc()).all()
    if not recipes:
        raise HTTPException(status_code=404, detail="검색된 레시피가 없습니다.")
    return recipes


@router.get("/{user_id}/recipes", response_model=List[UserRecipeOut])
async def get_user_recipes(user_id: str, db: Session = Depends(get_db)):
    # UserRecipe와 User (작성자)를 조인하여 ko_name(author_name)도 가져오기
    results = (
        db.query(UserRecipe, User.ko_name.label("author_name"))
        .join(User, UserRecipe.user_id == User.user_id)
        .filter(UserRecipe.user_id == user_id)
        .order_by(UserRecipe.created_at.desc())
        .all()
    )

    response = []
    for recipe, author_name in results:
        recipe_dict = recipe.__dict__.copy()
        recipe_dict["author_name"] = author_name
        # 메뉴얼 빈 항목 제거 함수가 있다면 적용
        filtered_recipe = filter_non_empty_manuals(recipe_dict)
        response.append(filtered_recipe)

    return response


@router.get("/{user_id}/recipes/{recipe_id}", response_model=UserRecipeOut)
async def get_one_user_recipe(user_id: str, recipe_id: int, db: Session = Depends(get_db)):
    # 작성자 이름 포함 조인 쿼리
    result = (
        db.query(UserRecipe, User.ko_name.label("author_name"))
        .join(User, UserRecipe.user_id == User.user_id)
        .filter(UserRecipe.user_id == user_id, UserRecipe.id == recipe_id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe, author_name = result

    # recipe를 dict로 변환하고 author_name 추가
    recipe_dict = recipe.__dict__.copy()
    recipe_dict["author_name"] = author_name

    # 메뉴얼 빈 항목 제거
    filtered_recipe = filter_non_empty_manuals(recipe_dict)

    return filtered_recipe


@router.patch("/{user_id}/recipes/{recipe_id}")
async def update_user_recipe(user_id: str, recipe_id: int, recipe_update: UserRecipeUpdate, db: Session = Depends(get_db)):
    await service.update_user_recipe(user_id, recipe_id, recipe_update.dict(exclude_unset=True))
    return {"message": "Recipe updated"}


@router.delete("/{user_id}/recipes/{recipe_id}")
async def delete_user_recipe(user_id: str, recipe_id: int, db: Session = Depends(get_db)):
    await service.delete_user_recipe(user_id, recipe_id)
    return {"message": "Recipe deleted"}


@router.post("/recipes/{user_recipe_id}/rating")
def rate_user_recipe(user_recipe_id: int, req: RatingRequest, db: Session = Depends(get_db)):
    try:
        # 함수 호출 로그 출력
        print(f"rate_user_recipe 호출됨 user_recipe_id={user_recipe_id}, user_id={req.user_id}, rating={req.rating}")

        recipe = add_or_update_rating(
            user_id=req.user_id,
            score=req.rating,
            recipe_id=None,
            user_recipe_id=user_recipe_id,
            db=db,
        )

        print(f"add_or_update_rating 반환: recipe.avg_rating={recipe.avg_rating}, rating_count={recipe.rating_count}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    avg = db.query(Rating).filter_by(user_recipe_id=user_recipe_id).with_entities(func.avg(Rating.rating)).scalar()
    count = db.query(Rating).filter_by(user_recipe_id=user_recipe_id).count()

    recipe.avg_rating = round(avg or 0, 2)
    recipe.rating_count = count
    db.commit()
    db.refresh(recipe)

    return {"success": True, "avg_rating": recipe.avg_rating, "rating_count": recipe.rating_count}



@router.get("/recipes/{recipe_id}")
def get_user_recipe_detail(
    recipe_id: int,
    user_id: str = Query(None),
    increment_view: bool = Query(True),
    db: Session = Depends(get_db),
):
    recipe = db.query(UserRecipe).filter(UserRecipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="사용자 레시피를 찾을 수 없습니다.")

    if increment_view:
        recipe.view_count = (recipe.view_count or 0) + 1
        recipe.updated_at = datetime.now()
        db.commit()
        db.refresh(recipe)

    user_rating = 0
    if user_id:
        rating_obj = db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.user_recipe_id == recipe_id
        ).first()
        if rating_obj:
            user_rating = rating_obj.rating

        print(f"[DEBUG] user_id={user_id}, recipe_id={recipe_id}, user_rating={user_rating}")

    recipe_dict = recipe.__dict__.copy()
    recipe_dict["user_rating"] = user_rating

    return recipe_dict



