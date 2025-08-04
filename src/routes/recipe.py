from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import (
    Rating, Recipe, RecipeRatingHistories, PeriodTypeEnum,
    UserSearchHistory, UserBmiRecommendation, UserDetail
)
from service.recipe_service import (
    get_recipe, get_recipe_detail, get_recipe_list,
    increase_recipe_view_count, add_or_update_rating
)
from sqlalchemy import desc
from datetime import date, timedelta

router = APIRouter()

# BMI 분류 함수 (추천 등급 구분용)
def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상"
    elif bmi < 25:
        return "과체중"
    else:
        return "비만"

# --------------------
# 평점 입력용 Pydantic 모델
# --------------------
class RatingRequest(BaseModel):
    user_id: str         # int → str!
    rating: int          # 1~5 점 사이여야 함

# --------------------
# 사용자 검색 이력 저장용 Pydantic 모델
# --------------------
class SearchHistoryRequest(BaseModel):
    user_id: str         # int → str!
    search_word: str

# --------------------
# BMI 저장용 Pydantic 모델
# --------------------
class BmiRecommendationRequest(BaseModel):
    user_id: str          # int → str!
    height: float
    weight: float
    recommended_recipes: str = None

# --------------------
# 레시피 외부 검색 API
# --------------------
@router.get("/recipes/external/search")
def search_recipes(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    recipes = get_recipe(q, db)
    if not recipes:
        raise HTTPException(404, "레시피가 없습니다.")
    return recipes

# --------------------
# 레시피 상세 정보 API
# --------------------
@router.get("/recipedetail")
def recipe_detail(
    id: int = Query(...),
    user_id: str = Query(None),     # int → str
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

# --------------------
# 레시피 리스트 조회 API
# --------------------
@router.get("/recipelist")
def recipe_list(db: Session = Depends(get_db)):
    return get_recipe_list(db)

# --------------------
# 레시피 조회수 증가 API
# --------------------
@router.post("/recipes/{recipe_id}/view")
def view_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = increase_recipe_view_count(recipe_id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")
    return {"view_count": recipe.view_count}

# --------------------
# 레시피 별점 입력 API
# --------------------
@router.post("/recipes/{recipe_id}/rating")
def rate_recipe(recipe_id: int, rating: RatingRequest, db: Session = Depends(get_db)):
    if not (1 <= rating.rating <= 5):
        raise HTTPException(400, "별점은 1~5점 사이여야 합니다.")

    try:
        # user_id: int → str
        recipe = add_or_update_rating(recipe_id, rating.user_id, rating.rating, db)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

    return {
        "avg_rating": float(recipe.avg_rating),
        "rating_count": recipe.rating_count
    }

# --------------------
# 랭킹 조회 API
# --------------------
@router.get("/rankings")
def get_rankings(
    period: str = Query(..., regex="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
):
    today = date.today()

    try:
        period_enum = PeriodTypeEnum(period)
    except ValueError:
        raise HTTPException(400, "Invalid period")

    if period_enum == PeriodTypeEnum.daily:
        period_start_date = today
    elif period_enum == PeriodTypeEnum.weekly:
        period_start_date = today - timedelta(days=today.weekday())
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

# --------------------
# 카테고리 & 검색어 페이징 조회 API
# --------------------
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

# --------------------
# 사용자 검색 기록 저장 API
# --------------------
@router.post("/search-history")
def add_search_history(
    request: SearchHistoryRequest,
    db: Session = Depends(get_db)
):
    history = UserSearchHistory(
        user_id=request.user_id,
        search_word=request.search_word
    )
    db.add(history)
    db.commit()          # await 없이 그냥!
    db.refresh(history)  # (선택) 저장된 행 다시 읽어서 갱신
    return {"message": "Search history saved"}

# --------------------
# 사용자 BMI 저장 및 추천 API
# --------------------
@router.post("/user/profile/bmi-recommendation")
def save_bmi_recommendation(
    request: BmiRecommendationRequest,
    db: Session = Depends(get_db)
):
    bmi = request.weight / ((request.height / 100) ** 2)

    recommendation = UserBmiRecommendation(
        user_id=request.user_id,
        height=request.height,
        weight=request.weight,
        bmi_value=round(bmi, 2),
        recommended_recipes=request.recommended_recipes
    )
    db.add(recommendation)
    db.commit()
    return {"message": "BMI recommendation saved", "bmi": round(bmi, 2)}

# ---------------------------------
# 사용자 선호 기반 추천 API (예시)
# ---------------------------------
@router.get("/recommendations/user-preferences")
def get_user_preference_recommendations(
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db),
):
    # 사용자 검색 기록에서 최근 5개 키워드 조회
    recent_searches = (
        db.query(UserSearchHistory.search_word)
        .filter(UserSearchHistory.user_id == user_id)
        .order_by(UserSearchHistory.search_time.desc())
        .limit(5)
        .all()
    )
    keywords = [kw for (kw,) in recent_searches]

    if not keywords:
        # 검색 기록 없는 사용자는 추천 안함 (빈 리스트 반환)
        return {"recipes": []}

    from sqlalchemy import or_

    like_conditions = [Recipe.name.ilike(f"%{kw}%") for kw in keywords]
    query = db.query(Recipe).filter(or_(*like_conditions))

    recipes = query.order_by(Recipe.view_count.desc()).limit(10).all()

    if len(recipes) < 10:
        needed = 10 - len(recipes)
        popular_recipes = (
            db.query(Recipe)
            .filter(~Recipe.id.in_([r.id for r in recipes]))
            .order_by(Recipe.view_count.desc())
            .limit(needed)
            .all()
        )
        recipes.extend(popular_recipes)

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


# ---------------------------------
# BMI 기반 추천 API
# ---------------------------------
@router.get("/recommendations/bmi")
def get_bmi_recommendations(
    user_id: str = Query(..., description="사용자 ID"),   # int → str
    db: Session = Depends(get_db),
):
    # 사용자 신체정보 조회
    user_profile = db.query(UserDetail).filter_by(user_id=user_id).first()
    if not user_profile or not user_profile.height or not user_profile.weight:
        raise HTTPException(400, "사용자 신체 정보(키, 몸무게)가 필요합니다.")

    bmi = float(user_profile.weight) / ((float(user_profile.height) / 100) ** 2)
    bmi_class = classify_bmi(bmi)

    # BMI 분류별 추천 로직 - 예시
    if bmi_class == "저체중":
        query = db.query(Recipe).filter(Recipe.category.in_(["밥", "구이, 찜"])).order_by(Recipe.INFO_ENG.desc())
    elif bmi_class == "정상":
        query = db.query(Recipe).order_by(Recipe.view_count.desc())
    elif bmi_class == "과체중":
        query = db.query(Recipe).filter(Recipe.category.in_(["샐러드", "국, 찌개", "반찬"])).order_by(Recipe.INFO_ENG.asc())
    else:  # 비만
        query = db.query(Recipe).filter(Recipe.category.in_(["샐러드", "반찬"])).order_by(Recipe.INFO_ENG.asc())

    recipes = query.limit(10).all()

    result = [{
        "id": r.id,
        "name": r.name,
        "image_url": r.image_url,
        "category": r.category,
        "avg_rating": float(r.avg_rating or 0),
        "rating_count": r.rating_count or 0,
        "view_count": r.view_count or 0,
    } for r in recipes]

    return {
        "bmi": round(bmi, 2),
        "bmi_category": bmi_class,
        "recipes": result,
    }
