from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Rating, Recipe, RecipeRatingHistories, PeriodTypeEnum
from service.recipe_service import (
    get_recipe, get_recipe_detail, get_recipe_list,
    increase_recipe_view_count, add_or_update_rating
)
from sqlalchemy import desc
from datetime import date, timedelta

router = APIRouter()

# 평점 입력용 데이터 모델
class RatingRequest(BaseModel):
    user_id: int
    rating: int  # 1~5 점 사이여야 함


@router.get("/recipes/external/search")
def search_recipes(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    recipes = get_recipe(q, db)
    if not recipes:
        raise HTTPException(404, "레시피가 없습니다.")
    return recipes


@router.get("/recipedetail")
def recipe_detail(
    id: int = Query(...),
    user_id: int = Query(None),
    db: Session = Depends(get_db),
):
    recipe = increase_recipe_view_count(id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")

    user_rating = 0
    if user_id is not None:
        rating_entry = db.query(Rating).filter_by(recipe_id=id, user_id=user_id).first()
        if rating_entry:
            user_rating = rating_entry.rating

    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description,
        "image_url": recipe.image_url,
        "category": recipe.category,
        "ingredients": recipe.ingredients.split(",") if recipe.ingredients else [],
        "INFO_ENG": recipe.INFO_ENG,
        "INFO_CAR": recipe.INFO_CAR,
        "INFO_PRO": recipe.INFO_PRO,
        "INFO_FAT": recipe.INFO_FAT,
        "INFO_NA": recipe.INFO_NA,
        "RCP_NA_TIP": recipe.RCP_NA_TIP,
        "avg_rating": float(recipe.avg_rating or 0),
        "rating_count": recipe.rating_count or 0,
        "view_count": recipe.view_count or 0,
        "user_rating": user_rating,
    }


@router.get("/recipelist")
def recipe_list(db: Session = Depends(get_db)):
    return get_recipe_list(db)


@router.post("/recipes/{recipe_id}/view")
def view_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = increase_recipe_view_count(recipe_id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")
    return {"view_count": recipe.view_count}


@router.post("/recipes/{recipe_id}/rating")
def rate_recipe(recipe_id: int, rating: RatingRequest, db: Session = Depends(get_db)):
    if not (1 <= rating.rating <= 5):
        raise HTTPException(400, "별점은 1~5점 사이여야 합니다.")

    try:
        recipe = add_or_update_rating(recipe_id, rating.user_id, rating.rating, db)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

    return {
        "avg_rating": float(recipe.avg_rating),
        "rating_count": recipe.rating_count
    }


# 랭킹 조회용 API - 일간, 주간, 월간 별점을 기준으로 상위 레시피 반환
@router.get("/rankings")
def get_rankings(
    period: str = Query(..., regex="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
):
    today = date.today()

    # period 문자열을 Enum으로 변환
    try:
        period_enum = PeriodTypeEnum(period)
    except ValueError:
        raise HTTPException(400, "Invalid period")

    # 기간별 시작일 계산
    if period_enum == PeriodTypeEnum.daily:
        period_start_date = today
    elif period_enum == PeriodTypeEnum.weekly:
        period_start_date = today - timedelta(days=today.weekday())  # 이번 주 월요일
    elif period_enum == PeriodTypeEnum.monthly:
        period_start_date = today.replace(day=1)
    else:
        raise HTTPException(400, "Invalid period")

    avg_rating_expr = RecipeRatingHistories.rating_sum / RecipeRatingHistories.rating_count

    rankings = (
        db.query(Recipe, RecipeRatingHistories)
        .join(RecipeRatingHistories, Recipe.id == RecipeRatingHistories.recipe_id)
        .filter(
            RecipeRatingHistories.period_type == period_enum,
            RecipeRatingHistories.period_start_date == period_start_date,
            RecipeRatingHistories.rating_count > 0,
        )
        .order_by(desc(avg_rating_expr))
        .limit(10)
        .all()
    )

    result = []
    for recipe, rating_hist in rankings:
        result.append({
            "id": recipe.id,
            "name": recipe.name,
            "image_url": recipe.image_url,
            "avg_rating": float(rating_hist.rating_sum / rating_hist.rating_count),
            "rating_count": rating_hist.rating_count,
            "view_count": recipe.view_count or 0,
        })

    return {"recipes": result}

@router.get("/recipes")
def get_recipes(
    category: str = Query(None),
    search: str = Query(None),
    page: int = Query(1),
    db: Session = Depends(get_db),
):
    query = db.query(Recipe)

    if category and category != "전체":
        query = query.filter(Recipe.category == category)

    if search:
        query = query.filter(Recipe.name.contains(search))

    page_size = 10
    recipes = query.offset((page - 1) * page_size).limit(page_size).all()

    result = [
        {
            "id": r.id,
            "name": r.name,
            "image_url": r.image_url,
            "category": r.category,
            "avg_rating": float(r.avg_rating or 0),
            "rating_count": r.rating_count or 0,
            "view_count": r.view_count or 0,
        }
        for r in recipes
    ]
    return {"recipes": result}

