from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import (
    Rating, Recipe, RecipeRatingHistories, PeriodTypeEnum,
    UserSearchHistory, UserBmiRecommendation, UserDetail, UserFavorites # ← UserFavorites 추가!
)
from service.recipe_service import (
    get_recipe, get_recipe_detail, get_recipe_list,
    increase_recipe_view_count, add_or_update_rating,
    add_to_favorites, remove_from_favorites, get_user_favorites # ← 찜 서비스 함수들 추가!
)
from sqlalchemy import desc
from datetime import date, timedelta
import shutil
import os
from collections import Counter
from ai.ai_model import model
from typing import List
from datetime import datetime

router = APIRouter()

# BMI 분류 함수
def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상"
    elif bmi < 25:
        return "과체중"
    else:
        return "비만"

# 평점 입력용 Pydantic 모델
class RatingRequest(BaseModel):
    user_id: str
    rating: int

# 즐겨찾기(찜) 관련 Pydantic 모델 추가
class FavoriteRequest(BaseModel):
    user_id: str
    recipe_id: int

# 사용자 검색 이력 저장용 Pydantic 모델
class SearchHistoryRequest(BaseModel):
    user_id: str
    recipe_id: int = None
    search_word: str

# 사용자 검색 이력 응답용 Pydantic 모델
class SearchHistoryResponse(BaseModel):
    id: int
    user_id: str
    search_word: str
    search_time: str
class Config:
    from_attributes = True

# BMI 저장용 Pydantic 모델
class BmiRecommendationRequest(BaseModel):
    user_id: str
    height: float
    weight: float
    recommended_recipes: str = None

# ★★★ 찜(즐겨찾기) 추가 API
@router.post("/favorites")
def favorite_recipe(request: FavoriteRequest, db: Session = Depends(get_db)):
    try:
        fav = add_to_favorites(request.user_id, request.recipe_id, db)
        return {"message": "레시피를 즐겨찾기(찜) 추가했습니다."}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

# ★★★ 찜(즐겨찾기) 해제 API
@router.delete("/favorites")
def unfavorite_recipe(request: FavoriteRequest, db: Session = Depends(get_db)):
    try:
        remove_from_favorites(request.user_id, request.recipe_id, db)
        return {"message": "레시피 즐겨찾기(찜) 해제 성공"}
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

# ★★★ 사용자의 즐겨찾기(찜) 레시피 목록 조회 API
@router.get("/favorites/{user_id}")
def get_favorites(user_id: str, db: Session = Depends(get_db)):
    recipes = get_user_favorites(user_id, db)
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


# 레시피 외부 검색 API
@router.get("/recipes/external/search")
def search_recipes(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    recipes = get_recipe(q, db)
    if not recipes:
        raise HTTPException(404, "레시피가 없습니다.")
    return recipes


# 레시피 상세 정보 API
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
        # ⬇⬇⬇ 조리 방법(매뉴얼)과 이미지 한 번에 모두 추가
        **{f"MANUAL{str(i).zfill(2)}": getattr(recipe, f"MANUAL{str(i).zfill(2)}") for i in range(1, 21)},
        **{f"MANUAL_IMG{str(i).zfill(2)}": getattr(recipe, f"MANUAL_IMG{str(i).zfill(2)}") for i in range(1, 21)},
    }


# 레시피 리스트 조회 API
@router.get("/recipelist")
def recipe_list(db: Session = Depends(get_db)):
    return get_recipe_list(db)


# 레시피 조회수 증가 API
@router.post("/recipes/{recipe_id}/view")
def view_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = increase_recipe_view_count(recipe_id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")
    return {"view_count": recipe.view_count}


# 레시피 별점 입력 API
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


# 랭킹 조회 API
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


# 사용자 BMI 저장 및 추천 API
@router.post("/user/profile/bmi-recommendation")
def save_bmi_recommendation(
    request: BmiRecommendationRequest,
    db: Session = Depends(get_db),
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


# 사용자 선호 기반 추천 API (예시)
@router.get("/recommendations/user-preferences")
def get_user_preference_recommendations(
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db),
):
    recent_searches = (
        db.query(UserSearchHistory.search_word)
        .filter(UserSearchHistory.user_id == user_id)
        .order_by(UserSearchHistory.search_time.desc())
        .limit(5)
        .all()
    )
    keywords = [kw for (kw,) in recent_searches]

    if not keywords:
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


# BMI 기반 추천 API
@router.get("/recommendations/bmi")
def get_bmi_recommendations(
    user_id: str = Query(..., description="사용자 ID"),   # int → str
    db: Session = Depends(get_db),
):
    user_profile = db.query(UserDetail).filter_by(user_id=user_id).first()
    if not user_profile or not user_profile.height or not user_profile.weight:
        raise HTTPException(400, "사용자 신체 정보(키, 몸무게)가 필요합니다.")

    bmi = float(user_profile.weight) / ((float(user_profile.height) / 100) ** 2)
    bmi_class = classify_bmi(bmi)

    if bmi_class == "저체중":
        query = db.query(Recipe).filter(Recipe.category.in_(["밥", "구이, 찜"])).order_by(Recipe.INFO_ENG.desc())
    elif bmi_class == "정상":
        query = db.query(Recipe).order_by(Recipe.view_count.desc())
    elif bmi_class == "과체중":
        query = db.query(Recipe).filter(Recipe.category.in_(["샐러드", "국, 찌개", "반찬"])).order_by(Recipe.INFO_ENG.asc())
    else:
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


# 이미지 업로드 및 YOLO 분석 후 관련 레시피 반환 API
@router.post("/recipes/upload")
async def upload_recipe_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, image.filename)

    # 파일 저장
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"파일 저장 실패: {str(e)}")

    # YOLO 예측
    try:
        results = model(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(500, f"YOLO 추론 실패: {str(e)}")

    # 라벨명 추출
    food_names = []
    names = model.names  # {id: label} dict
    for r in results:
        if hasattr(r, "boxes"):
            for box in r.boxes:
                class_id = int(box.cls[0])
                label = names[class_id]
                food_names.append(label)

    # ▷▷▷ 첫 번째 프린트: 예측된 모든 음식명 리스트
    print(f"[DEBUG] Detected food names from image: {food_names}")

    os.remove(file_path)

    if not food_names:
        raise HTTPException(404, "이미지에서 음식을 인식하지 못했습니다.")

    from collections import Counter
    common_food_name = Counter(food_names).most_common(1)[0][0]

    # ▷▷▷ 접두사_음식명 → 음식명으로 변환
    if "_" in common_food_name:
        _, search_name = common_food_name.split("_", 1)
    else:
        search_name = common_food_name

    # ▷▷▷ 두 번째 프린트: DB 검색에 사용될 대표 음식명
    print(f"[DEBUG] Representative food name used for DB search: {search_name}")

    # 수정된 검색어로 DB 검색
    recipes = get_recipe(search_name, db)
    if not recipes:
        raise HTTPException(404, f"{search_name} 기반 검색 결과가 없습니다.")

    return recipes
