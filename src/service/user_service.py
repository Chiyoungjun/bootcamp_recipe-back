from db import get_db_pool
import aiomysql


class UserService:
    # 전체 회원 조회 (상세정보 포함)
    async def get_users(self):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT u.*, d.height, d.weight, d.preferred_food, d.preferred_tags
                    FROM user u
                    LEFT JOIN user_detail d ON u.id = d.user_id
                """)
                return await cur.fetchall()

    # 특정 회원 조회 (user_id 기준)
    async def get_one_user(self, user_id):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT u.*, d.height, d.weight, d.preferred_food, d.preferred_tags, d.birth_date
                    FROM user u
                    LEFT JOIN user_detail d ON u.id = d.user_id
                    WHERE u.user_id = %s
                """, (user_id,))
                return await cur.fetchone()

    # 로그인 서비스
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
                if user["pw"] != pw:
                    raise Exception("Wrong Password")
                return {
                    "id": user["id"],
                    "user_id": user["user_id"],
                    "ko_name": user["ko_name"],
                    "email": user["email"]
                }

    # 회원가입 서비스
    async def sign_up(self, user_info):
        user_id = user_info.get("user_id")
        pw = user_info.get("pw")
        ko_name = user_info.get("ko_name")
        email = user_info.get("email")
        birth_date = user_info.get("birth_date")
        height = user_info.get("height")
        weight = user_info.get("weight")
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
                    INSERT INTO user(user_id, pw, ko_name, email)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, pw, ko_name, email))
                await conn.commit()

                user_pk = cur.lastrowid

                if height or weight or birth_date or preferred_food or preferred_tags:
                    await cur.execute("""
                        INSERT INTO user_detail(user_id, height, weight, birth_date, preferred_food, preferred_tags)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (user_pk, height, weight, birth_date, preferred_food, preferred_tags))
                    await conn.commit()

                return {
                    "user_id": user_id,
                    "ko_name": ko_name,
                    "email": email,
                    "detail": {
                        "height": height,
                        "weight": weight,
                        "birth_date": birth_date,
                        "preferred_food": preferred_food,
                        "preferred_tags": preferred_tags,
                    }
                }

    # 회원정보 수정 서비스 (PATCH)
    async def update_user(self, user_id, update_info):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # user 테이블 업데이트
                await cur.execute("""
                    UPDATE user 
                    SET ko_name=%s, email=%s
                    WHERE user_id=%s
                """, (
                    update_info.get("ko_name"),
                    update_info.get("email"),
                    user_id,
                ))

                # user_detail 테이블 업데이트
                await cur.execute("""
                    UPDATE user_detail 
                    SET height=%s, weight=%s, birth_date=%s, preferred_food=%s, preferred_tags=%s
                    WHERE user_id=(SELECT id FROM user WHERE user_id=%s)
                """, (
                    update_info.get("height"),
                    update_info.get("weight"),
                    update_info.get("birth_date"),
                    update_info.get("preferred_food"),
                    update_info.get("preferred_tags"),
                    user_id,
                ))

                await conn.commit()
                return {"msg": "회원 정보 수정 완료"}
