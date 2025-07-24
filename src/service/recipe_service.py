from db import get_db_pool
import aiomysql
import httpx

# 여기 내가 발급받은 API 키를 직접 입력
API_KEY = "daca2ae71503468ab75a"

class RecipeService:

    async def get_recipes(self):
        """DB에서 레시피 전체 리스트를 조회해 반환"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT recipe_id, title, summary, img_url FROM Recipe")
                recipes = await cur.fetchall()
                return recipes

    async def get_recipe(self, recipe_id: int):
        """특정 레시피 상세 조회"""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM Recipe WHERE recipe_id=%s", (recipe_id,))
                recipe = await cur.fetchone()
                return recipe

    async def get_external_recipes(self, query: str):
        """외부 API 호출: 하드코딩된 API_KEY를 사용"""
        if not API_KEY:
            raise Exception("API 키가 설정되어 있지 않습니다.")

        url = "https://openapi.foodsafetykorea.go.kr/api/"   # 실제 API URL로 바꾸기
        headers = {
            "Authorization": f"Bearer {API_KEY}"          # API 헤더 필요 시 맞게 변경
        }
        params = {
            "query": query,
            "number": 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
