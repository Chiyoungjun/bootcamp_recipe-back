# src/service/recipe_service.py
from fastapi import APIRouter, Query
import requests
import urllib.parse

router = APIRouter()
API_KEY = "daca2ae71503468ab75a"  # 반드시 본인 발급받은 유효한 키로 교체하세요!

@router.get("/recipe/")
def get_recipe(food_name: str = Query(..., min_length=1, description="검색할 음식명")):
    encoded_food_name = urllib.parse.quote(food_name)
    url = (
        f"https://openapi.foodsafetykorea.go.kr/api/"
        f"{API_KEY}/COOKRCP01/json/1/20/RCP_NM={encoded_food_name}"
    )
    try:
        print(f"[simple_api] 요청 URL: {url}")
        res = requests.get(url, timeout=5)
        print(f"[simple_api] 응답 상태 코드: {res.status_code}")
        print(f"[simple_api] 응답 텍스트 일부:\n{res.text[:500]}")  # 최대 500자 로그

        if res.status_code == 200:
            try:
                data = res.json()
            except Exception as json_err:
                print(f"[simple_api] JSON 파싱 오류: {json_err}")
                return []

            if "COOKRCP01" in data:
                rows = data["COOKRCP01"].get("row", [])
            else:
                rows = []

            print(f"[simple_api] 검색어 '{food_name}' 결과 개수: {len(rows)}")
            return rows
        else:
            print(f"[simple_api] HTTP 에러 응답 코드: {res.status_code}")
            return []
    except Exception as e:
        print(f"[simple_api] 요청 중 예외 발생: {e}")
        return []
