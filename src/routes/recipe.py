# src/routes/recipe.py
from fastapi import APIRouter, Query
from service.recipe_service import get_recipe

router = APIRouter()

@router.get("/recipes/external/search")  # 기존 경로와 동일하게 맞춰주세요
def search_external_recipes(q: str = Query(..., min_length=1, description="검색어")):
    return get_recipe(q)
