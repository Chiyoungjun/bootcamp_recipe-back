from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File, Query
from typing import List, Optional

from .service import UserService
from .schemas import UserRecipeOut, UserRecipeUpdate, UserRecipeDetailOut

# 사용자 전용 라우터 (/api/users 로 include)
router = APIRouter()
# 퍼블릭 호환 라우터 (/api 로 include → /api/userrecipedetail 지원)
public_router = APIRouter()

service = UserService()

# ------------------------------
# 내부 헬퍼: steps/step_images 생성
# ------------------------------
def _attach_steps_and_images(payload: dict) -> dict:
    """
    DB에서 읽어온 dict(payload)에 steps/step_images를 생성해 넣고,
    원본 MANUALxx / MANUAL_IMGxx 키는 제거한다.
    이미 steps가 존재하면 덮어쓰지 않음(빈 배열이거나 없을 때만 생성).
    """
    resp = dict(payload)

    need_make_steps = not resp.get("steps")
    if need_make_steps:
        steps = [resp.get(f"MANUAL{str(i).zfill(2)}") for i in range(1, 21)]
        # None/공백 제거 + str로 방어
        steps = [str(s).strip() for s in steps if s is not None and str(s).strip() != ""]
        resp["steps"] = steps

        step_images = [resp.get(f"MANUAL_IMG{str(i).zfill(2)}") for i in range(1, 21)]
        step_images = [str(img).strip() for img in step_images if img is not None and str(img).strip() != ""]
        # 단계 수에 맞춰 자르기
        resp["step_images"] = step_images[:len(steps)]

    # 페이로드 정리: 원본 MANUAL 키 제거(응답 모델과 중복 방지)
    for i in range(1, 21):
        resp.pop(f"MANUAL{str(i).zfill(2)}", None)
        resp.pop(f"MANUAL_IMG{str(i).zfill(2)}", None)

    return resp


# ------------------------------
# 내부 헬퍼: 상세 조회 공용 처리
# ------------------------------
async def _get_user_recipe_detail_core(
    *, recipe_id: int, user_id: Optional[str], lang: str = "ko", increment_view: bool = True
) -> UserRecipeDetailOut:
    try:
        recipe = await service.get_user_recipe_detail(
            recipe_id=recipe_id, user_id=user_id, lang=lang, increment_view=increment_view
        )
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # ← 여기서 steps/step_images를 보장
        hydrated = _attach_steps_and_images(recipe)
        return hydrated  # response_model이 UserRecipeDetailOut이므로 필드만 통과
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================
# 0) 루트: 단순 조회
# ========================================================
@router.get("/")
async def get_users():
    try:
        data = await service.get_users()
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================
# 1) 고정/정적 경로 (위쪽 배치)
# ========================================================
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


# ========================================================
# 2) 사용자 레시피 상세 조회 (정적 경로) — users prefix
#    /api/users/userrecipedetail
# ========================================================
@router.get("/userrecipedetail", response_model=UserRecipeDetailOut)
async def get_user_recipe_detail_on_users_prefix(
    id: int = Query(..., alias="id"),
    user_id: Optional[str] = Query(None),
    lang: Optional[str] = Query("ko"),
    increment_view: Optional[bool] = Query(True),
):
    return await _get_user_recipe_detail_core(
        recipe_id=id, user_id=user_id, lang=lang, increment_view=increment_view
    )


# ========================================================
# 2-1) 퍼블릭 호환 라우터에도 동일 엔드포인트 노출
#      /api/userrecipedetail
# ========================================================
@public_router.get("/userrecipedetail", response_model=UserRecipeDetailOut)
async def get_user_recipe_detail_public(
    id: int = Query(..., alias="id"),
    user_id: Optional[str] = Query(None),
    lang: Optional[str] = Query("ko"),
    increment_view: Optional[bool] = Query(True),
):
    return await _get_user_recipe_detail_core(
        recipe_id=id, user_id=user_id, lang=lang, increment_view=increment_view
    )


# ========================================================
# 3) 세그먼트 많은 경로 (유저 레시피 관련)
# ========================================================
@router.get("/{user_id}/recipes/search", response_model=List[UserRecipeOut])
async def search_user_recipes(
    user_id: str,
    q: str = Query(..., min_length=1, max_length=50),
):
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


@router.post("/{user_id}/recipes", response_model=int)
async def create_user_recipe(
    user_id: str,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image_url: Optional[UploadFile] = File(None),

    # 단계 텍스트(기존 방식: MANUAL01~20)
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

    # 단계 이미지(기존 방식)
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

    # ✅ 새 입력 방식: 프론트가 JSON 문자열로 보내면 서비스에서 팬아웃
    steps_json: Optional[str] = Form(None),
    step_images_json: Optional[str] = Form(None),
):
    # 텍스트/이미지 일괄 수집(기존)
    manual_texts = [locals().get(f"MANUAL{str(i).zfill(2)}") or "" for i in range(1, 21)]
    manual_imgs = [locals().get(f"MANUAL_IMG{str(i).zfill(2)}") for i in range(1, 21)]

    # ✅ payload를 딕셔너리로 만들고, MANUAL01~20은 dict 확장으로 한 번에 삽입
    payload = {
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
        # 기존 MANUAL 텍스트도 함께 전달(있으면 우선 적용)
        **{f"MANUAL{str(i).zfill(2)}": manual_texts[i - 1] for i in range(1, 21)},
    }

    # 프론트에서 온 JSON 문자열(옵션)을 전달 → service가 파싱 후 MANUAL01~20으로 팬아웃
    if steps_json is not None:
        payload["steps_json"] = steps_json
    if step_images_json is not None:
        payload["step_images_json"] = step_images_json

    new_id = await service.create_user_recipe(
        user_id,
        payload,
        image_file=image_url,
        manual_imgs=manual_imgs,
    )
    return new_id


@router.patch("/{user_id}/recipes/{recipe_id}")
async def update_user_recipe(user_id: str, recipe_id: int, recipe_update: UserRecipeUpdate):
    await service.update_user_recipe(user_id, recipe_id, recipe_update.dict(exclude_unset=True))
    return {"message": "Recipe updated"}


@router.delete("/{user_id}/recipes/{recipe_id}")
async def delete_user_recipe(user_id: str, recipe_id: int):
    await service.delete_user_recipe(user_id, recipe_id)
    return {"message": "Recipe deleted"}


# ========================================================
# 4) 가장 범용적인 단일 파라미터 경로는 맨 아래
# ========================================================
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


@router.patch("/{user_id}")
async def update_user(user_id: str, request: Request):
    update_info = await request.json()
    try:
        data = await service.update_user(user_id, update_info)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
