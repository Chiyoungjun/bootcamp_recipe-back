from db import get_db_pool
import aiomysql


class UserService:
    async def get_users(self):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM User")
                return await cur.fetchall()

    async def get_one_user(self, user_id):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM User WHERE user_id=%s", (user_id,))
                return await cur.fetchone()

    async def sign_in(self, user_info):
        id, password = user_info.get("id"), user_info.get("password")
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM User WHERE id=%s", (id,))
                user = await cur.fetchone()
                if not user:
                    raise Exception("Invalid Id")
                if user["password"] != password:
                    raise Exception("Wrong Password")
                return {"id": user["id"], "name": user["name"]}

    async def sign_up(self, user_info):
        id, password, name = user_info.get("id"), user_info.get("password"), user_info.get("name")
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM User WHERE id=%s", (id,))
                user = await cur.fetchone()
                if user:
                    raise Exception("Already has User")
                await cur.execute("INSERT INTO User(id,password,name) VALUES(%s,%s,%s)", (id, password, name))
                await conn.commit()
                return {"id": id, "name": name}
