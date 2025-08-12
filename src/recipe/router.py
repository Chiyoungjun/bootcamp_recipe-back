from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, distinct, desc
from pydantic import BaseModel
from database import get_db

# recipe 폴더 내 models
from .models import (
    Rating, Recipe, RecipeRatingHistories, PeriodTypeEnum
)

# user 폴더 내 models
from user.models import (
    UserSearchHistory, UserBmiRecommendation, UserDetail, UserFavorites
)

# service 모듈 전체 import
from . import service

# schemas 불러오기
from .schemas import (
    RatingRequest, FavoriteRequest, SearchHistoryRequest, BmiRecommendationRequest
)

from datetime import date, timedelta, datetime
import shutil
import os
from collections import Counter
from ai.ai_model import model
from typing import List

router = APIRouter()


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상"
    elif bmi < 25:
        return "과체중"
    else:
        return "비만"


@router.post("/favorites")
def favorite_recipe(request: FavoriteRequest, db: Session = Depends(get_db)):
    try:
        fav = service.add_to_favorites(request.user_id, request.recipe_id, db)
        return {"message": "레시피를 즐겨찾기(찜) 추가했습니다."}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.delete("/favorites")
def unfavorite_recipe(request: FavoriteRequest, db: Session = Depends(get_db)):
    try:
        service.remove_from_favorites(request.user_id, request.recipe_id, db)
        return {"message": "레시피 즐겨찾기(찜) 해제 성공"}
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@router.get("/favorites/{user_id}")
def get_favorites(user_id: str, db: Session = Depends(get_db)):
    recipes = service.get_user_favorites(user_id, db)
    result = [{
        "id": r.id,
        "name": r.name,
        "image_url": r.image_url,
        "category": r.category,
        "avg_rating": float(r.avg_rating or 0),
        "rating_count": r.rating_count or 0,
        "view_count": r.view_count or 0,
    } for r in recipes if r]
    return {"favorites": result}


@router.get("/recipes/external/search")
def search_recipes(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    recipes = service.get_recipe(q, db)
    if not recipes:
        raise HTTPException(404, "레시피가 없습니다.")
    return recipes


@router.get("/recipedetail")
def recipe_detail(
    id: int = Query(...),
    user_id: str = Query(None),
    increment_view: bool = Query(True),
    db: Session = Depends(get_db),
):
    if increment_view:
        recipe = service.increase_recipe_view_count(id, db)
    else:
        recipe = db.query(Recipe).filter_by(id=id).first()
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
        **{f"MANUAL{str(i).zfill(2)}": getattr(recipe, f"MANUAL{str(i).zfill(2)}") for i in range(1, 21)},
        **{f"MANUAL_IMG{str(i).zfill(2)}": getattr(recipe, f"MANUAL_IMG{str(i).zfill(2)}") for i in range(1, 21)},
    }


@router.get("/recipelist")
def recipe_list(db: Session = Depends(get_db)):
    return service.get_recipe_list(db)


@router.post("/recipes/{recipe_id}/view")
def view_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = service.increase_recipe_view_count(recipe_id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")
    return {"view_count": recipe.view_count}


@router.post("/recipes/{recipe_id}/rating")
def rate_recipe(recipe_id: int, rating: RatingRequest, db: Session = Depends(get_db)):
    if not (1 <= rating.rating <= 5):
        raise HTTPException(400, "별점은 1~5점 사이여야 합니다.")

    try:
        recipe = service.add_or_update_rating(recipe_id, rating.user_id, rating.rating, db)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

    return {
        "avg_rating": float(recipe.avg_rating),
        "rating_count": recipe.rating_count
    }


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


@router.get("/recommendations/bmi")
def get_bmi_recommendations(
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db),
):
    user_profile = db.query(UserDetail).filter_by(user_id=user_id).first()
    if not user_profile or not user_profile.height or not user_profile.weight:
        raise HTTPException(400, "사용자 신체 정보(키, 몸무게)가 필요합니다.")

    bmi = float(user_profile.weight) / ((float(user_profile.height) / 100) ** 2)
    bmi_class = classify_bmi(bmi)

    if bmi_class == "저체중":
        query = db.query(service.Recipe).filter(service.Recipe.category.in_(["밥", "구이, 찜"])).order_by(service.Recipe.INFO_ENG.desc())
    elif bmi_class == "정상":
        query = db.query(service.Recipe).order_by(service.Recipe.view_count.desc())
    elif bmi_class == "과체중":
        query = db.query(service.Recipe).filter(service.Recipe.category.in_(["샐러드", "국, 찌개", "반찬"])).order_by(service.Recipe.INFO_ENG.asc())
    else:
        query = db.query(service.Recipe).filter(service.Recipe.category.in_(["샐러드", "반찬"])).order_by(service.Recipe.INFO_ENG.asc())

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


@router.post("/recipes/upload")
async def upload_recipe_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, image.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"파일 저장 실패: {str(e)}")

    try:
        results = model(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(500, f"YOLO 추론 실패: {str(e)}")

    food_names = []
    names = model.names
    for r in results:
        if hasattr(r, "boxes"):
            for box in r.boxes:
                class_id = int(box.cls[0])
                label = names[class_id]
                food_names.append(label)

    print(f"[DEBUG] Detected food names from image: {food_names}")

    os.remove(file_path)

    if not food_names:
        raise HTTPException(404, "이미지에서 음식을 인식하지 못했습니다.")

    common_food_name = Counter(food_names).most_common(1)[0][0]

    if "_" in common_food_name:
        _, search_name = common_food_name.split("_", 1)
    else:
        search_name = common_food_name

    print(f"[DEBUG] Representative food name used for DB search: {search_name}")

    recipes = service.get_recipe(search_name, db)
    if not recipes:
        raise HTTPException(404, f"{search_name} 기반 검색 결과가 없습니다.")

    return recipes

# 사용자 선호 기반 추천 API (예시)
@router.get("/recommendations/user-preferences")
def get_user_preference_recommendations(
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db),
):
    # 1. 사용자의 최근 검색어 5개 가져오기
    recent_searches = (
        db.query(UserSearchHistory.search_word)
        .filter(UserSearchHistory.user_id == user_id)
        .order_by(UserSearchHistory.search_time.desc())
        .limit(5)
        .all()
    )
    keywords = [kw for (kw,) in recent_searches]

    # 검색어 없으면 빈 리스트 즉시 반환
    if not keywords:
        return {"recipes": []}

    # 2. 검색어별 해당 레시피들의 카테고리 모두 추출
    categories_query = (
        db.query(distinct(Recipe.category))
        .filter(
            or_(*[Recipe.name.ilike(f"%{kw}%") for kw in keywords])
        )
    )
    categories = [c for (c,) in categories_query.all()]

    if not categories:
        # 검색어에 해당하는 레시피가 없으면 빈 리스트 반환 혹은 기본 추천
        return {"recipes": []}

    # 3. 추출한 복수 카테고리에 해당하는 레시피를 모두 조회, 인기순 정렬
    query = db.query(Recipe).filter(Recipe.category.in_(categories))
    recipes = query.order_by(Recipe.view_count.desc()).limit(10).all()

    # 4. 추천할 레시피가 부족하면 인기 레시피로 보충
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

    # 5. 결과 가공
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

# 사용자 검색 기록 저장 API
@router.post("/search-history")
def add_search_history(
    request: SearchHistoryRequest,
    db: Session = Depends(get_db)
):
    history = UserSearchHistory(
        user_id=request.user_id,
        recipe_id=request.recipe_id,   # 반드시 포함할 것
        search_word=request.search_word,
        search_time=datetime.now()
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return {"message": "Search history saved"}

@router.get("/search-history/{user_id}")
def get_search_history(
    user_id: str,
    page: int = 1,
    items_per_page: int = 10,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * items_per_page

    # 총 검색 기록 개수
    total_count = db.query(UserSearchHistory).filter(
        UserSearchHistory.user_id == user_id
    ).count()

    # 페이징 검색 기록
    histories = (
        db.query(UserSearchHistory)
        .filter(UserSearchHistory.user_id == user_id)
        .order_by(UserSearchHistory.search_time.desc())
        .offset(offset)
        .limit(items_per_page)
        .all()
    )

    return {
        "totalCount": total_count,
        "histories": [
            {
                "id": h.id,
                "user_id": h.user_id,
                "recipe_id": h.recipe_id,
                "search_word": h.search_word,
                "search_time": h.search_time.isoformat() if h.search_time else None
            }
            for h in histories
        ]
    }

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
        
    total_count = query.count()   # 추가한 코드!!!

    page_size = 12
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
    return {
        "recipes": result,
        "total_count": total_count
    }