import os
import uuid
import shutil
from typing import List, Optional
from fastapi import UploadFile
from db import get_db_pool
import aiomysql
from .schemas import UserRecipeOut


class UserService:
    async def get_users(self):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT u.user_id, u.ko_name, u.email, 
                           d.height, d.weight, d.gender, d.preferred_food, d.preferred_tags
                    FROM user u
                    LEFT JOIN user_detail d ON u.user_id = d.user_id
                """)
                return await cur.fetchall()

    async def get_one_user(self, user_id: str):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT u.user_id, u.ko_name, u.email, d.height, d.weight, 
                           d.gender, d.preferred_food, d.preferred_tags, d.birth_date
                    FROM user u
                    LEFT JOIN user_detail d ON u.user_id = d.user_id
                    WHERE u.user_id = %s
                """, (user_id,))
                return await cur.fetchone()

    async def sign_in(self, user_info):
        user_id = user_info.get("user_id")
        pw = user_info.get("pw")
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM user WHERE user_id=%s", (user_id,))
                user = await cur.fetchone()
                if not user:
                    raise Exception("Invalid User ID")
                if user["pw"] != pw:  # TODO: 암호화 처리 필요
                    raise Exception("Wrong Password")
                return {
                    "user_id": user["user_id"],
                    "ko_name": user["ko_name"],
                    "email": user["email"]
                }

    async def sign_up(self, user_info):
        user_id = user_info.get("user_id")
        pw = user_info.get("pw")
        ko_name = user_info.get("ko_name")
        email = user_info.get("email")
        birth_date = user_info.get("birth_date")
        height = user_info.get("height")
        weight = user_info.get("weight")
        gender = user_info.get("gender")
        preferred_food = user_info.get("preferred_food")
        preferred_tags = user_info.get("preferred_tags")

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM user WHERE user_id=%s", (user_id,))
                user = await cur.fetchone()
                if user:
                    raise Exception("User ID already exists")

                await cur.execute("""
                    INSERT INTO user (user_id, pw, ko_name, email)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, pw, ko_name, email))
                await conn.commit()

                if any([height, weight, birth_date, gender, preferred_food, preferred_tags]):
                    await cur.execute("""
                        INSERT INTO user_detail
                        (user_id, height, weight, birth_date, gender, preferred_food, preferred_tags)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, height, weight, birth_date, gender, preferred_food, preferred_tags))
                    await conn.commit()

                return {
                    "user_id": user_id,
                    "ko_name": ko_name,
                    "email": email,
                    "detail": {
                        "height": height,
                        "weight": weight,
                        "birth_date": birth_date,
                        "gender": gender,
                        "preferred_food": preferred_food,
                        "preferred_tags": preferred_tags,
                    }
                }

    async def update_user(self, user_id: str, update_info):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    UPDATE user 
                    SET ko_name=%s, email=%s
                    WHERE user_id=%s
                """, (
                    update_info.get("ko_name"),
                    update_info.get("email"),
                    user_id,
                ))
                await cur.execute("""
                    UPDATE user_detail 
                    SET height=%s, weight=%s, birth_date=%s, gender=%s, preferred_food=%s, preferred_tags=%s
                    WHERE user_id=%s
                """, (
                    update_info.get("height"),
                    update_info.get("weight"),
                    update_info.get("birth_date"),
                    update_info.get("gender"),
                    update_info.get("preferred_food"),
                    update_info.get("preferred_tags"),
                    user_id,
                ))
                await conn.commit()
                return {"msg": "회원 정보 수정 완료"}

    # ----------- UserRecipe CRUD -----------

    async def create_user_recipe(self, user_id: str, recipe_data: dict,
                                 image_file: Optional[UploadFile] = None,
                                 manual_imgs: Optional[List[Optional[UploadFile]]] = None):
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        if image_file:
            filename = f"{uuid.uuid4().hex}_{image_file.filename}"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
            recipe_data["image_url"] = filepath
        else:
            recipe_data["image_url"] = ""

        manual_img_paths = []
        if manual_imgs:
            for file in manual_imgs:
                if file:
                    filename = f"{uuid.uuid4().hex}_{file.filename}"
                    filepath = os.path.join(upload_dir, filename)
                    with open(filepath, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    manual_img_paths.append(filepath)
                else:
                    manual_img_paths.append("")
        else:
            manual_img_paths = [""] * 20

        if len(manual_img_paths) < 20:
            manual_img_paths += [""] * (20 - len(manual_img_paths))
        else:
            manual_img_paths = manual_img_paths[:20]

        for i in range(20):
            key = f"MANUAL_IMG{str(i+1).zfill(2)}"
            recipe_data[key] = manual_img_paths[i]

        def safe_get(data, key):
            val = data.get(key)
            return val if val is not None else ""

        manual_texts = [recipe_data.get(f"MANUAL{str(i).zfill(2)}", "") or "" for i in range(1, 21)]

        form_data = {
            "name": safe_get(recipe_data, "name"),
            "description": safe_get(recipe_data, "description"),
            "category": safe_get(recipe_data, "category"),
            "ingredients": safe_get(recipe_data, "ingredients"),
            "INFO_ENG": safe_get(recipe_data, "INFO_ENG"),
            "INFO_CAR": safe_get(recipe_data, "INFO_CAR"),
            "INFO_PRO": safe_get(recipe_data, "INFO_PRO"),
            "INFO_FAT": safe_get(recipe_data, "INFO_FAT"),
            "INFO_NA": safe_get(recipe_data, "INFO_NA"),
            "RCP_NA_TIP": safe_get(recipe_data, "RCP_NA_TIP"),
            "image_url": safe_get(recipe_data, "image_url"),
            # is_public 필드 제거하여 포함 안함
        }
        

        for i, text in enumerate(manual_texts, start=1):
            form_data[f"MANUAL{str(i).zfill(2)}"] = text

        for i in range(1, 21):
            form_data[f"MANUAL_IMG{str(i).zfill(2)}"] = safe_get(recipe_data, f"MANUAL_IMG{str(i).zfill(2)}")

        query = """
            INSERT INTO user_recipes
            (user_id, name, description, image_url, view_count, avg_rating, rating_count, created_at, updated_at,
             MANUAL01, MANUAL02, MANUAL03, MANUAL04, MANUAL05, MANUAL06, MANUAL07, MANUAL08, MANUAL09, MANUAL10,
             MANUAL11, MANUAL12, MANUAL13, MANUAL14, MANUAL15, MANUAL16, MANUAL17, MANUAL18, MANUAL19, MANUAL20,
             MANUAL_IMG01, MANUAL_IMG02, MANUAL_IMG03, MANUAL_IMG04, MANUAL_IMG05, MANUAL_IMG06, MANUAL_IMG07, MANUAL_IMG08,
             MANUAL_IMG09, MANUAL_IMG10, MANUAL_IMG11, MANUAL_IMG12, MANUAL_IMG13, MANUAL_IMG14, MANUAL_IMG15, MANUAL_IMG16,
             MANUAL_IMG17, MANUAL_IMG18, MANUAL_IMG19, MANUAL_IMG20,
             category, ingredients, INFO_ENG, INFO_CAR, INFO_PRO, INFO_FAT, INFO_NA, RCP_NA_TIP)
            VALUES (%s, %s, %s, %s, 0, 0.00, 0, NOW(), NOW(),
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s)
        """

        args = (
            user_id,
            form_data["name"],
            form_data["description"],
            form_data["image_url"],
            form_data["MANUAL01"], form_data["MANUAL02"], form_data["MANUAL03"], form_data["MANUAL04"], form_data["MANUAL05"],
            form_data["MANUAL06"], form_data["MANUAL07"], form_data["MANUAL08"], form_data["MANUAL09"], form_data["MANUAL10"],
            form_data["MANUAL11"], form_data["MANUAL12"], form_data["MANUAL13"], form_data["MANUAL14"], form_data["MANUAL15"],
            form_data["MANUAL16"], form_data["MANUAL17"], form_data["MANUAL18"], form_data["MANUAL19"], form_data["MANUAL20"],
            form_data["MANUAL_IMG01"], form_data["MANUAL_IMG02"], form_data["MANUAL_IMG03"], form_data["MANUAL_IMG04"],
            form_data["MANUAL_IMG05"], form_data["MANUAL_IMG06"], form_data["MANUAL_IMG07"], form_data["MANUAL_IMG08"],
            form_data["MANUAL_IMG09"], form_data["MANUAL_IMG10"], form_data["MANUAL_IMG11"], form_data["MANUAL_IMG12"],
            form_data["MANUAL_IMG13"], form_data["MANUAL_IMG14"], form_data["MANUAL_IMG15"], form_data["MANUAL_IMG16"],
            form_data["MANUAL_IMG17"], form_data["MANUAL_IMG18"], form_data["MANUAL_IMG19"], form_data["MANUAL_IMG20"],
            form_data["category"],
            form_data["ingredients"],
            form_data["INFO_ENG"],
            form_data["INFO_CAR"],
            form_data["INFO_PRO"],
            form_data["INFO_FAT"],
            form_data["INFO_NA"],
            form_data["RCP_NA_TIP"],
        )

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                await conn.commit()
                await cur.execute("SELECT LAST_INSERT_ID()")
                last_id = await cur.fetchone()
            
                return last_id[0]

    async def get_user_recipes(self, user_id: str):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM user_recipes WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
                return await cur.fetchall()

    async def get_user_recipe(self, user_id: str, recipe_id: int):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM user_recipes WHERE user_id=%s AND id=%s", (user_id, recipe_id))
                return await cur.fetchone()

    async def update_user_recipe(self, user_id: str, recipe_id: int, update_data: dict):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                valid_keys = {
                    'name', 'description', 'image_url',
                    'MANUAL01', 'MANUAL02', 'MANUAL03', 'MANUAL04', 'MANUAL05',
                    'MANUAL06', 'MANUAL07', 'MANUAL08', 'MANUAL09', 'MANUAL10',
                    'MANUAL11', 'MANUAL12', 'MANUAL13', 'MANUAL14', 'MANUAL15',
                    'MANUAL16', 'MANUAL17', 'MANUAL18', 'MANUAL19', 'MANUAL20',
                    'MANUAL_IMG01', 'MANUAL_IMG02', 'MANUAL_IMG03', 'MANUAL_IMG04', 'MANUAL_IMG05',
                    'MANUAL_IMG06', 'MANUAL_IMG07', 'MANUAL_IMG08', 'MANUAL_IMG09', 'MANUAL_IMG10',
                    'MANUAL_IMG11', 'MANUAL_IMG12', 'MANUAL_IMG13', 'MANUAL_IMG14', 'MANUAL_IMG15',
                    'MANUAL_IMG16', 'MANUAL_IMG17', 'MANUAL_IMG18', 'MANUAL_IMG19', 'MANUAL_IMG20',
                    'category', 'ingredients', 'INFO_ENG', 'INFO_CAR', 'INFO_PRO', 'INFO_FAT', 'INFO_NA', 'RCP_NA_TIP'
                }
                fields = []
                values = []
                for key, value in update_data.items():
                    if key in valid_keys:
                        fields.append(f"{key} = %s")
                        values.append(value)
                if not fields:
                    return
                values.extend([recipe_id, user_id])
                sql = f"UPDATE user_recipes SET {', '.join(fields)} WHERE id = %s AND user_id = %s"
                await cur.execute(sql, tuple(values))
                await conn.commit()

    async def delete_user_recipe(self, user_id: str, recipe_id: int):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM user_recipes WHERE id=%s AND user_id=%s", (recipe_id, user_id))
                await conn.commit()

    # async def search_all_public_recipes(self, query: str) -> List[UserRecipeOut]:
    #     pool = await get_db_pool()
    #     async with pool.acquire() as conn:
    #         async with conn.cursor(aiomysql.DictCursor) as cur:
    #             await cur.execute(
    #                 "SELECT * FROM user_recipes WHERE name LIKE %s ORDER BY created_at DESC",
    #                 (f"%{query}%",)
    #             )
    #             rows = await cur.fetchall()
    #             print(f"[search_all_public_recipes] 쿼리 결과 개수: {len(rows)}")
    #             for r in rows:
    #                 print(r.get("id"), r.get("name"))
    #             return rows


    async def search_user_recipes(self, user_id: str, query: str) -> List[UserRecipeOut]:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM user_recipes WHERE user_id=%s AND name LIKE %s ORDER BY created_at DESC",
                    (user_id, f"%{query}%")
                )
                return await cur.fetchall()

    # async def get_all_user_recipes(self, query: Optional[str] = None):
    #     pool = await get_db_pool()
    #     async with pool.acquire() as conn:
    #         async with conn.cursor(aiomysql.DictCursor) as cur:
    #             if query:
    #                 await cur.execute(
    #                     "SELECT * FROM user_recipes WHERE name LIKE %s ORDER BY created_at DESC",
    #                     (f"%{query}%",)
    #                 )
    #             else:
    #                 await cur.execute(
    #                     "SELECT * FROM user_recipes ORDER BY created_at DESC"
    #                 )
    #             return await cur.fetchall()
