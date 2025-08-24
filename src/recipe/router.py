from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, distinct, desc
from database import get_db

#랭킹 계산식 코드 임포트
from recipe.calculation import get_basic_rankings, get_user_rankings

# recipe 폴더 내 모델
from .models import Rating, Recipe, RecipeRatingHistories, PeriodTypeEnum
from recipe.service import save_search_history

# user 폴더 내 모델
from user.models import UserSearchHistory, UserBmiRecommendation, UserDetail, UserFavorites, UserRecipe

# service 모듈 전체 임포트
from . import service

# 번역기능 추가
from recipe.service import translate_texts  # 번역 함수 import

# schemas
from .schemas import RatingRequest, FavoriteRequest, SearchHistoryRequest, BmiRecommendationRequest

from datetime import date, timedelta, datetime
import shutil
import os
from collections import Counter
from ai.ai_model import model
from typing import List ,Optional

from chatbot.chatbot import ask_chatbot # 정용우 추가
from pydantic import BaseModel # 정용우 추가 # 요청 바디(JSON)**를 자동으로 파이썬 객체로 변환 # 클라이언트가 "레시피 알려줘"> request.message 로 사용
from fastapi.responses import StreamingResponse # 스트리밍 서비스 # 정용우 추가
#from chatbot import model # 정용우 추가 이거 뭔가 안돼서 아래 3줄추가.
import google.generativeai as genai # 정용우

genai.configure(api_key="AIzaSyDnMIpa9qzRUdMvX5FvH4v13JOhWfjzkIs") # 정용우
gemini_model = genai.GenerativeModel("gemini-1.5-flash") # 정용우


router = APIRouter()

# ---------------------------------
# 즐겨찾기
# ---------------------------------
# 찜 추가 API (db 세션 반드시 주입, 서비스 호출 시 db 전달)
from pydantic import BaseModel


@router.post("/favorites")
def add_favorite(request: FavoriteRequest, db: Session = Depends(get_db)):
    # 중복 체크 코드 필수!
    if request.user_recipe_id:
        exists = db.query(UserFavorites).filter_by(
            user_id=request.user_id, user_recipe_id=request.user_recipe_id
        ).first()
        if exists:
            raise HTTPException(400, "이미 찜함")
        fav = UserFavorites(user_id=request.user_id, user_recipe_id=request.user_recipe_id)
    elif request.recipe_id:
        exists = db.query(UserFavorites).filter_by(
            user_id=request.user_id, recipe_id=request.recipe_id
        ).first()
        if exists:
            raise HTTPException(400, "이미 찜함")
        fav = UserFavorites(user_id=request.user_id, recipe_id=request.recipe_id)
    else:
        raise HTTPException(400, "recipe_id 또는 user_recipe_id 둘 중 하나 필수")
    db.add(fav)
    db.commit()
    return {"result": "success"}




# 찜 해제 API
@router.delete("/favorites")
def unfavorite_recipe(request: FavoriteRequest, db: Session = Depends(get_db)):
    try:
        service.remove_from_favorites(
            request.user_id,
            request.recipe_id,
            request.user_recipe_id,  # None이 아니라 실제 값 넘기기
            db
        )
        return {"message": "레시피 즐겨찾기(찜) 해제 성공"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/favorites/{user_id}")
def get_favorites(user_id: str, db: Session = Depends(get_db)):
    favorites_list = db.query(UserFavorites).filter(UserFavorites.user_id == user_id).all()

    result = []
    for fav in favorites_list:
        recipe_obj = fav.user_recipe or fav.recipe  # ORM 관계에 맞게
        
        # 필드를 구분해서 추가
        item = {
            "id": recipe_obj.id,
            "name": recipe_obj.name,
            "image_url": recipe_obj.image_url,
            "avg_rating": getattr(recipe_obj, "avg_rating", 0),
            "rating_count": getattr(recipe_obj, "rating_count", 0),
            "view_count": getattr(recipe_obj, "view_count", 0),
        }

        # 기본 레시피 분기: category 필드 포함
        if hasattr(recipe_obj, "category"):
            item["category"] = recipe_obj.category

        # 사용자 레시피면 user_id와 user_recipe_id(구분용)도 포함
        if fav.user_recipe:
            item["user_id"] = fav.user_id
            item["user_recipe_id"] = recipe_obj.id  # 또는 recipe_obj.user_recipe_id (모델명에 따라 다름)

        result.append(item)

    return {"favorites": result}




# ---------------------------------
# 외부 레시피 검색
# ---------------------------------
@router.get("/recipes/external/search")
def search_recipes(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    recipes = service.get_recipe(q, db)
    if not recipes:
        raise HTTPException(404, "레시피가 없습니다.")
    return recipes

# ---------------------------------
# 레시피 상세보기 (번역기능 추가)
# ---------------------------------
# 백엔드: recipe/router.py (recipedetail API 일부 수정 예시)
@router.get("/recipedetail")
async def recipe_detail(
    id: int = Query(None),
    user_recipe_id: int = Query(None),  # 새로 추가, 기본값 None
    user_id: Optional[str] = Query(None),
    lang: str = Query("ko"),
    increment_view: bool = Query(True),
    db: Session = Depends(get_db)
):
    # 1. 레시피 조회 및 조회수 증가 처리
    if user_recipe_id is not None:
        # 사용자 레시피 처리
        if increment_view:
            recipe = service.increase_recipe_view_count(user_recipe_id=user_recipe_id, db=db)
        else:
            recipe = db.query(UserRecipe).filter_by(id=user_recipe_id).first()
    elif id is not None:
        # 기존 일반 레시피 처리
        if increment_view:
            recipe = service.increase_recipe_view_count(recipe_id=id, db=db)
        else:
            recipe = db.query(Recipe).filter_by(id=id).first()
    else:
        raise HTTPException(status_code=400, detail="id 또는 user_recipe_id 중 하나를 제공해야 합니다.")

    if not recipe:
        raise HTTPException(404, "레시피가 없습니다. 챗봇을 이용해주세요.")

    # 2. 단계 텍스트 및 이미지 추출 
    steps = []
    step_images = []
    for i in range(1, 21):
        text = getattr(recipe, f"MANUAL{str(i).zfill(2)}", None)
        img = getattr(recipe, f"MANUAL_IMG{str(i).zfill(2)}", None)
        if text:
            steps.append(text)
            step_images.append(img)

    # 3. 사용자 평점 조회
    user_rating = 0
    if user_id:
        rating_entry = None
        if user_recipe_id is not None:
            rating_entry = db.query(Rating).filter_by(user_recipe_id=user_recipe_id, user_id=user_id).first()
        else:
            rating_entry = db.query(Rating).filter_by(recipe_id=id, user_id=user_id).first()
        if rating_entry:
            user_rating = rating_entry.rating

    # 4. 한국어인 경우 반환
    if lang.lower() == "ko":
        data = {
            "id": recipe.id,
            "lang": "ko",
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

        for i, step in enumerate(steps):
            step_num = str(i + 1).zfill(2)
            data[f"MANUAL{step_num}"] = step
            data[f"MANUAL_IMG{step_num}"] = step_images[i]
        return data

    # 5. 다국어 번역 처리
    try:
        texts_to_translate = [
            recipe.name,
            recipe.description or "",
            recipe.RCP_NA_TIP or ""
        ] + (recipe.ingredients.split(",") if recipe.ingredients else []) + steps

        translated = await translate_texts(texts_to_translate, dest=lang)
        name = translated[0]
        description = translated[1]
        tip = translated[2]
        ingredients_translated = translated[3:3+len(recipe.ingredients.split(",")) if recipe.ingredients else 0]
        steps_translated = translated[3+len(ingredients_translated):]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"번역 실패: {e}")

    # 6. 최종 응답 구성
    return {
        "id": recipe.id,
        "lang": lang,
        "name": name,
        "description": description,
        "image_url": recipe.image_url,
        "category": recipe.category,
        "ingredients": ingredients_translated,
        "steps": steps_translated,
        "step_images": step_images,
        "INFO_ENG": recipe.INFO_ENG,
        "INFO_CAR": recipe.INFO_CAR,
        "INFO_PRO": recipe.INFO_PRO,
        "INFO_FAT": recipe.INFO_FAT,
        "INFO_NA": recipe.INFO_NA,
        "RCP_NA_TIP": tip,
        "avg_rating": float(recipe.avg_rating or 0),
        "rating_count": recipe.rating_count or 0,
        "view_count": recipe.view_count or 0,
        "user_rating": user_rating,
    }

# ---------------------------------
# 레시피 목록
# ---------------------------------
@router.get("/recipelist")
def recipe_list(db: Session = Depends(get_db)):
    return service.get_recipe_list(db)

# ---------------------------------
# 조회수 증가
# ---------------------------------
@router.post("/recipes/{recipe_id}/view")
def view_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = service.increase_recipe_view_count(recipe_id, db)
    if not recipe:
        raise HTTPException(404, "레시피가 없습니다.")
    return {"view_count": recipe.view_count}

# ---------------------------------
# 별점 등록
# ---------------------------------
@router.post("/recipes/{recipe_id}/rating")
def rate_recipe(recipe_id: int, rating: RatingRequest, db: Session = Depends(get_db)):
    try:
        recipe = service.add_or_update_rating(
            recipe_id=recipe_id,
            user_id=rating.user_id,
            score=rating.rating,
            user_recipe_id=None,
            db=db
        )
        return {
            "avg_rating": float(recipe.avg_rating),
            "rating_count": recipe.rating_count
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------
# 랭킹
# ---------------------------------
@router.get("/rankings")
def get_rankings(period: str = Query(..., regex="^(daily|weekly|monthly)$"), db: Session = Depends(get_db)):
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

    basic_rankings = get_basic_rankings(db, Recipe, RecipeRatingHistories, period_enum, period_start_date)
    user_rankings = get_user_rankings(db, UserRecipe)

    combined = []
    for recipe, score in basic_rankings:
        combined.append({
            "id": recipe.id,
            "name": recipe.name,
            "image_url": recipe.image_url,
            "avg_rating": float(recipe.avg_rating),
            "rating_count": recipe.rating_count,
            "view_count": recipe.view_count,
            "score": float(score),
            "type": "basic",
        })

    for recipe, score in user_rankings:
        combined.append({
            "id": recipe.id,
            "name": recipe.name,
            "image_url": recipe.image_url,
            "avg_rating": float(recipe.avg_rating),
            "rating_count": recipe.rating_count,
            "view_count": recipe.view_count,
            "score": float(score),
            "type": "user",
        })

    # 점수 값 로그 출력
    import logging
    logging.info("--- Combined recipes score list ---")
    for item in combined:
        logging.info(f"id: {item['id']}, type: {item['type']}, score: {item['score']}")

    combined.sort(key=lambda x: x["score"], reverse=True)

    return {"recipes": combined[:10]}


# ---------------------------------
# 사용자 선호 기반 추천
# ---------------------------------
@router.get("/recommendations/user-preferences")
def get_user_preference_recommendations(user_id: str = Query(...), db: Session = Depends(get_db)):
    # 1. 사용자 선호 정보 조회
    user_pref = db.query(UserDetail.preferred_food, UserDetail.preferred_tags).filter(
        UserDetail.user_id == user_id
    ).first()

    if user_pref:
        preferred_food = user_pref.preferred_food or ""
        preferred_tags = user_pref.preferred_tags or ""
    else:
        preferred_food = ""
        preferred_tags = ""

    # 2. 최근 검색어 키워드 조회
    recent_searches = (
        db.query(UserSearchHistory.search_word)
        .filter(UserSearchHistory.user_id == user_id)
        .order_by(UserSearchHistory.search_time.desc())
        .limit(5)
        .all()
    )
    keywords = [kw for (kw,) in recent_searches]

    # 3. 키워드 + 선호음식 + 선호태그 병합
    combined_keywords = set(keywords)
    if preferred_food:
        combined_keywords.update(preferred_food.split(','))  # 쉼표로 구분된 경우
    if preferred_tags:
        combined_keywords.update(preferred_tags.split(','))

    if not combined_keywords:
        return {"recipes": []}

    # 4. 레시피 카테고리 검색에서 combined_keywords를 활용
    # 키워드가 이름에 포함된 레시피 카테고리 가져오기
    categories = [c for (c,) in db.query(distinct(Recipe.category)).filter(
        or_(*[Recipe.name.ilike(f"%{kw.strip()}%") for kw in combined_keywords if kw.strip()])
    ).all()]

    if not categories:
        return {"recipes": []}

    # 5. 추천 레시피 조회 (조회수 순으로 최대 10개)
    recipes = db.query(Recipe).filter(
        Recipe.category.in_(categories)
    ).order_by(Recipe.view_count.desc()).limit(10).all()

    # 6. 10개 미만 시 추가 인기 레시피 보충
    if len(recipes) < 10:
        needed = 10 - len(recipes)
        extra = db.query(Recipe).filter(~Recipe.id.in_([r.id for r in recipes])
        ).order_by(Recipe.view_count.desc()).limit(needed).all()
        recipes.extend(extra)

    # 7. 결과 반환
    return {"recipes": [{
        "id": r.id,
        "name": r.name,
        "image_url": r.image_url,
        "category": r.category,
        "avg_rating": float(r.avg_rating or 0),
        "rating_count": r.rating_count or 0,
        "view_count": r.view_count or 0,
    } for r in recipes]}

# ---------------------------------
# 검색 기록 저장/조회
# ---------------------------------
@router.post("/search-history")
def add_search_history(request: SearchHistoryRequest, db: Session = Depends(get_db)):
    try:
        history = save_search_history(
            user_id=request.user_id,
            search_word=request.search_word,
            recipe_id=request.recipe_id,
            user_recipe_id=request.user_recipe_id,
            db=db
        )
        return {"message": "Search history saved", "data": history}
    except Exception as e:
        # 중복 등 처리된 예외는 save_search_history 내부에서 처리하니 여기서 다시 에러가 난다면 심각한 문제
        return {"message": "Error saving history", "detail": str(e)}

# @router.post("/search-history")
# def add_search_history(request: SearchHistoryRequest, db: Session = Depends(get_db)):
#     history = UserSearchHistory(
#         user_id=request.user_id,
#         recipe_id=request.recipe_id,
#         user_recipe_id=request.user_recipe_id,
#         search_word=request.search_word,
#         search_time=datetime.now()
#     )
#     db.add(history)
#     db.commit()
#     return {"message": "Search history saved"}



@router.get("/search-history/{user_id}")
def get_search_history(user_id: str, page: int = 1, items_per_page: int = 6, db: Session = Depends(get_db)):
    offset = (page - 1) * items_per_page
    total_count = db.query(UserSearchHistory).filter(UserSearchHistory.user_id == user_id).count()
    histories = db.query(UserSearchHistory).filter(
        UserSearchHistory.user_id == user_id
    ).order_by(UserSearchHistory.search_time.desc()).offset(offset).limit(items_per_page).all()

    result = []

    for h in histories:
        recipe_data = {}

        # 기본 레시피 조회
        if h.recipe_id:
            recipe = db.query(Recipe).filter(Recipe.id == h.recipe_id).first()
            if recipe:
                recipe_data = {
                    "id": recipe.id,
                    "name": recipe.name,
                    "image_url": recipe.image_url,
                    "avg_rating": recipe.avg_rating or 0,
                    "rating_count": recipe.rating_count or 0,
                    "view_count": recipe.view_count or 0,
                    "user_id": None,
                }

        # 사용자 레시피 조회
        elif h.user_recipe_id:
            user_recipe = db.query(UserRecipe).filter(UserRecipe.id == h.user_recipe_id).first()
            if user_recipe:
                recipe_data = {
                    "id": user_recipe.id,
                    "name": user_recipe.name,
                    "image_url": user_recipe.image_url,
                    "avg_rating": user_recipe.avg_rating or 0,
                    "rating_count": user_recipe.rating_count or 0,
                    "view_count": user_recipe.view_count or 0,
                    "user_id": user_recipe.user_id,
                }

        result.append({
            "id": h.id,
            "user_id": h.user_id,
            "recipe_id": h.recipe_id,
            "user_recipe_id": h.user_recipe_id,
            "search_word": h.search_word,
            "search_time": h.search_time.isoformat() if h.search_time else None,
            "recipe_info": recipe_data,
        })

    return {
        "totalCount": total_count,
        "histories": result,
    }




# ---------------------------------
# 페이징 레시피 조회 카테고리 라우터
# ---------------------------------
@router.get("/recipes")
def get_recipes(category: str = Query(None), search: str = Query(None), page: int = Query(1), db: Session = Depends(get_db)):
    # 기존 레시피 쿼리
    query = db.query(Recipe)
    
    # 기타 카테고리 처리: "기타"이면 기존 레시피에서 "기타" 또는 사용자 레시피 전체를 합치는 형태로 조회
    if category and category != "전체":
        if category == "기타":
            # 기존 레시피 중 category가 기타인 것 조회
            query = query.filter(Recipe.category == "기타")
        else:
            query = query.filter(Recipe.category == category)
    
    if search:
        query = query.filter(Recipe.name.contains(search))
    
    total_count = query.count()
    page_size = 12
    recipes = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 사용자 레시피는 category 없음 → 기타에 합치려고 별도 쿼리로 조회
    user_recipe_list = []
    if category == "기타":
        # 사용자 레시피 전체 조회 + 검색어 필터(옵션)
        user_query = db.query(UserRecipe)
        if search:
            user_query = user_query.filter(UserRecipe.name.contains(search))
        user_recipe_list = user_query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 기존 레시피 + 사용자 레시피 합치기 (원하는 형태로 변환 필요)
    combined_recipes = []
    for r in recipes:
        combined_recipes.append({
            "id": r.id,
            "name": r.name,
            "image_url": r.image_url,
            "category": r.category,
            "avg_rating": float(r.avg_rating or 0),
            "rating_count": r.rating_count or 0,
            "view_count": r.view_count or 0,
            "is_user_recipe": False,
        })
    for ur in user_recipe_list:
        combined_recipes.append({
            "id": ur.id,
            "name": ur.name,
            "image_url": ur.image_url,
            "category": "기타",  # 임의로 기타 처리
            "avg_rating": float(ur.avg_rating or 0),
            "rating_count": ur.rating_count or 0,
            "view_count": ur.view_count or 0,
            "is_user_recipe": True,
        })
    
    # total_count 도 기존+사용자 레시피 합계로 변경 필요 (페이징 별도 구현 권장)
    combined_total_count = total_count + (user_query.count() if category == "기타" else 0)
    
    return {
        "recipes": combined_recipes,
        "total_count": combined_total_count,
    }


class ChatRequest(BaseModel):
    message: str

# ✅ 완성형: ask_chatbot 사용
@router.post("/chatbot")
def chatbot_answer(request: ChatRequest):
    try:
        answer = ask_chatbot(request.message)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ 스트리밍: text/plain 스트림
@router.post("/chatbot/stream")
def chatbot_stream(request: ChatRequest):
    prompt = (
        f"'{request.message}'에 대해 요리 전문가처럼 자세하고 친절하게 요리 레시피를 단계별로 설명해줘. "
        f"칼로리,지방 같은 영양성분과 재료를 먼저 알려줘. "
        f"그 다음에는 1단계,2단계...단계별로 요리 순서를 알려줘"
    )
    def token_stream():
        try:
            response = gemini_model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[ERROR] {str(e)}"

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")