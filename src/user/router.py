from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from typing import List, Optional

from .service import UserService
from .schemas import UserRecipeOut, UserRecipeUpdate
from fastapi import Query

router = APIRouter()
service = UserService()


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


@router.post("/{user_id}/recipes", response_model=int)
async def create_user_recipe(
    user_id: str,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image_url: Optional[UploadFile] = File(None),

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

    category: Optional[str] = Form(None),

    ingredients: str = Form(...),

    INFO_ENG: Optional[str] = Form(None),
    INFO_CAR: Optional[str] = Form(None),
    INFO_PRO: Optional[str] = Form(None),
    INFO_FAT: Optional[str] = Form(None),
    INFO_NA: Optional[str] = Form(None),

    RCP_NA_TIP: Optional[str] = Form(None),
):
    manual_texts = [locals().get(f"MANUAL{str(i).zfill(2)}") or "" for i in range(1, 21)]
    manual_imgs = [locals().get(f"MANUAL_IMG{str(i).zfill(2)}") for i in range(1, 21)]

    new_id = await service.create_user_recipe(
        user_id,
        {
            "name": name,
            "description": description or "",
            "category": category or "",
            "ingredients": ingredients,
            "INFO_ENG": INFO_ENG or "",
            "INFO_CAR": INFO_CAR or "",
            "INFO_PRO": INFO_PRO or "",
            "INFO_FAT": INFO_FAT or "",
            "INFO_NA": INFO_NA or "",
            "RCP_NA_TIP": RCP_NA_TIP or "",
            **{f"MANUAL{str(i).zfill(2)}": manual_texts[i-1] for i in range(1, 21)},
        },
        image_file=image_url,
        manual_imgs=manual_imgs
    )
    return new_id

@router.get("/{user_id}/recipes/search", response_model=List[UserRecipeOut])
async def search_user_recipes(
    user_id: str,            # 숫자나 문자 모두 가능
    q: str = Query(..., min_length=1, max_length=50)
):
    # service에서 사용자 레시피 중 검색어 q가 포함된 레시피만 필터링하여 반환
    recipes = await service.search_user_recipes(user_id, q)
    return recipes

@router.get("/{user_id}/recipes", response_model=List[UserRecipeOut])
async def get_user_recipes(user_id: str):
    recipes = await service.get_user_recipes(user_id)
    return recipes


@router.get("/{user_id}/recipes/{recipe_id}", response_model=UserRecipeOut)
async def get_one_user_recipe(user_id: str, recipe_id: int):
    recipe = await service.get_user_recipe(user_id, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.patch("/{user_id}/recipes/{recipe_id}")
async def update_user_recipe(user_id: str, recipe_id: int, recipe_update: UserRecipeUpdate):
    await service.update_user_recipe(user_id, recipe_id, recipe_update.dict(exclude_unset=True))
    return {"message": "Recipe updated"}


@router.delete("/{user_id}/recipes/{recipe_id}")
async def delete_user_recipe(user_id: str, recipe_id: int):
    await service.delete_user_recipe(user_id, recipe_id)
    return {"message": "Recipe deleted"}


