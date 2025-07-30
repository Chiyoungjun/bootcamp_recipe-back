from fastapi import APIRouter, Query
import requests
import urllib.parse

router = APIRouter()

API_KEY = "62f25c3fe3fb40deb80c"  # 본인 유효키로 교체하세요

def get_recipe(food_name: str):
    encoded_food_name = urllib.parse.quote(food_name)
    url = (
        f"https://openapi.foodsafetykorea.go.kr/api/"
        f"{API_KEY}/COOKRCP01/json/1/100/RCP_NM={encoded_food_name}"
    )
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rows = data.get("COOKRCP01", {}).get("row", [])
            return rows
        else:
            return []
    except Exception as e:
        print(f"API 호출 오류: {e}")
        return []

def get_recipe_detail(id: int):
    # 1~1000건 전체 받아오기
    url = (
        f"https://openapi.foodsafetykorea.go.kr/api/"
        f"{API_KEY}/COOKRCP01/json/1/1000"
    )
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rows = data.get("COOKRCP01", {}).get("row", [])
            # 여기서 id와 같은 row만 반환
            for row in rows:
                if str(row.get("RCP_SEQ")) == str(id):
                    return row
            return None
        else:
            return None
    except Exception as e:
        print(f"API 호출 오류: {e}")
        return None
    
# ===========================
# ★ 전체 레시피 리스트 반환 함수 추가
# 프론트엔드가 유사 레시피 필터링에 사용
# ===========================
def get_recipe_list():
    url = (
        f"https://openapi.foodsafetykorea.go.kr/api/"
        f"{API_KEY}/COOKRCP01/json/1/1000"
    )
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rows = data.get("COOKRCP01", {}).get("row", [])
            return rows
        else:
            return []
    except Exception as e:
        print(f"API 호출 오류: {e}")
        return []