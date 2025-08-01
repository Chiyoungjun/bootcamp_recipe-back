import requests
import urllib.parse
from sqlalchemy.orm import Session
from models import Recipe, Rating

API_KEY = "62f25c3fe3fb40deb80c"  # 본인 키로 교체하세요

def categorize_recipe(name: str) -> str:
    if "찌개" in name:
        return "찌개"
    elif "볶음" in name:
        return "볶음"
    elif "탕" in name:
        return "탕"
    elif "조림" in name:
        return "조림"
    else:
        return "기타"

def parse_ingredients(parts_dtl: str) -> list:
    if not parts_dtl:
        return []
    return [x.strip() for x in parts_dtl.split(",") if x.strip()]

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

                    # 영양 정보 등
                    info_eng = row.get("INFO_ENG")
                    info_car = row.get("INFO_CAR")
                    info_pro = row.get("INFO_PRO")
                    info_fat = row.get("INFO_FAT")
                    info_na  = row.get("INFO_NA")
                    rcp_na_tip = row.get("RCP_NA_TIP")
                    category = categorize_recipe(row.get("RCP_NM", ""))
                    ingredients = parse_ingredients(row.get("RCP_PARTS_DTLS", ""))

                    # 이미 있는 row → update, 새로운 row → insert
                    recipe = db.query(Recipe).filter_by(id=rid).first()
                    if recipe:
                        # update 모든 신규 컬럼 포함!
                        recipe.name        = row.get("RCP_NM")
                        recipe.description = row.get("RCP_PARTS_DTLS", "")
                        recipe.image_url   = row.get("ATT_FILE_NO_MAIN")
                        recipe.category    = category
                        recipe.ingredients = ",".join(ingredients) if isinstance(ingredients, list) else ingredients
                        recipe.INFO_ENG    = info_eng
                        recipe.INFO_CAR    = info_car
                        recipe.INFO_PRO    = info_pro
                        recipe.INFO_FAT    = info_fat
                        recipe.INFO_NA     = info_na
                        recipe.RCP_NA_TIP  = rcp_na_tip
                        for key, val in manual_fields.items():
                            setattr(recipe, key, val)
                    else:
                        # insert
                        recipe = Recipe(
                            id=rid,
                            name=row.get("RCP_NM"),
                            image_url=row.get("ATT_FILE_NO_MAIN"),
                            description=row.get("RCP_PARTS_DTLS", ""),
                            category=category,
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

# === 기존 함수명 100% 유지 ===

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
            for row in rows:
                row["CATEGORY"] = categorize_recipe(row.get("RCP_NM", ""))
                row["INGREDIENTS"] = parse_ingredients(row.get("RCP_PARTS_DTLS", ""))
            return rows
    except Exception as e:
        print(f"API 호출 오류: {e}")
    return []

def save_recipe_to_db_from_api(api_row, db: Session):
    rid = int(api_row["RCP_SEQ"])
    recipe = db.query(Recipe).filter_by(id=rid).first()
    if recipe:
        # update 기존 row에 menu/manual 필드 등 값 덮음
        recipe.name        = api_row.get("RCP_NM")
        recipe.image_url   = api_row.get("ATT_FILE_NO_MAIN")
        recipe.description = api_row.get("RCP_PARTS_DTLS", "")
        # 기타 신규필드 UPDATE 로직 넣을 수 있음
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
        db.commit()
        db.refresh(recipe)
    return recipe

def add_or_update_rating(recipe_id: int, user_id: int, score: int, db: Session):
    rating = db.query(Rating).filter_by(recipe_id=recipe_id, user_id=user_id).first()
    if rating:
        rating.rating = score
    else:
        rating = Rating(recipe_id=recipe_id, user_id=user_id, rating=score)
        db.add(rating)
    db.commit()
    ratings = db.query(Rating).filter_by(recipe_id=recipe_id).all()
    avg = sum([r.rating for r in ratings]) / len(ratings) if ratings else 0
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    recipe.avg_rating = avg
    recipe.rating_count = len(ratings)
    db.commit()
    db.refresh(recipe)
    return recipe




# import requests

# API_KEY = "62f25c3fe3fb40deb80c"  # 본인 키로 교체필요

# def categorize_recipe(name: str) -> str:
#     if "찌개" in name:
#         return "찌개"
#     elif "볶음" in name:
#         return "볶음"
#     elif "탕" in name:
#         return "탕"
#     elif "조림" in name:
#         return "조림"
#     else:
#         return "기타"

# def parse_ingredients(parts_dtl: str) -> list:
#     if not parts_dtl:
#         return []
#     return [x.strip() for x in parts_dtl.split(",") if x.strip()]

# def get_recipe(food_name: str):
#     import urllib.parse
#     encoded_food_name = urllib.parse.quote(food_name)
#     url = (
#         f"https://openapi.foodsafetykorea.go.kr/api/"
#         f"{API_KEY}/COOKRCP01/json/1/100/RCP_NM={encoded_food_name}"
#     )
#     try:
#         res = requests.get(url, timeout=5)
#         if res.status_code == 200:
#             data = res.json()
#             rows = data.get("COOKRCP01", {}).get("row", [])
#             # 가공 추가 (선택적)
#             for row in rows:
#                 row["CATEGORY"] = categorize_recipe(row.get("RCP_NM", ""))
#                 row["INGREDIENTS"] = parse_ingredients(row.get("RCP_PARTS_DTLS", ""))
#             return rows
#         else:
#             return []
#     except Exception as e:
#         print(f"API 호출 오류: {e}")
#         return []

# def get_recipe_detail(id: int):
#     url = (
#         f"https://openapi.foodsafetykorea.go.kr/api/"
#         f"{API_KEY}/COOKRCP01/json/1/1000"
#     )
#     try:
#         res = requests.get(url, timeout=5)
#         if res.status_code == 200:
#             data = res.json()
#             rows = data.get("COOKRCP01", {}).get("row", [])
#             for row in rows:
#                 if str(row.get("RCP_SEQ")) == str(id):
#                     row["CATEGORY"] = categorize_recipe(row.get("RCP_NM", ""))
#                     row["INGREDIENTS"] = parse_ingredients(row.get("RCP_PARTS_DTLS", ""))
#                     return row
#             return None
#         else:
#             return None
#     except Exception as e:
#         print(f"API 호출 오류: {e}")
#         return None

# def get_recipe_list():
#     url = (
#         f"https://openapi.foodsafetykorea.go.kr/api/"
#         f"{API_KEY}/COOKRCP01/json/1/1000"
#     )
#     try:
#         res = requests.get(url, timeout=5)
#         if res.status_code == 200:
#             data = res.json()
#             rows = data.get("COOKRCP01", {}).get("row", [])
#             # 각 레시피에 CATEGORY, INGREDIENTS 필드 추가 가공
#             for row in rows:
#                 row["CATEGORY"] = categorize_recipe(row.get("RCP_NM", ""))
#                 row["INGREDIENTS"] = parse_ingredients(row.get("RCP_PARTS_DTLS", ""))
#             return rows
#         else:
#             return []
#     except Exception as e:
#         print(f"API 호출 오류: {e}")
#         return []
