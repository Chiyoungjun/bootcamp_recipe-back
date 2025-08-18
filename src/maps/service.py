import os
from dotenv import load_dotenv
load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_REST_KEY")

import requests
def search_places_by_keyword(keyword, x=None, y=None, radius=2000):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": keyword, "size": 10}
    if x and y:
        params["x"] = str(x)
        params["y"] = str(y)
        params["radius"] = radius
    resp = requests.get(url, headers=headers, params=params)
    print("[DEBUG] status_code:", resp.status_code)
    print("[DEBUG] response.text:", resp.text)  # ★ 에러 상세 메시지 여기 찍힘
    resp.raise_for_status()
    return resp.json()

# import os
# import requests
# from dotenv import load_dotenv

# # .env 파일에서 환경변수 로드 (최상위 루트에 .env가 있으면 기본값이면 자동으로 찾음)
# load_dotenv()

# KAKAO_API_KEY = os.getenv("KAKAO_REST_KEY")
# print(KAKAO_API_KEY)

# def search_places_by_keyword(keyword, x=None, y=None, radius=2000):
#     """
#     카카오 장소(음식점 등) 키워드 검색 API 호출
#     Args:
#         keyword (str): 검색어(예: '닭고기볶음밥', '치킨', ...)
#         x (float|str): 경도(옵션, 현 위치 기반시)
#         y (float|str): 위도(옵션)
#         radius (int): 반경(m), 기본 2km
#     Returns:
#         dict: 카카오 API response (가게 리스트, 메타)
#     """
#     url = "https://dapi.kakao.com/v2/local/search/keyword.json"
#     headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
#     params = {"query": keyword, "size": 10}
#     if x and y:
#         params["x"] = str(x)
#         params["y"] = str(y)
#         params["radius"] = radius
#     resp = requests.get(url, headers=headers, params=params)
#     resp.raise_for_status()
#     return resp.json()
