import requests
import urllib.parse

API_KEY = "daca2ae71503468ab75a"  # 본인 키로 교체하세요

def get_recipe(food_name: str):
    encoded_food_name = urllib.parse.quote(food_name)
    url = f"https://openapi.foodsafetykorea.go.kr/api/{API_KEY}/COOKRCP01/json/1/20/RCP_NM={encoded_food_name}"
    print(f"[get_recipe] Request URL: {url}")

    try:
        res = requests.get(url, timeout=5)
        print(f"[get_recipe] Status code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            rows = data.get("COOKRCP01", {}).get("row", [])
            print(f"[get_recipe] Retrieved {len(rows)} recipes")
            return rows
        else:
            print(f"[get_recipe] API error status: {res.status_code}")
            return []
    except Exception as e:
        print(f"[get_recipe] Exception: {e}")
        return []

def get_recipe_detail(id: int, food_name: str):
    # 음식명으로 리스트 받아서 id 기준 필터링
    rows = get_recipe(food_name)
    for recipe in rows:
        if str(recipe.get("RCP_SEQ")) == str(id):
            return recipe
    return None
