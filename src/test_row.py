import requests

API_KEY = "62f25c3fe3fb40deb80c"
url = f"https://openapi.foodsafetykorea.go.kr/api/{API_KEY}/COOKRCP01/json/1/1"
r = requests.get(url)
print(r.json()["COOKRCP01"]["row"][0])  # 실제 row dict 확인!