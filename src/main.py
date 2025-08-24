from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from recipe.router import router as recipe_router
from user.router import router as user_router
from ai.router import router as ai_router
from maps.router import router as maps_router  # ★카카오맵 추가
from fastapi.staticfiles import StaticFiles

from ai.ai_model import model  # 위에서 만든 모듈에서 모델 임포트

from recipe.router import router as chatbot_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastAPI 의존성으로 모델 객체 제공
def get_model():
    return model

# 라우터 등록
app.include_router(recipe_router, prefix="/api")
app.include_router(user_router, prefix="/api/users")
app.include_router(ai_router, prefix="/api")
app.include_router(maps_router)  # ★카카오맵 검색 api 등록!
app.include_router(chatbot_router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# for route in app.routes:
#     try:
#         print(route.path, route.methods)
#     except Exception as e:
#         print(route.path, "NO METHODS", e)
