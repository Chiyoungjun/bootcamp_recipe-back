import requests
import urllib.parse
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, date
from fastapi import HTTPException
from collections import Counter
from ai.ai_model import category_model, feature_builder, label_encoder


# recipe/models.py
from .models import (
    Recipe,Rating, RecipeRatingHistories, RecipeViewCountHistories,
    PeriodTypeEnum
)

# user/models.py
from user.models import (
    UserSearchHistory, UserFavorites, UserRecipe
)

# 번역 관련 import
from googletrans import Translator
from typing import List
import asyncio

translator = Translator()

API_KEY = "62f25c3fe3fb40deb80c"  # API 키 꼭 선언해 주세요

def predict_recipe_category(name: str, description: str, way: str = "", category: str = "") -> str:
    import pandas as pd

    df = pd.DataFrame([{
        feature_builder.columns_['name']: name,
        feature_builder.columns_['desc']: description,
        feature_builder.columns_['way']: way,
        feature_builder.columns_['category']: category
    }])

    X, _ = feature_builder.transform(df)
    cluster_num = int(category_model.predict(X)[0])
    predicted_label = label_encoder.inverse_transform([cluster_num])[0]

    return predicted_label




def parse_ingredients(parts_dtl: str) -> list:
    if not parts_dtl:
        return []
    return [x.strip() for x in parts_dtl.split(",") if x.strip()]

async def translate_texts(texts: List[str], dest: str = "en") -> List[str]:
    result = []
    loop = asyncio.get_event_loop()
    for t in texts:
        s = t if t is not None else ""
        try:
            translated = await loop.run_in_executor(None, translator.translate, s, dest)
            result.append(translated.text)
        except Exception as e:
            print(f"번역 중 오류 발생: {e}, 입력값: {s}")
            result.append("")
    return result

def fetch_and_save_all_recipes(db: Session, total=40000, batch_size=500):
    for start in range(1, total + 1, batch_size):
        end = min(start + batch_size - 1, total)
        url = (
            f"https://openapi.foodsafetykorea.go.kr/api/"
            f"{API_KEY}/COOKRCP01/json/{start}/{end}"
        )
        print(f"{start}~{end} 구간 적재 중...")
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                data = res.json()
                rows = data.get("COOKRCP01", {}).get("row", [])
                for row in rows:
                    rid = int(row["RCP_SEQ"])
                    manual_fields = {}
                    for i in range(1, 21):
                        mkey = f"MANUAL{str(i).zfill(2)}"
                        ikey = f"MANUAL_IMG{str(i).zfill(2)}"
                        manual_fields[mkey] = row.get(mkey)
                        manual_fields[ikey] = row.get(ikey)

                    ingredients = parse_ingredients(row.get("RCP_PARTS_DTLS", ""))

                    ml_category = predict_recipe_category(row.get("RCP_NM", ""), row.get("RCP_PARTS_DTLS", ""))

                    recipe = db.query(Recipe).filter_by(id=rid).first()
                    if recipe:
                        recipe.name = row.get("RCP_NM")
                        recipe.description = row.get("RCP_PARTS_DTLS", "")
                        recipe.image_url = row.get("ATT_FILE_NO_MAIN")
                        recipe.category = ml_category
                        recipe.ingredients = ",".join(ingredients) if isinstance(ingredients, list) else ingredients
                        recipe.INFO_ENG = row.get("INFO_ENG")
                        recipe.INFO_CAR = row.get("INFO_CAR")
                        recipe.INFO_PRO = row.get("INFO_PRO")
                        recipe.INFO_FAT = row.get("INFO_FAT")
                        recipe.INFO_NA = row.get("INFO_NA")
                        recipe.RCP_NA_TIP = row.get("RCP_NA_TIP")
                        for key, val in manual_fields.items():
                            setattr(recipe, key, val)
                    else:
                        recipe = Recipe(
                            id=rid,
                            name=row.get("RCP_NM"),
                            image_url=row.get("ATT_FILE_NO_MAIN"),
                            description=row.get("RCP_PARTS_DTLS", ""),
                            category=ml_category,
                            ingredients=",".join(ingredients) if isinstance(ingredients, list) else ingredients,
                            INFO_ENG=row.get("INFO_ENG"),
                            INFO_CAR=row.get("INFO_CAR"),
                            INFO_PRO=row.get("INFO_PRO"),
                            INFO_FAT=row.get("INFO_FAT"),
                            INFO_NA=row.get("INFO_NA"),
                            RCP_NA_TIP=row.get("RCP_NA_TIP"),
                            **manual_fields
                        )
                        db.add(recipe)
                db.commit()
                print(f"  ⮕ {len(rows)}개 row 저장")
            else:
                print(f"  ⮕ API 에러 {res.status_code}")
        except Exception as e:
            print(f"  ⮕ 예외 발생: {e}")

def fetch_external_recipe_by_name(food_name: str):
    encoded = urllib.parse.quote(food_name)
    url = (
        f"https://openapi.foodsafetykorea.go.kr/api/"
        f"{API_KEY}/COOKRCP01/json/1/10/RCP_NM={encoded}"
    )
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rows = data.get("COOKRCP01", {}).get("row", [])
            return rows
    except Exception as e:
        print(f"API 호출 오류: {e}")
    return []

def save_recipe_to_db_from_api(api_row, db: Session):
    rid = int(api_row["RCP_SEQ"])
    recipe = db.query(Recipe).filter_by(id=rid).first()
    if recipe:
        recipe.name = api_row.get("RCP_NM")
        recipe.image_url = api_row.get("ATT_FILE_NO_MAIN")
        recipe.description = api_row.get("RCP_PARTS_DTLS", "")
        db.commit()
        db.refresh(recipe)
        return recipe
    recipe = Recipe(
        id=rid,
        name=api_row.get("RCP_NM"),
        image_url=api_row.get("ATT_FILE_NO_MAIN"),
        description=api_row.get("RCP_PARTS_DTLS", ""),
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe

def get_recipe(q: str, db: Session):
    recipes = db.query(Recipe).filter(Recipe.name.contains(q)).all()
    if recipes:
        return recipes
    api_rows = fetch_external_recipe_by_name(q)
    saved = []
    for row in api_rows:
        saved.append(save_recipe_to_db_from_api(row, db))
    return saved

def get_recipe_detail(recipe_id: int, db: Session):
    return db.query(Recipe).filter_by(id=recipe_id).first()

def get_recipe_list(db: Session):
    return db.query(Recipe).all()

def increase_recipe_view_count(recipe_id: int = None, user_recipe_id: int = None, db: Session = None):
    if not (recipe_id or user_recipe_id):
        raise ValueError("recipe_id 또는 user_recipe_id 중 하나를 반드시 제공해야 합니다.")

    if recipe_id:
        recipe = db.query(Recipe).filter_by(id=recipe_id).first()
        history_filter = {'recipe_id': recipe_id}
    elif user_recipe_id:
        recipe = db.query(UserRecipe).filter_by(id=user_recipe_id).first()
        history_filter = {'user_recipe_id': user_recipe_id}

    if not recipe:
        raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")

    # 조회수 증가
    recipe.view_count = (recipe.view_count or 0) + 1

    today = date.today()
    view_hist = db.query(RecipeViewCountHistories).filter_by(date=today, **history_filter).first()

    if view_hist:
        view_hist.view_count += 1
        view_hist.updated_at = datetime.now()
    else:
        view_hist = RecipeViewCountHistories(
            date=today,
            view_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **history_filter
        )
        db.add(view_hist)

    db.commit()
    db.refresh(recipe)

    return recipe

def get_period_start_dates(nowdt: datetime):
    daily = nowdt.date()
    weekly = (nowdt - timedelta(days=nowdt.weekday())).date()
    monthly = nowdt.replace(day=1).date()
    return daily, weekly, monthly

def add_or_update_rating(user_id, score, recipe_id=None, user_recipe_id=None, db=None):
    if not (recipe_id or user_recipe_id):
        raise ValueError("recipe_id 또는 user_recipe_id 중 하나를 반드시 제공해야 합니다.")

    rating_filter = {'user_id': user_id}
    if recipe_id:
        rating_filter['recipe_id'] = recipe_id
    else:
        rating_filter['user_recipe_id'] = user_recipe_id

    existing_rating = db.query(Rating).filter_by(**rating_filter).first()
    if existing_rating:
        raise ValueError("이미 별점을 등록하셨습니다.")

    now = datetime.now()

    new_rating = Rating(
        rating=score,
        user_id=user_id,
        created_at=now,
        updated_at=now,
    )

    if recipe_id is not None:
        new_rating.recipe_id = recipe_id
        new_rating.user_recipe_id = None
    else:
        new_rating.user_recipe_id = user_recipe_id
        new_rating.recipe_id = None

    # 삽입 직전 상태 출력
    print("Before flush - recipe_id:", new_rating.recipe_id, "user_recipe_id:", new_rating.user_recipe_id)

    db.add(new_rating)
    db.flush()

    daily, weekly, monthly = get_period_start_dates(now)
    for period_type, period_start_date in [('daily', daily), ('weekly', weekly), ('monthly', monthly)]:
        hist_data = {
            "period_type": PeriodTypeEnum(period_type),
            "period_start_date": period_start_date,
            "rating_sum": score,
            "rating_count": 1,
            "created_at": now,
            "updated_at": now
        }
        if recipe_id is not None:
            hist_data["recipe_id"] = recipe_id
        if user_recipe_id is not None:
            hist_data["user_recipe_id"] = user_recipe_id

        # 생성 컬럼 avg_rating은 절대로 포함하지 않음
        # 필드를 직접 명시해서 exclude 하거나 dict를 써서 생성 시 제외

        hist = db.query(RecipeRatingHistories).filter_by(
            recipe_id=recipe_id,
            user_recipe_id=user_recipe_id,
            period_type=PeriodTypeEnum(period_type),
            period_start_date=period_start_date
        ).first()

        if hist:
            hist.rating_sum += score
            hist.rating_count += 1
            hist.updated_at = now
            # 절대 avg_rating 직접 수정하지 말 것
        else:
            hist = RecipeRatingHistories(**hist_data)
            db.add(hist)

    if recipe_id:
        ratings = db.query(Rating).filter_by(recipe_id=recipe_id).all()
        recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    else:
        ratings = db.query(Rating).filter_by(user_recipe_id=user_recipe_id).all()
        recipe = db.query(UserRecipe).filter_by(id=user_recipe_id).first()

    avg = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
    recipe.avg_rating = avg
    recipe.rating_count = len(ratings)

    db.commit()
    db.refresh(recipe)

    return recipe


def save_search_history(user_id: str, search_word: str, recipe_id: int = None, user_recipe_id: int = None, db: Session = None):
    if not (recipe_id or user_recipe_id):
        raise ValueError("recipe_id 또는 user_recipe_id 중 하나를 반드시 제공해야 합니다.")

    try:
        # 중복 체크: user_recipe_id 우선
        if user_recipe_id is not None:
            existing = db.query(UserSearchHistory).filter_by(user_id=user_id, user_recipe_id=user_recipe_id).first()
            if existing:
                return existing

        # recipe_id 중복 체크
        if recipe_id is not None:
            existing = db.query(UserSearchHistory).filter_by(user_id=user_id, recipe_id=recipe_id).first()
            if existing:
                return existing

        history = UserSearchHistory(
            user_id=user_id,
            search_word=search_word,
            recipe_id=recipe_id,
            user_recipe_id=user_recipe_id,
            search_time=datetime.now()
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    except IntegrityError:
        db.rollback()
        # 중복 발생 시 기존 데이터 재조회 후 반환
        existing = None
        if user_recipe_id is not None:
            existing = db.query(UserSearchHistory).filter_by(user_id=user_id, user_recipe_id=user_recipe_id).first()
        if existing is None and recipe_id is not None:
            existing = db.query(UserSearchHistory).filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if existing:
            return existing
        raise 

def add_to_favorites(user_id: str, recipe_id: int = None, user_recipe_id: int = None, db: Session = None):
    if not (recipe_id or user_recipe_id):
        raise ValueError("recipe_id 또는 user_recipe_id 중 하나를 반드시 제공해야 합니다.")

    query = db.query(UserFavorites).filter(UserFavorites.user_id == user_id)

    if recipe_id is not None:
        query = query.filter(UserFavorites.recipe_id == recipe_id)
    elif user_recipe_id is not None:
        query = query.filter(UserFavorites.user_recipe_id == user_recipe_id)

    fav = query.first()
    if fav:
        raise ValueError("이미 찜한 레시피입니다.")

    new_fav = UserFavorites(
        user_id=user_id,
        recipe_id=recipe_id if recipe_id and user_recipe_id is None else None,
        user_recipe_id=user_recipe_id if user_recipe_id else None,
        created_at=datetime.now()
    )
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return new_fav



def remove_from_favorites(user_id: str, recipe_id: int = None, user_recipe_id: int = None, db: Session = None):
    fav = db.query(UserFavorites).filter_by(
        user_id=user_id,
        recipe_id=recipe_id,
        user_recipe_id=user_recipe_id
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
        return True
    else:
        raise ValueError("찜 목록에 없습니다.")

def get_user_favorites(user_id: str, db: Session = None):
    favs = db.query(UserFavorites).filter_by(user_id=user_id).all()
    result = []
    for fav in favs:
        recipe = None
        if fav.recipe_id:
            recipe = db.query(Recipe).filter_by(id=fav.recipe_id).first()
        elif fav.user_recipe_id:
            recipe = db.query(UserRecipe).filter_by(id=fav.user_recipe_id).first()
        if recipe:
            result.append(recipe)
    return result

