from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from service.recipe_service import (
    get_recipe, get_recipe_detail, get_recipe_list,
    increase_recipe_view_count, add_or_update_rating
)
from database import get_db
from pydantic import BaseModel

router = APIRouter()

@router.get("/recipes/external/search")
def search_recipes(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    recipes = get_recipe(q, db)
    if not recipes:
        raise HTTPException(404, "레시피가 없습니다.")
    return recipes

@router.get("/recipedetail")
def recipe_detail(id: int = Query(...), db: Session = Depends(get_db)):
    recipe = get_recipe_detail(id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")
    return recipe

@router.get("/recipelist")
def recipe_list(db: Session = Depends(get_db)):
    return get_recipe_list(db)

@router.post("/recipes/{recipe_id}/view")
def view_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = increase_recipe_view_count(recipe_id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")
    return {"view_count": recipe.view_count}

class RatingRequest(BaseModel):
    user_id: int
    rating: int  # 1~5

@router.post("/recipes/{recipe_id}/rating")
def rate_recipe(recipe_id: int, rating: RatingRequest, db: Session = Depends(get_db)):
    if not (1 <= rating.rating <= 5):
        raise HTTPException(400, "별점은 1~5점이어야 합니다.")
    recipe = add_or_update_rating(recipe_id, rating.user_id, rating.rating, db)
    return {
        "avg_rating": float(recipe.avg_rating),
        "rating_count": recipe.rating_count
    }


# from fastapi import APIRouter, Query, HTTPException
# from service.recipe_service import get_recipe, get_recipe_detail, get_recipe_list

# router = APIRouter()

# @router.get("/recipes/external/search")
# def search_external_recipes(q: str = Query(..., min_length=1, description="검색어")):
#     return get_recipe(q)

# @router.get("/recipedetail")
# def recipe_detail(id: int = Query(..., description="레시피 고유 ID(RCP_SEQ)")):
#     result = get_recipe_detail(id)
#     if not result:
#         raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")
#     return result

# @router.get("/recipelist")
# def recipe_list():
#     return get_recipe_list()
