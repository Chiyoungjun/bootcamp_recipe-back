import requests
import urllib.parse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, date
from collections import Counter
from ai.ai_model import category_model, vectorizer, manual_map


# recipe 폴더 안 models.py
from .models import (
    Recipe, Rating, RecipeRatingHistories, RecipeViewCountHistories,
    PeriodTypeEnum
)

# user 폴더 안 models.py
from user.models import (
    UserSearchHistory, UserFavorites
)

# 번역 기능 추가 import
from googletrans import Translator
from typing import List

from ai.ai_model import category_model  # ML 모델 로드

translator = Translator()

def predict_recipe_category(name: str, description: str) -> str:
    text = (name or "") + " " + (description or "")
    X = vectorizer.transform([text])
    cluster_num = int(category_model.predict(X)[0])

    # 병합 로직
    if cluster_num in [3, 11, 12,13]:
        cluster_num = 2  # 병합된 '한식' 군집 번호

    return manual_map.get(cluster_num, str(cluster_num))


API_KEY = "62f25c3fe3fb40deb80c"

def parse_ingredients(parts_dtl: str) -> list:
    if not parts_dtl:
        return []
    return [x.strip() for x in parts_dtl.split(",") if x.strip()]

def translate_texts(texts: List[str], dest: str = "en") -> List[str]:
    result = []
    for t in texts:
        s = t if t is not None else ""
        try:
            translated = translator.translate(s, dest=dest)
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

                    info_eng = row.get("INFO_ENG")
                    info_car = row.get("INFO_CAR")
                    info_pro = row.get("INFO_PRO")
                    info_fat = row.get("INFO_FAT")
                    info_na = row.get("INFO_NA")
                    rcp_na_tip = row.get("RCP_NA_TIP")
                    ingredients = parse_ingredients(row.get("RCP_PARTS_DTLS", ""))

                    # ML 모델로 카테고리 예측
                    ml_category = predict_recipe_category(row.get("RCP_NM", ""), row.get("RCP_PARTS_DTLS", ""))

                    recipe = db.query(Recipe).filter_by(id=rid).first()
                    if recipe:
                        recipe.name = row.get("RCP_NM")
                        recipe.description = row.get("RCP_PARTS_DTLS", "")
                        recipe.image_url = row.get("ATT_FILE_NO_MAIN")
                        recipe.category = ml_category
                        recipe.ingredients = ",".join(ingredients) if isinstance(ingredients, list) else ingredients
                        recipe.INFO_ENG = info_eng
                        recipe.INFO_CAR = info_car
                        recipe.INFO_PRO = info_pro
                        recipe.INFO_FAT = info_fat
                        recipe.INFO_NA = info_na
                        recipe.RCP_NA_TIP = rcp_na_tip
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
                            INFO_ENG=info_eng,
                            INFO_CAR=info_car,
                            INFO_PRO=info_pro,
                            INFO_FAT=info_fat,
                            INFO_NA=info_na,
                            RCP_NA_TIP=rcp_na_tip,
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

def increase_recipe_view_count(recipe_id: int, db: Session):
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe:
        recipe.view_count = (recipe.view_count or 0) + 1
        today = date.today()
        view_hist = db.query(RecipeViewCountHistories).filter_by(recipe_id=recipe_id, date=today).first()
        if view_hist:
            view_hist.view_count += 1
            view_hist.updated_at = datetime.now()
        else:
            view_hist = RecipeViewCountHistories(
                recipe_id=recipe_id,
                date=today,
                view_count=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
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

def add_or_update_rating(recipe_id: int, user_id: str, score: int, db: Session):
    rating = db.query(Rating).filter_by(recipe_id=recipe_id, user_id=user_id).first()
    if rating:
        raise ValueError("이미 별점을 등록하셨습니다.")
    now = datetime.now()
    new_rating = Rating(recipe_id=recipe_id, user_id=user_id, rating=score, created_at=now, updated_at=now)
    db.add(new_rating)
    db.flush()
    daily, weekly, monthly = get_period_start_dates(now)
    for period_type, period_start_date in [
        ('daily', daily), ('weekly', weekly), ('monthly', monthly)
    ]:
        hist = db.query(RecipeRatingHistories).filter_by(
            recipe_id=recipe_id,
            period_type=PeriodTypeEnum(period_type),
            period_start_date=period_start_date
        ).first()
        if hist:
            hist.rating_sum += score
            hist.rating_count += 1
            hist.updated_at = now
        else:
            hist = RecipeRatingHistories(
                recipe_id=recipe_id,
                period_type=PeriodTypeEnum(period_type),
                period_start_date=period_start_date,
                rating_sum=score,
                rating_count=1,
                created_at=now,
                updated_at=now
            )
            db.add(hist)
    ratings = db.query(Rating).filter_by(recipe_id=recipe_id).all()
    avg = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    recipe.avg_rating = avg
    recipe.rating_count = len(ratings)
    db.commit()
    db.refresh(recipe)
    return recipe

def save_search_history(user_id: str, recipe_id: int, search_word: str, db: Session):
    history = UserSearchHistory(
        user_id=user_id,
        recipe_id=recipe_id,
        search_word=search_word,
        search_time=datetime.now()
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def add_to_favorites(user_id: str, recipe_id: int, db: Session):
    fav = UserFavorites(user_id=user_id, recipe_id=recipe_id)
    db.add(fav)
    try:
        db.commit()
        db.refresh(fav)
        return fav
    except IntegrityError:
        db.rollback()
        raise ValueError("이미 찜한 레시피입니다.")

def remove_from_favorites(user_id: str, recipe_id: int, db: Session):
    fav = db.query(UserFavorites).filter_by(user_id=user_id, recipe_id=recipe_id).first()
    if fav:
        db.delete(fav)
        db.commit()
        return True
    else:
        raise ValueError("찜 목록에 없습니다.")

def get_user_favorites(user_id: str, db: Session):
    favs = db.query(UserFavorites).filter_by(user_id=user_id).all()
    recipes = [db.query(Recipe).filter_by(id=fav.recipe_id).first() for fav in favs]
    return recipes
