from fastapi import APIRouter, Query, HTTPException
from service.recipe_service import get_recipe, get_recipe_detail, get_recipe_list

router = APIRouter()

@router.get("/recipes/external/search")
def search_external_recipes(q: str = Query(..., min_length=1, description="검색어")):
    return get_recipe(q)

@router.get("/recipedetail")
def recipe_detail(id: int = Query(..., description="레시피 고유 ID(RCP_SEQ)")):
    result = get_recipe_detail(id)
    if not result:
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")
    return result

# ===========================
# ★ 전체 레시피 반환 API 추가 (/recipelist)
# 프론트에서 이걸 호출해 전체 데이터 기반 유사레시피 추출
# ===========================
@router.get("/recipelist")
def recipe_list():
    return get_recipe_list()