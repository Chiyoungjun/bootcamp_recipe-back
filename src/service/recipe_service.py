from fastapi import APIRouter, Query
import requests
import urllib.parse

router = APIRouter()

API_KEY = "daca2ae71503468ab75a"  # 본인 유효키로 교체하세요

def get_recipe(food_name: str):
    encoded_food_name = urllib.parse.quote(food_name)
    url = (
        f"https://openapi.foodsafetykorea.go.kr/api/"
        f"{API_KEY}/COOKRCP01/json/1/20/RCP_NM={encoded_food_name}"
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
    url = (
        f"https://openapi.foodsafetykorea.go.kr/api/"
        f"{API_KEY}/COOKRCP01/json/1/1/RCP_SEQ={id}"
    )
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rows = data.get("COOKRCP01", {}).get("row", [])
            return rows[0] if rows else None
        else:
            return None
    except Exception as e:
        print(f"API 호출 오류: {e}")
        return None
