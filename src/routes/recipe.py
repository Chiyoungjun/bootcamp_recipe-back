from fastapi import APIRouter, Query, HTTPException
from service.recipe_service import get_recipe, get_recipe_detail

router = APIRouter()

@router.get("/recipes/external/search")
def search_external_recipes(q: str = Query(..., min_length=1, description="검색어")):
    return get_recipe(q)

@router.get("/recipedetail")
def recipe_detail(
    id: int = Query(..., description="레시피 고유 ID (RCP_SEQ)"),
    food_name: str = Query(..., description="음식명 (RCP_NM)")
):
    recipe = get_recipe_detail(id, food_name)
    if not recipe:
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")
    return recipe
