import os
import uuid
import shutil
import json
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from db import get_db_pool
import aiomysql
from .schemas import UserRecipeOut  # 리스트 검색용 타입힌트 유지


class UserService:
    # -----------------------------
    # User 조회/인증
    # -----------------------------
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
                if user["pw"] != pw:  # 실제 서비스에서는 반드시 해시 사용
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
                # 아이디 중복
                await cur.execute("SELECT 1 FROM user WHERE user_id=%s", (user_id,))
                if await cur.fetchone():
                    raise Exception("User ID already exists")

                # user
                await cur.execute("""
                    INSERT INTO user (user_id, pw, ko_name, email)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, pw, ko_name, email))
                await conn.commit()

                # user_detail (옵션)
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
    

    # -----------------------------
    # UserRecipe CRUD
    # -----------------------------
    async def create_user_recipe(
        self,
        user_id: str,
        recipe_data: dict,
        image_file: Optional[UploadFile] = None,
        manual_imgs: Optional[List[Optional[UploadFile]]] = None
    ):
        """
        업로드 파일을 저장하고 user_recipes에 삽입.
        - DB에는 상대 경로('uploads/xxx')가 들어가도록 현재 구현 유지.
        - MANUAL01~20 / MANUAL_IMG01~20 / 영양정보 / 팁 / 재료(문자열) 저장.
        - steps / step_images(리스트 또는 JSON 문자열)도 받아 자동으로 팬아웃 저장.
        """
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # 메인 이미지 저장
        if image_file:
            filename = f"{uuid.uuid4().hex}_{image_file.filename}"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
            recipe_data["image_url"] = filepath
        else:
            recipe_data["image_url"] = ""

        # ---------- 입력 정규화 유틸 ----------
        def _to_list(val) -> Optional[List[Any]]:
            """list 그대로 or JSON 문자열 → list 로 변환. 실패 시 None."""
            if isinstance(val, list):
                return val
            if isinstance(val, str) and val.strip():
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    return None
            return None

        # ---------- 단계 이미지: step_images_json/step_images → 없으면 업로드 파일 ----------
        step_images_raw = recipe_data.get("step_images_json") or recipe_data.get("step_images")
        step_images_list = _to_list(step_images_raw)

        manual_img_paths: List[str] = []
        if step_images_list:
            manual_img_paths = [str(x or "").strip().replace("\\", "/") for x in step_images_list]
        elif manual_imgs:
            for file in manual_imgs:
                if file:
                    filename = f"{uuid.uuid4().hex}_{file.filename}"
                    filepath = os.path.join(upload_dir, filename)
                    with open(filepath, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    manual_img_paths.append(filepath)
                else:
                    manual_img_paths.append("")

        # 길이 보정(정확히 20개)
        if len(manual_img_paths) < 20:
            manual_img_paths += [""] * (20 - len(manual_img_paths))
        else:
            manual_img_paths = manual_img_paths[:20]

        # recipe_data에 반영
        for i in range(20):
            key = f"MANUAL_IMG{str(i+1).zfill(2)}"
            recipe_data[key] = manual_img_paths[i]

        def safe_get(data: Dict[str, Any], key: str) -> str:
            val = data.get(key)
            return val if val is not None else ""

        # ---------- steps: steps_json/steps → MANUAL01~20 팬아웃 ----------
        steps_raw = recipe_data.get("steps_json") or recipe_data.get("steps")
        steps_list = _to_list(steps_raw)

        # 우선 기존 MANUAL 값으로 초기화
        manual_texts = [recipe_data.get(f"MANUAL{str(i).zfill(2)}", "") or "" for i in range(1, 21)]

        # steps 리스트가 있으면 덮어쓰기
        if steps_list:
            for i in range(1, 21):
                manual_texts[i-1] = (str(steps_list[i-1]).strip() if i-1 < len(steps_list) and steps_list[i-1] is not None else manual_texts[i-1])

        # 재료가 배열로 왔다면 문자열로 저장
        ingredients_in = recipe_data.get("ingredients")
        if isinstance(ingredients_in, list):
            recipe_data["ingredients"] = "\n".join([str(x).strip() for x in ingredients_in if str(x).strip()])

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
        }
        # 텍스트/이미지 필드 추가
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

        # 디버깅
        print(f"쿼리 내 플레이스홀더 개수: {query.count('%s')}, 인자 개수: {len(args)}")

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
                await cur.execute(
                    "SELECT * FROM user_recipes WHERE user_id=%s ORDER BY created_at DESC",
                    (user_id,),
                )
                rows = await cur.fetchall()
                # 경로 보정(윈도우 대비)
                for r in rows:
                    if r.get("image_url"):
                        r["image_url"] = r["image_url"].replace("\\", "/")
                return rows

    async def get_user_recipe(self, user_id: str, recipe_id: int):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM user_recipes WHERE user_id=%s AND id=%s",
                    (user_id, recipe_id),
                )
                row = await cur.fetchone()
                if row and row.get("image_url"):
                    row["image_url"] = row["image_url"].replace("\\", "/")
                return row

    async def update_user_recipe(self, user_id: str, recipe_id: int, update_data: dict):
        """
        - steps(List[str] 또는 JSON 문자열) → MANUAL01~20 팬아웃
        - step_images(List[str] 또는 JSON 문자열) → MANUAL_IMG01~20 팬아웃
        - 기존 개별 필드 업데이트도 그대로 지원
        """
        # -------- 입력 정규화 유틸 --------
        def _to_list(val) -> Optional[List[Any]]:
            if isinstance(val, list):
                return val
            if isinstance(val, str) and val.strip():
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    return None
            return None

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 1) 배열 꺼내기 (문자열이면 JSON 파싱)
                steps = _to_list(update_data.pop("steps", None))
                step_images = _to_list(update_data.pop("step_images", None))

                # ingredients가 리스트면 줄바꿈 문자열로 전환
                if isinstance(update_data.get("ingredients"), list):
                    ing_list = [str(x).strip() for x in update_data["ingredients"] if str(x).strip()]
                    update_data["ingredients"] = "\n".join(ing_list)

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

                fields: List[str] = []
                values: List[Any] = []

                # 2) steps → MANUAL01~20
                if isinstance(steps, list):
                    norm_steps = [(s or "").strip() for s in steps]
                    for i in range(1, 21):
                        fields.append(f"MANUAL{i:02d} = %s")
                        values.append(norm_steps[i-1] if i-1 < len(norm_steps) else "")

                # 3) step_images → MANUAL_IMG01~20
                if isinstance(step_images, list):
                    norm_imgs = [(s or "").strip().replace("\\", "/") for s in step_images]
                    for i in range(1, 21):
                        fields.append(f"MANUAL_IMG{i:02d} = %s")
                        values.append(norm_imgs[i-1] if i-1 < len(norm_imgs) else "")

                # 4) 개별 필드
                for key, value in update_data.items():
                    if key in valid_keys:
                        fields.append(f"{key} = %s")
                        values.append(value)

                if not fields:
                    return  # 변경 없음

                # updated_at 갱신
                fields.append("updated_at = NOW()")
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

    async def search_user_recipes(self, user_id: str, query: str) -> List[UserRecipeOut]:
        recipes = await self.get_user_recipes(user_id)
        return [r for r in recipes if (r.get("name") or "").lower().find(query.lower()) >= 0]

    # -----------------------------
    # ✅ 단계 전용 저장 메서드 (전용 엔드포인트용)
    # -----------------------------
    async def set_recipe_steps(
        self,
        user_id: str,
        recipe_id: int,
        steps: List[str],
        step_images: Optional[List[str]] = None,
    ):
        """
        steps → MANUAL01~20
        step_images → MANUAL_IMG01~20
        """
        # 길이 보정
        norm_steps = [(s or "").strip() for s in (steps or [])][:20]
        if len(norm_steps) < 20:
            norm_steps += [""] * (20 - len(norm_steps))

        norm_imgs: List[str] = []
        if isinstance(step_images, list):
            norm_imgs = [(x or "").strip().replace("\\", "/") for x in step_images][:20]
        if len(norm_imgs) < 20:
            norm_imgs += [""] * (20 - len(norm_imgs))

        # UPDATE 쿼리 조립
        fields = []
        values = []
        for i in range(1, 21):
            fields.append(f"MANUAL{i:02d} = %s")
            values.append(norm_steps[i-1])
        for i in range(1, 21):
            fields.append(f"MANUAL_IMG{i:02d} = %s")
            values.append(norm_imgs[i-1])

        fields.append("updated_at = NOW()")
        values.extend([recipe_id, user_id])

        sql = f"UPDATE user_recipes SET {', '.join(fields)} WHERE id = %s AND user_id = %s"

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, tuple(values))
                await conn.commit()

    # ======================================================
    # ✅ 상세: 표준 필드(ingredients/steps/step_images/tip)를 채워 반환
    # ======================================================
    async def get_user_recipe_detail(
        self,
        recipe_id: int,
        user_id: Optional[str],
        lang: str = "ko",
        increment_view: bool = True
    ):
        """
        상세 페이지 전용 데이터 조립.
        - API 응답에 표준 필드 포함:
            ingredients: List[str]
            steps:       List[str]
            step_images: List[str]
            tip:         str
          + 호환용 필드(RCP_PARTS_DTLS, MANUALxx, MANUAL_IMGxx)도 같이 반환.
        - 별점/조회수는 user_recipes와 RecipeRankLog를 활용(있으면).
        """
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 1) 본문
                await cur.execute("SELECT * FROM user_recipes WHERE id=%s", (recipe_id,))
                base = await cur.fetchone()
                if not base:
                    return None

                # 2) 조회수 +1
                if increment_view:
                    await cur.execute(
                        "UPDATE user_recipes SET view_count = COALESCE(view_count,0) + 1 WHERE id=%s",
                        (recipe_id,)
                    )
                    await conn.commit()
                    base["view_count"] = (base.get("view_count") or 0) + 1
                else:
                    base["view_count"] = int(base.get("view_count") or 0)

                # 3) 평점 기본값
                base["avg_rating"] = float(base.get("avg_rating") or 0)
                base["rating_count"] = int(base.get("rating_count") or 0)
                user_rating_val = 0

                # 4) RecipeRankLog 보강(있으면)
                try:
                    await cur.execute("SHOW TABLES LIKE 'RecipeRankLog'")
                    has_log = await cur.fetchone() is not None
                    if has_log:
                        await cur.execute(
                            """
                            SELECT
                                COALESCE(AVG(CASE WHEN event='rating' AND rating IS NOT NULL THEN rating END), 0) AS avg_rating,
                                SUM(CASE WHEN event='rating' AND rating IS NOT NULL THEN 1 ELSE 0 END)          AS rating_count,
                                MAX(CASE WHEN event='rating' AND user_id = %s THEN rating ELSE NULL END)        AS user_rating
                            FROM RecipeRankLog
                            WHERE recipe_id = %s
                            """,
                            (user_id, recipe_id)
                        )
                        agg = await cur.fetchone() or {}
                        base["avg_rating"]   = float(agg.get("avg_rating") or base["avg_rating"] or 0)
                        base["rating_count"] = int(agg.get("rating_count") or base["rating_count"] or 0)
                        user_rating_val      = int(agg.get("user_rating") or 0)
                except Exception as e:
                    print("RecipeRankLog 집계 스킵:", e)

                # 5) 경로 보정(윈도우 대비)
                if base.get("image_url"):
                    base["image_url"] = base["image_url"].replace("\\", "/")
                for i in range(1, 21):
                    k = f"MANUAL_IMG{str(i).zfill(2)}"
                    if base.get(k):
                        base[k] = base[k].replace("\\", "/")

                # 6) 표준 필드 조립 --------------------------
                # (a) 재료: TEXT를 구분자 기준으로 리스트화
                ingredients_list: List[str] = []
                raw_ing = (base.get("ingredients") or "").strip()
                if raw_ing:
                    parts = [p.strip() for p in raw_ing.replace("\r", "").split("\n")]
                    tmp: List[str] = []
                    for p in parts:
                        tmp.extend([x.strip() for x in p.split(",")])
                    ingredients_list = [x for x in tmp if x]

                # (b) 만드는 법(steps): MANUAL01~20을 순서대로 수집(빈값 제외)
                steps_list: List[str] = []
                for i in range(1, 21):
                    k = f"MANUAL{str(i).zfill(2)}"
                    v = (base.get(k) or "").strip()
                    if v:
                        steps_list.append(v)

                # (c) 단계 이미지(step_images): MANUAL_IMG01~20을 수집(빈값 제외) 후 steps 길이에 맞춰 자름
                step_images_list: List[str] = []
                for i in range(1, 21):
                    img_k = f"MANUAL_IMG{str(i).zfill(2)}"
                    img_v = str(base.get(img_k) or "").strip().replace("\\", "/")
                    if img_v:
                        step_images_list.append(img_v)
                step_images_list = step_images_list[:len(steps_list)]

                # (d) 팁
                tip_text = (base.get("RCP_NA_TIP") or "").strip()

                # (e) 호환용 문자열(RCP_PARTS_DTLS)
                rcp_parts_dtls = "\n".join(ingredients_list) if ingredients_list else ""

                # 7) 최종 detail 딕셔너리 --------------------
                detail: Dict[str, Any] = {
                    # 기본
                    "id": base["id"],
                    "user_id": base.get("user_id"),
                    "name": base.get("name"),
                    "description": base.get("description"),
                    "image_url": base.get("image_url"),
                    "view_count": base.get("view_count", 0),
                    "avg_rating": base.get("avg_rating", 0.0),
                    "rating_count": base.get("rating_count", 0),
                    "user_rating": user_rating_val,

                    "created_at": base.get("created_at"),
                    "updated_at": base.get("updated_at"),

                    # 영양정보(원본 유지)
                    "INFO_ENG": base.get("INFO_ENG"),
                    "INFO_CAR": base.get("INFO_CAR"),
                    "INFO_PRO": base.get("INFO_PRO"),
                    "INFO_FAT": base.get("INFO_FAT"),
                    "INFO_NA": base.get("INFO_NA"),
                }

                # ✅ 표준 필드(프론트가 바로 사용)
                detail["ingredients"] = ingredients_list
                detail["steps"] = steps_list
                detail["step_images"] = step_images_list
                detail["tip"] = tip_text

                # 호환 필드(기존 컴포넌트 대비)
                detail["RCP_PARTS_DTLS"] = rcp_parts_dtls
                detail["RCP_NA_TIP"] = tip_text
                for i in range(1, 21):
                    t_key = f"MANUAL{str(i).zfill(2)}"
                    img_k = f"MANUAL_IMG{str(i).zfill(2)}"
                    detail[t_key] = (base.get(t_key) or "")
                    detail[img_k] = (base.get(img_k) or "")

                return detail
